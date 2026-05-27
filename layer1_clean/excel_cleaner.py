# layer1_clean/excel_cleaner.py
# Excel / CSV 來源清洗器
# 繼承 BaseCleaner，實作 load() 和 map_columns()
# 支援 .xlsx / .xls / .csv

import pandas as pd
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from layer1_clean.base_cleaner import BaseCleaner
from config import COLUMN_MAP


class ExcelCleaner(BaseCleaner):
    """
    Excel / CSV 來源清洗器。

    使用方式：
        cleaner = ExcelCleaner(source_file="C:\\bk\\py\\ece_data.xlsx")
        clean_df = cleaner.clean()

    config.py 的 COLUMN_MAP 定義欄位對應關係。
    如果來源有多個 sheet，用 sheet_name 參數指定。
    """

    def __init__(self, source_file: str, sheet_name=0, encoding: str = "utf-8-sig"):
        """
        Args:
            source_file: 來源檔案路徑
            sheet_name:  Excel sheet 名稱或索引（CSV 不需要）
            encoding:    CSV 編碼（Excel 不需要）
        """
        super().__init__(source_file)
        self.sheet_name = sheet_name
        self.encoding = encoding

    # ===== 1. 讀取來源檔案 =====

    def load(self) -> pd.DataFrame:
        """根據副檔名自動選擇讀取方式"""
        ext = os.path.splitext(self.source_file)[1].lower()

        if ext in (".xlsx", ".xls"):
            df = pd.read_excel(
                self.source_file,
                sheet_name=self.sheet_name,
                dtype=str,          # 全部讀成字串，避免數字型電話被轉成 float
            )
        elif ext == ".csv":
            # 先嘗試 utf-8-sig（有 BOM），失敗再試 big5
            try:
                df = pd.read_csv(
                    self.source_file,
                    dtype=str,
                    encoding=self.encoding,
                )
            except UnicodeDecodeError:
                print(f"  [警告] utf-8-sig 讀取失敗，改用 big5 重試")
                df = pd.read_csv(
                    self.source_file,
                    dtype=str,
                    encoding="big5",
                    on_bad_lines="skip",
                )
        else:
            raise ValueError(f"不支援的檔案格式：{ext}，目前支援 .xlsx / .xls / .csv")

        # 欄位名稱去掉首尾空白（有些 Excel 欄位名稱帶空格）
        df.columns = [str(c).strip() for c in df.columns]
        return df

    # ===== 2. 欄位對應 =====

    def map_columns(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        """
        根據 config.COLUMN_MAP 做欄位對應。
        來源欄位名稱 → 主檔欄位名稱。
        來源有但對應表沒有的欄位直接捨棄。
        對應表有但來源沒有的欄位補空字串。
        """
        mapped = {}

        for src_col, master_col in COLUMN_MAP.items():
            if src_col in raw_df.columns:
                # 來源有這個欄位 → 對應到主檔欄位
                mapped[master_col] = raw_df[src_col]
            else:
                # 來源沒有這個欄位 → 補空字串
                print(f"  [提示] 來源缺少欄位「{src_col}」，主檔「{master_col}」將填空白")
                mapped[master_col] = ""

        result_df = pd.DataFrame(mapped)
        return result_df
