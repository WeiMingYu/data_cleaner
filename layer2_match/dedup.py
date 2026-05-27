# layer2_match/dedup.py
# 去重檢查
# 在比對之前先檢查來源資料自身有沒有重複
# 避免同一筆資料被比對兩次導致誤補

import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import MATCH_KEYS


class DedupChecker:
    """
    來源資料去重檢查器。
    在進入 Matcher 之前呼叫，把來源裡重複的資料找出來警告使用者。

    注意：這裡只是「警告」，不自動刪除。
    讓使用者決定要保留哪一筆。
    """

    def __init__(self, source_df: pd.DataFrame):
        self.source_df = source_df

    def check(self) -> dict:
        """
        檢查來源資料的重複情況。
        回傳 { rule_name: duplicate_df }
        """
        results = {}
        for rule in MATCH_KEYS:
            rule_name = "+".join(rule)
            # 檢查這些欄位組合有沒有重複
            available_cols = [c for c in rule if c in self.source_df.columns]
            if not available_cols:
                continue

            # 找出重複的組合
            dup_mask = self.source_df.duplicated(subset=available_cols, keep=False)
            dup_df = self.source_df[dup_mask].copy()

            # 排除空值（空值不算重複）
            for col in available_cols:
                dup_df = dup_df[dup_df[col].str.strip() != ""]

            if len(dup_df) > 0:
                results[rule_name] = dup_df

        return results

    def print_report(self):
        """印出去重報告"""
        results = self.check()
        if not results:
            print("[Layer2-Dedup] 來源資料無重複，OK")
            return

        print("\n[Layer2-Dedup] ⚠ 發現重複資料，請確認：")
        for rule_name, dup_df in results.items():
            print(f"\n  比對欄位「{rule_name}」重複 {len(dup_df)} 筆：")
            print(dup_df[["名稱", "縣市區", "電話"]].head(10).to_string(index=False))
            if len(dup_df) > 10:
                print(f"  ... 還有 {len(dup_df) - 10} 筆")

    def get_deduped_df(self, keep: str = "first") -> pd.DataFrame:
        """
        回傳去重後的 DataFrame。
        Args:
            keep: "first"（保留第一筆）/ "last"（保留最後一筆）
        使用前建議先呼叫 print_report() 確認哪些重複。
        """
        # 用 MATCH_KEYS 第一組規則去重
        if not MATCH_KEYS:
            return self.source_df

        primary_rule = MATCH_KEYS[0]
        available_cols = [c for c in primary_rule if c in self.source_df.columns]
        if not available_cols:
            return self.source_df

        return self.source_df.drop_duplicates(subset=available_cols, keep=keep).reset_index(drop=True)
