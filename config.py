# config.py
# 所有設定集中在此，不散落各模組
# 使用者只需要：
#   1. 把 A檔（來源）放進 input/
#   2. 把 B檔（主檔）放進 master/
#   3. 填入下面的檔名
#   4. 執行 python pipeline.py
#
# 不需要填完整路徑，框架自動組合。

import os

# ===== 1. 專案根目錄（自動取得，不需修改）=====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ===== 2. 固定目錄（自動組合，不需修改）=====
INPUT_DIR  = os.path.join(BASE_DIR, "input")    # A檔放這裡（來源檔）
MASTER_DIR = os.path.join(BASE_DIR, "master")   # B檔放這裡（主檔）
OUTPUT_DIR = os.path.join(BASE_DIR, "output")   # 結果輸出到這裡
TEMP_DIR   = os.path.join(BASE_DIR, "temp")     # 暫存（自動建立）

# ===== 3. 【使用者只改這裡】填入檔名即可 =====

# A檔：來源檔案名稱（放在 input/ 資料夾下）
SOURCE_FILENAME = "ece_data.xlsx"

# B檔：主檔名稱（放在 master/ 資料夾下）
MASTER_FILENAME = "整合_學校類_含MAIL_補齊.xlsx"

# 輸出檔名（自動寫入 output/ 資料夾）
OUTPUT_FILENAME = "整合_學校類_含MAIL_補齊_更新.xlsx"

# ===== 4. 完整路徑（自動組合，不需修改）=====
SOURCE_FILE = os.path.join(INPUT_DIR,  SOURCE_FILENAME)
MASTER_FILE = os.path.join(MASTER_DIR, MASTER_FILENAME)
OUTPUT_FILE = os.path.join(OUTPUT_DIR, OUTPUT_FILENAME)

# ===== 5. 來源欄位對應（SOURCE 欄位名稱 → 主檔欄位名稱）=====
# 說明：左邊是來源檔案的欄位名稱，右邊是主檔的欄位名稱
# 如果來源沒有某個欄位，不需要列在這裡，主檔欄位保持空白
COLUMN_MAP = {
    # 範例（ECE幼兒園資料）：
    "公私立":   "公私立",
    "分類":     "分類",
    "縣市區":   "縣市區",
    "區":       "鄉鎮市區",       # 來源叫「區」，主檔叫「鄉鎮市區」
    "名稱":     "名稱",
    "地址":     "地址",
    "email":    "Mail 電子郵件",  # 來源叫 email，主檔叫「Mail 電子郵件」
    "電話":     "電話",
    "傳真":     "傳真",
    "網址":     "網址",
    "備註":     "備註",
    "資料來源": "資料來源",
}

# ===== 6. 比對邏輯設定（由使用者定義）=====
# 規則格式：list of list
#   外層：多組規則依序嘗試，第一組命中即停止
#   內層：同一組規則中，所有欄位都相同才算符合
MATCH_KEYS = [
    ["電話"],               # 第一優先：電話完全相同
    ["名稱", "縣市區"],     # 第二優先：名稱+縣市區都相同
]

# ===== 7. 補齊邏輯設定 =====
# 主檔已有值 → 不覆蓋；主檔空白 → 從來源補入
FILL_COLUMNS = [
    "Mail 電子郵件",
    "電話",
    "傳真",
    "網址",
    "地址",
    "備註",
]

# 強制覆蓋欄位（不管主檔有沒有值，一律用來源值覆蓋）
# 謹慎使用，通常留空
FORCE_OVERWRITE_COLUMNS = []

# ===== 8. 清洗規則開關 =====
CLEAN_NAME_PREFIX    = True   # 去掉名稱前縣市區前綴
CLEAN_PHONE_FORMAT   = True   # 電話格式化
CLEAN_ADDRESS_PREFIX = True   # 地址去前綴編碼

# ===== 9. 輸出設定 =====
UNMATCHED_SHEET_NAME  = "待人工確認"
NEW_RECORDS_SHEET_NAME = "新增資料"
CONFIRM_BEFORE_WRITE  = True  # 寫入前詢問 y/n 確認
