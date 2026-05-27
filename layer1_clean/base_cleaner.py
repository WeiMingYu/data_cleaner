# layer1_clean/base_cleaner.py
# 清洗基底類別（抽象）
# 所有來源清洗器都繼承這個，實作 load() 和 map_columns()

from abc import ABC, abstractmethod
import pandas as pd
import sys
import os

# 讓子模組可以 import 專案根目錄的模組
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from master_schema import MASTER_COLUMNS, REQUIRED_COLUMNS, empty_record
from config import COLUMN_MAP, CLEAN_NAME_PREFIX, CLEAN_PHONE_FORMAT, CLEAN_ADDRESS_PREFIX
from layer1_clean import clean_rules as rules


class BaseCleaner(ABC):
    """
    清洗基底抽象類別。
    子類別必須實作：
        load()        → 讀取原始檔，回傳 raw DataFrame
        map_columns() → 欄位對應，回傳符合主檔格式的 DataFrame
    """

    def __init__(self, source_file: str):
        self.source_file = source_file
        self._raw_df = None      # 原始資料（讀取後存這裡）
        self._clean_df = None    # 清洗後資料

    # ===== 1. 抽象方法：子類別必須實作 =====

    @abstractmethod
    def load(self) -> pd.DataFrame:
        """讀取來源檔案，回傳原始 DataFrame（不做清洗）"""
        pass

    @abstractmethod
    def map_columns(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        """
        欄位對應：把來源欄位對應到主檔欄位。
        回傳 DataFrame，欄位必須是 MASTER_COLUMNS 的子集。
        """
        pass

    # ===== 2. 通用清洗流程（子類別通常不需要覆寫）=====

    def clean(self) -> pd.DataFrame:
        """
        完整清洗流程：
        1. load() 讀取原始資料
        2. map_columns() 欄位對應
        3. apply_rules() 套用清洗規則
        4. validate() 驗證必填欄位
        5. 補齊缺少的主檔欄位（填空字串）
        回傳符合主檔格式的乾淨 DataFrame
        """
        print(f"[Layer1] 開始清洗：{self.source_file}")

        # --- Step 1: 讀取 ---
        self._raw_df = self.load()
        print(f"  讀取完成：{len(self._raw_df)} 筆")

        # --- Step 2: 欄位對應 ---
        mapped_df = self.map_columns(self._raw_df)
        print(f"  欄位對應完成，欄位：{mapped_df.columns.tolist()}")

        # --- Step 3: 套用清洗規則 ---
        cleaned_df = self._apply_rules(mapped_df)

        # --- Step 4: 補齊缺少的主檔欄位 ---
        for col in MASTER_COLUMNS:
            if col not in cleaned_df.columns:
                cleaned_df[col] = ""

        # 確保欄位順序符合主檔
        cleaned_df = cleaned_df[MASTER_COLUMNS]

        # --- Step 5: 驗證必填欄位 ---
        valid_df, invalid_df = self._validate(cleaned_df)
        if len(invalid_df) > 0:
            print(f"  ⚠ 無效資料（必填欄位為空）：{len(invalid_df)} 筆，已移除")

        print(f"  清洗完成：{len(valid_df)} 筆有效")
        self._clean_df = valid_df
        return valid_df

    def _apply_rules(self, df: pd.DataFrame) -> pd.DataFrame:
        """套用 clean_rules 裡的清洗函數"""
        df = df.copy()

        # 所有欄位先做基本清洗
        for col in df.columns:
            df[col] = df[col].apply(rules.clean_str)

        # 針對特定欄位套用專門規則
        if "名稱" in df.columns and CLEAN_NAME_PREFIX:
            df["名稱"] = df["名稱"].apply(rules.clean_name_prefix)

        if "縣市區" in df.columns:
            df["縣市區"] = df["縣市區"].apply(rules.clean_county)

        if "電話" in df.columns and CLEAN_PHONE_FORMAT:
            df["電話"] = df["電話"].apply(rules.clean_phone)

        if "傳真" in df.columns and CLEAN_PHONE_FORMAT:
            df["傳真"] = df["傳真"].apply(rules.clean_phone)

        if "地址" in df.columns and CLEAN_ADDRESS_PREFIX:
            df["地址"] = df["地址"].apply(rules.clean_address)

        if "Mail 電子郵件" in df.columns:
            df["Mail 電子郵件"] = df["Mail 電子郵件"].apply(rules.clean_email)

        if "網址" in df.columns:
            df["網址"] = df["網址"].apply(rules.clean_url)

        return df

    def _validate(self, df: pd.DataFrame):
        """
        驗證必填欄位。
        回傳 (valid_df, invalid_df)
        """
        mask = df[REQUIRED_COLUMNS].apply(
            lambda col: col.str.strip() != ""
        ).all(axis=1)
        return df[mask].reset_index(drop=True), df[~mask].reset_index(drop=True)

    def get_clean_df(self) -> pd.DataFrame:
        """取得清洗後的 DataFrame（需先呼叫 clean()）"""
        if self._clean_df is None:
            raise RuntimeError("請先呼叫 clean() 方法")
        return self._clean_df
