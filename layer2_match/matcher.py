# layer2_match/matcher.py
# 比對主邏輯
# 把清洗後的來源資料與主檔比對，決定每筆的處理方式
#
# 比對結果分三類：
#   MATCHED   → 找到對應的主檔資料，補齊空白欄位
#   NEW       → 主檔沒有，視為新資料（整筆新增）
#   CONFLICT  → 找到多筆可能符合，無法確定，丟到「待人工確認」

import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import MATCH_KEYS, FILL_COLUMNS, FORCE_OVERWRITE_COLUMNS
from master_schema import MASTER_COLUMNS


class Matcher:
    """
    比對器。
    輸入：清洗後的來源 DataFrame + 主檔 DataFrame
    輸出：
        - updated_master_df  → 補齊後的主檔（已有資料被補）
        - new_df             → 來源有、主檔沒有的新資料
        - unmatched_df       → 比對不到的資料（待人工確認）
        - stats              → 統計摘要 dict
    """

    def __init__(self, master_df: pd.DataFrame, source_df: pd.DataFrame):
        """
        Args:
            master_df: 主檔 DataFrame（已清洗，欄位符合 MASTER_COLUMNS）
            source_df: 來源 DataFrame（已清洗，欄位符合 MASTER_COLUMNS）
        """
        self.master_df = master_df.copy()
        self.source_df = source_df.copy()

        # 統計
        self.stats = {
            "來源總筆數": 0,
            "比對成功（補齊）": 0,
            "新增筆數": 0,
            "待人工確認": 0,
            "比對規則命中分布": {},
        }

    # ===== 1. 主比對流程 =====

    def run(self):
        """
        執行比對，回傳 (updated_master_df, new_df, unmatched_df)
        """
        self.stats["來源總筆數"] = len(self.source_df)

        updated_master = self.master_df.copy()
        new_records = []
        unmatched_records = []

        # 建立主檔索引（加速比對）
        master_indexes = self._build_indexes(updated_master)

        for i, src_row in self.source_df.iterrows():
            result, rule_name, master_idx = self._match_one(src_row, updated_master, master_indexes)

            if result == "MATCHED":
                # 找到了 → 補齊空白欄位
                updated_master = self._fill_row(updated_master, master_idx, src_row)
                self.stats["比對成功（補齊）"] += 1
                self.stats["比對規則命中分布"][rule_name] = \
                    self.stats["比對規則命中分布"].get(rule_name, 0) + 1

            elif result == "NEW":
                # 主檔沒有 → 標記為新增
                new_records.append(src_row.to_dict())
                self.stats["新增筆數"] += 1

            elif result == "UNMATCHED":
                # 比對不到 → 待人工確認
                row_dict = src_row.to_dict()
                row_dict["比對備註"] = "未找到符合的主檔資料"
                unmatched_records.append(row_dict)
                self.stats["待人工確認"] += 1

        # 組合結果
        new_df = pd.DataFrame(new_records, columns=MASTER_COLUMNS) if new_records else pd.DataFrame(columns=MASTER_COLUMNS)
        unmatched_df = pd.DataFrame(unmatched_records) if unmatched_records else pd.DataFrame()

        return updated_master, new_df, unmatched_df

    # ===== 2. 建立比對索引 =====

    def _build_indexes(self, master_df: pd.DataFrame) -> dict:
        """
        根據 MATCH_KEYS 預先建立索引（dict），加速比對。
        格式：{ rule_name: { key_value: [row_idx, ...] } }
        """
        indexes = {}
        for rule in MATCH_KEYS:
            rule_name = "+".join(rule)
            index = {}
            for idx, row in master_df.iterrows():
                # 組合鍵值（多欄位用 | 連接）
                key = self._make_key(row, rule)
                if key == "":
                    continue  # 空值不建索引
                if key not in index:
                    index[key] = []
                index[key].append(idx)
            indexes[rule_name] = index
        return indexes

    def _make_key(self, row, columns: list) -> str:
        """把多個欄位值組合成一個比對鍵"""
        parts = []
        for col in columns:
            v = str(row.get(col, "")).strip()
            if v == "":
                return ""  # 任一欄位為空就不比對
            parts.append(v)
        return "|".join(parts)

    # ===== 3. 單筆比對 =====

    def _match_one(self, src_row, master_df: pd.DataFrame, master_indexes: dict):
        """
        對單筆來源資料執行比對。
        依 MATCH_KEYS 順序嘗試，第一個命中的規則算數。

        回傳：(result, rule_name, master_idx)
            result:     "MATCHED" / "NEW" / "UNMATCHED"
            rule_name:  命中的規則名稱（例 "電話"）
            master_idx: 主檔 DataFrame 的 index（只有 MATCHED 才有值）
        """
        for rule in MATCH_KEYS:
            rule_name = "+".join(rule)
            index = master_indexes.get(rule_name, {})

            # 組合來源這筆的鍵值
            key = self._make_key(src_row, rule)
            if key == "":
                continue  # 來源這個欄位是空的，跳過這條規則

            matched_idxs = index.get(key, [])

            if len(matched_idxs) == 1:
                # 唯一命中 → 成功
                return "MATCHED", rule_name, matched_idxs[0]
            elif len(matched_idxs) > 1:
                # 多筆命中 → 待人工確認（取第一筆補齊，並在 unmatched 標記）
                # 這裡的策略：取第一筆繼續，但把來源資料放到待確認
                return "UNMATCHED", rule_name, None

        # 所有規則都沒找到 → NEW（主檔沒有這筆）
        return "NEW", "", None

    # ===== 4. 補齊欄位 =====

    def _fill_row(self, master_df: pd.DataFrame, master_idx, src_row) -> pd.DataFrame:
        """
        把來源資料補到主檔對應的那一筆。
        規則：
          - FILL_COLUMNS 裡的欄位：主檔有值就不動，空白才補
          - FORCE_OVERWRITE_COLUMNS 裡的欄位：不管有沒有值，直接用來源覆蓋
        """
        for col in FILL_COLUMNS:
            if col not in master_df.columns:
                continue
            src_val = str(src_row.get(col, "")).strip()
            master_val = str(master_df.at[master_idx, col]).strip()

            # 主檔空白才補
            if master_val == "" and src_val != "":
                master_df.at[master_idx, col] = src_val

        # 強制覆蓋欄位
        for col in FORCE_OVERWRITE_COLUMNS:
            if col not in master_df.columns:
                continue
            src_val = str(src_row.get(col, "")).strip()
            if src_val != "":
                master_df.at[master_idx, col] = src_val

        return master_df

    # ===== 5. 印出統計 =====

    def print_stats(self):
        """印出比對統計摘要"""
        print("\n" + "=" * 50)
        print("[Layer2] 比對統計")
        print("=" * 50)
        for k, v in self.stats.items():
            if isinstance(v, dict):
                print(f"  {k}：")
                for rk, rv in v.items():
                    print(f"    {rk}: {rv} 筆")
            else:
                print(f"  {k}：{v}")
        print("=" * 50)
