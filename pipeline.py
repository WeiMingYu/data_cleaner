# pipeline.py
# 一鍵執行主流程：清洗 → 比對 → 匯出
#
# 執行方式：
#   python pipeline.py                         ← 跑完整三層
#   python pipeline.py --layer 1               ← 只跑清洗
#   python pipeline.py --layer 2               ← 只跑比對
#   python pipeline.py --layer 3               ← 只跑匯出
#   python pipeline.py --source 另一個來源.xlsx ← 指定不同 A 檔檔名

import argparse
import os
import sys
import pandas as pd

# ===== 1. 確保可以 import 專案模組 =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from config import (
    SOURCE_FILE, MASTER_FILE, OUTPUT_FILE,
    INPUT_DIR, MASTER_DIR, OUTPUT_DIR, TEMP_DIR,
    SOURCE_FILENAME, MASTER_FILENAME, OUTPUT_FILENAME,
    CONFIRM_BEFORE_WRITE,
)
from master_schema import MASTER_COLUMNS
from layer1_clean.excel_cleaner import ExcelCleaner
from layer2_match.dedup import DedupChecker
from layer2_match.matcher import Matcher
from layer3_export.exporter import Exporter


# ===== 2. 啟動時自動建立所有需要的資料夾 =====
def ensure_dirs():
    """確保 input / master / output / temp 資料夾都存在"""
    for d in [INPUT_DIR, MASTER_DIR, OUTPUT_DIR, TEMP_DIR]:
        os.makedirs(d, exist_ok=True)


# ===== 3. 啟動檢查：A檔 B檔是否存在 =====
def check_files(source_file=None):
    """
    檢查 A檔（input/）和 B檔（master/）是否存在。
    找不到時列出該資料夾現有的檔案，方便使用者確認。
    """
    sf = source_file or SOURCE_FILE
    ok = True

    if not os.path.exists(sf):
        print(f"\n[錯誤] 找不到 A檔（來源）：{sf}")
        print(f"  請把來源檔案放到：{INPUT_DIR}")
        _list_dir(INPUT_DIR)
        ok = False

    if not os.path.exists(MASTER_FILE):
        print(f"\n[錯誤] 找不到 B檔（主檔）：{MASTER_FILE}")
        print(f"  請把主檔放到：{MASTER_DIR}")
        _list_dir(MASTER_DIR)
        ok = False

    return ok


def _list_dir(path):
    """列出資料夾內的檔案"""
    if not os.path.exists(path):
        print(f"  資料夾不存在（已自動建立）")
        return
    files = os.listdir(path)
    if files:
        print(f"  目前資料夾內有：{files}")
    else:
        print(f"  目前資料夾是空的")


# ===== 4. 各層入口函數 =====

def run_layer1(source_file=None) -> pd.DataFrame:
    """第一層：清洗來源資料（A檔）"""
    sf = source_file or SOURCE_FILE
    print("\n" + "=" * 60)
    print("【第一層】清洗來源資料（A檔）")
    print("=" * 60)
    print(f"  A檔路徑：{sf}")

    cleaner = ExcelCleaner(sf)
    clean_df = cleaner.clean()

    # 存暫存檔
    temp_path = os.path.join(TEMP_DIR, "layer1_clean.xlsx")
    clean_df.to_excel(temp_path, index=False)
    print(f"  暫存檔：{temp_path}")
    return clean_df


def run_layer2(clean_df: pd.DataFrame):
    """第二層：比對來源與主檔（B檔）"""
    print("\n" + "=" * 60)
    print("【第二層】比對來源與主檔（B檔）")
    print("=" * 60)
    print(f"  B檔路徑：{MASTER_FILE}")

    master_df = pd.read_excel(MASTER_FILE, dtype=str)
    master_df.columns = [str(c).strip() for c in master_df.columns]
    master_df = master_df.fillna("")
    print(f"  B檔筆數：{len(master_df)}")

    # 去重檢查
    dedup = DedupChecker(clean_df)
    dedup.print_report()

    # 比對
    matcher = Matcher(master_df, clean_df)
    updated_master, new_df, unmatched_df = matcher.run()
    matcher.print_stats()

    # 存暫存
    updated_master.to_excel(os.path.join(TEMP_DIR, "layer2_master.xlsx"), index=False)
    new_df.to_excel(os.path.join(TEMP_DIR, "layer2_new.xlsx"), index=False)
    unmatched_df.to_excel(os.path.join(TEMP_DIR, "layer2_unmatched.xlsx"), index=False)

    return updated_master, new_df, unmatched_df


def run_layer3(updated_master_df, new_df, unmatched_df):
    """第三層：匯出結果到 output/"""
    print("\n" + "=" * 60)
    print("【第三層】匯出結果")
    print("=" * 60)
    print(f"  輸出路徑：{OUTPUT_FILE}")

    exporter = Exporter(updated_master_df, new_df, unmatched_df, OUTPUT_FILE)
    exporter.export()
    exporter.print_summary()


# ===== 5. 主流程 =====

def run_all(source_file=None):
    """一鍵執行三層完整流程"""
    ensure_dirs()

    sf = source_file or SOURCE_FILE

    print("\n" + "=" * 60)
    print("  data_cleaner — 通用資料清洗框架")
    print(f"  A檔（來源）：{sf}")
    print(f"  B檔（主檔）：{MASTER_FILE}")
    print(f"  輸出目錄  ：{OUTPUT_DIR}")
    print("=" * 60)

    # 檢查檔案是否存在
    if not check_files(sf):
        return

    # Layer 1
    clean_df = run_layer1(sf)

    # Layer 2
    updated_master, new_df, unmatched_df = run_layer2(clean_df)

    # 確認才寫入
    if CONFIRM_BEFORE_WRITE:
        print("\n" + "=" * 60)
        print("準備匯出，請確認以上統計資料")
        print(f"  輸出檔案：{OUTPUT_FILE}")
        answer = input("確定要寫入嗎？(y/n) ").strip().lower()
        if answer != "y":
            print("已取消，不寫入。")
            return

    # Layer 3
    run_layer3(updated_master, new_df, unmatched_df)
    print("\n✅ 全部完成！")
    print(f"  請開啟：{OUTPUT_FILE}")


# ===== 6. 命令列參數 =====

def main():
    parser = argparse.ArgumentParser(
        description="data_cleaner 通用資料清洗框架",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
使用說明：
  1. 把 A檔（來源）放到 input/ 資料夾
  2. 把 B檔（主檔）放到 master/ 資料夾
  3. 在 config.py 填入檔名
  4. 執行 python pipeline.py
        """
    )
    parser.add_argument("--layer", type=int, choices=[1, 2, 3], default=None,
                        help="只跑指定層（1=清洗, 2=比對, 3=匯出）")
    parser.add_argument("--source", type=str, default=None,
                        help="指定 A 檔檔名（預設用 config.SOURCE_FILENAME）")
    args = parser.parse_args()

    ensure_dirs()

    # 處理 --source 參數（只填檔名，自動組合 input/ 路徑）
    source_file = None
    if args.source:
        source_file = os.path.join(INPUT_DIR, args.source)

    if args.layer == 1:
        if not check_files(source_file):
            return
        run_layer1(source_file)

    elif args.layer == 2:
        temp_path = os.path.join(TEMP_DIR, "layer1_clean.xlsx")
        if not os.path.exists(temp_path):
            print(f"[錯誤] 找不到暫存檔 {temp_path}，請先跑 --layer 1")
            return
        clean_df = pd.read_excel(temp_path, dtype=str).fillna("")
        run_layer2(clean_df)

    elif args.layer == 3:
        master_temp   = os.path.join(TEMP_DIR, "layer2_master.xlsx")
        new_temp      = os.path.join(TEMP_DIR, "layer2_new.xlsx")
        unmatched_temp = os.path.join(TEMP_DIR, "layer2_unmatched.xlsx")
        if not os.path.exists(new_temp):
            print("[錯誤] 找不到比對暫存檔，請先跑 --layer 2")
            return
        updated = pd.read_excel(master_temp, dtype=str).fillna("") if os.path.exists(master_temp) else pd.DataFrame(columns=MASTER_COLUMNS)
        new_df = pd.read_excel(new_temp, dtype=str).fillna("")
        unmatched = pd.read_excel(unmatched_temp, dtype=str).fillna("") if os.path.exists(unmatched_temp) else pd.DataFrame()
        run_layer3(updated, new_df, unmatched)

    else:
        run_all(source_file)


if __name__ == "__main__":
    main()
