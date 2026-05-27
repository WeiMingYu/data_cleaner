# pipeline.py
# 一鍵執行主流程：清洗 → 比對 → 匯出
# 每個階段有統計輸出，最後一個 y/n 才真正寫入
#
# 執行方式：
#   python pipeline.py
#
# 如果只想跑某一層測試：
#   python pipeline.py --layer 1    ← 只跑清洗，輸出暫存檔
#   python pipeline.py --layer 2    ← 只跑比對（需要先有暫存檔）
#   python pipeline.py --layer 3    ← 只跑匯出（需要先有比對結果）

import argparse
import os
import sys
import pandas as pd

# ===== 1. 確保可以 import 專案模組 =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from config import (
    SOURCE_FILE, MASTER_FILE, OUTPUT_FILE,
    TEMP_DIR, CONFIRM_BEFORE_WRITE,
)
from master_schema import MASTER_COLUMNS
from layer1_clean.excel_cleaner import ExcelCleaner
from layer2_match.dedup import DedupChecker
from layer2_match.matcher import Matcher
from layer3_export.exporter import Exporter


# ===== 2. 各層入口函數 =====

def run_layer1(source_file: str = SOURCE_FILE) -> pd.DataFrame:
    """
    第一層：清洗來源資料。
    回傳清洗後的標準格式 DataFrame。
    同時存一份暫存檔到 TEMP_DIR。
    """
    print("\n" + "=" * 60)
    print("【第一層】清洗來源資料")
    print("=" * 60)
    print(f"  來源檔案：{source_file}")

    cleaner = ExcelCleaner(source_file)
    clean_df = cleaner.clean()

    # 存暫存檔（方便 debug 或只跑某層時用）
    os.makedirs(TEMP_DIR, exist_ok=True)
    temp_path = os.path.join(TEMP_DIR, "layer1_clean.xlsx")
    clean_df.to_excel(temp_path, index=False)
    print(f"  暫存檔：{temp_path}")

    return clean_df


def run_layer2(clean_df: pd.DataFrame, master_file: str = MASTER_FILE):
    """
    第二層：比對來源資料與主檔。
    回傳 (updated_master_df, new_df, unmatched_df)。
    """
    print("\n" + "=" * 60)
    print("【第二層】比對來源與主檔")
    print("=" * 60)
    print(f"  主檔：{master_file}")

    # 讀取主檔
    master_df = pd.read_excel(master_file, dtype=str)
    master_df.columns = [str(c).strip() for c in master_df.columns]
    master_df = master_df.fillna("")
    print(f"  主檔筆數：{len(master_df)}")

    # 去重檢查
    dedup = DedupChecker(clean_df)
    dedup.print_report()

    # 執行比對
    matcher = Matcher(master_df, clean_df)
    updated_master, new_df, unmatched_df = matcher.run()
    matcher.print_stats()

    # 存暫存檔
    os.makedirs(TEMP_DIR, exist_ok=True)
    new_df.to_excel(os.path.join(TEMP_DIR, "layer2_new.xlsx"), index=False)
    unmatched_df.to_excel(os.path.join(TEMP_DIR, "layer2_unmatched.xlsx"), index=False)

    return updated_master, new_df, unmatched_df


def run_layer3(updated_master_df, new_df, unmatched_df, output_file: str = OUTPUT_FILE):
    """
    第三層：匯出結果到 Excel。
    """
    print("\n" + "=" * 60)
    print("【第三層】匯出結果")
    print("=" * 60)

    exporter = Exporter(updated_master_df, new_df, unmatched_df, output_file)
    exporter.export()
    exporter.print_summary()


# ===== 3. 主流程 =====

def run_all():
    """一鍵執行三層完整流程"""

    print("\n" + "=" * 60)
    print("  data_cleaner — 通用資料清洗框架")
    print(f"  來源：{SOURCE_FILE}")
    print(f"  主檔：{MASTER_FILE}")
    print(f"  輸出：{OUTPUT_FILE}")
    print("=" * 60)

    # --- Layer 1：清洗 ---
    clean_df = run_layer1()

    # --- Layer 2：比對 ---
    updated_master, new_df, unmatched_df = run_layer2(clean_df)

    # --- 確認才寫入 ---
    if CONFIRM_BEFORE_WRITE:
        print("\n" + "=" * 60)
        print("準備匯出，請確認以上統計資料")
        print(f"  輸出檔案：{OUTPUT_FILE}")
        answer = input("確定要寫入嗎？(y/n) ").strip().lower()
        if answer != "y":
            print("已取消，不寫入。")
            return

    # --- Layer 3：匯出 ---
    run_layer3(updated_master, new_df, unmatched_df)

    print("\n✅ 全部完成！")


# ===== 4. 命令列參數處理 =====

def main():
    parser = argparse.ArgumentParser(description="data_cleaner 通用資料清洗框架")
    parser.add_argument(
        "--layer",
        type=int,
        choices=[1, 2, 3],
        default=None,
        help="只跑指定的層（1=清洗, 2=比對, 3=匯出），不指定則跑全部",
    )
    parser.add_argument(
        "--source",
        type=str,
        default=SOURCE_FILE,
        help=f"來源檔案路徑（預設：{SOURCE_FILE}）",
    )
    args = parser.parse_args()

    if args.layer == 1:
        # 只跑清洗
        run_layer1(args.source)

    elif args.layer == 2:
        # 只跑比對（從暫存檔讀清洗結果）
        temp_path = os.path.join(TEMP_DIR, "layer1_clean.xlsx")
        if not os.path.exists(temp_path):
            print(f"[錯誤] 找不到暫存檔 {temp_path}，請先跑 --layer 1")
            return
        clean_df = pd.read_excel(temp_path, dtype=str).fillna("")
        run_layer2(clean_df)

    elif args.layer == 3:
        # 只跑匯出（從暫存檔讀比對結果）
        master_temp = os.path.join(TEMP_DIR, "layer2_master.xlsx")
        new_temp = os.path.join(TEMP_DIR, "layer2_new.xlsx")
        unmatched_temp = os.path.join(TEMP_DIR, "layer2_unmatched.xlsx")

        if not os.path.exists(new_temp):
            print(f"[錯誤] 找不到暫存檔，請先跑 --layer 2")
            return

        updated = pd.read_excel(master_temp, dtype=str).fillna("") if os.path.exists(master_temp) else pd.DataFrame(columns=MASTER_COLUMNS)
        new_df = pd.read_excel(new_temp, dtype=str).fillna("")
        unmatched = pd.read_excel(unmatched_temp, dtype=str).fillna("") if os.path.exists(unmatched_temp) else pd.DataFrame()
        run_layer3(updated, new_df, unmatched)

    else:
        # 跑全部
        run_all()


if __name__ == "__main__":
    main()
