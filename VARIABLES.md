# VARIABLES.md
**專案：data_cleaner — 通用資料清洗框架**
**路徑：** `C:\bk\py\data_cleaner\`
**GitHub：** https://github.com/WeiMingYu/data_cleaner
**最後更新：2026-05-27**
**規則：每次修改設定或新增功能，同步更新此文件**

---

## 一、目錄結構

```
data_cleaner/
├── input/                  ← 【A檔放這裡】來源檔（外來資料，要清洗的）
├── master/                 ← 【B檔放這裡】主檔（要被比對補齊的）
├── output/                 ← 【輸出到這裡】比對後的結果 Excel
├── temp/                   ← 暫存檔（自動建立，不需手動管理）
│
├── config.py               ← 所有設定（使用者只改這裡）
├── master_schema.py        ← 主檔欄位定義（唯一真相）
├── pipeline.py             ← 一鍵主流程入口
│
├── layer1_clean/
│   ├── base_cleaner.py     ← 清洗基底（抽象類別）
│   ├── excel_cleaner.py    ← Excel / CSV 清洗器
│   └── clean_rules.py      ← 清洗規則庫（新髒資料加這裡）
│
├── layer2_match/
│   ├── matcher.py          ← 比對主邏輯
│   └── dedup.py            ← 來源自身去重檢查
│
├── layer3_export/
│   └── exporter.py         ← 匯出多 sheet Excel
│
├── VARIABLES.md            ← 本文件
├── SESSION.md              ← 對話狀態記錄
├── README.md               ← GitHub 說明
└── requirements.txt
```

---

## 二、config.py 關鍵設定

| 變數 | 說明 | 範例值 |
|---|---|---|
| SOURCE_FILENAME | A檔檔名（放在 input/） | `ece_data.xlsx` |
| MASTER_FILENAME | B檔檔名（放在 master/） | `整合_學校類_含MAIL_補齊.xlsx` |
| OUTPUT_FILENAME | 輸出檔名（自動寫到 output/） | `整合_學校類_含MAIL_補齊_更新.xlsx` |
| COLUMN_MAP | 來源欄位 → 主檔欄位對應 dict | 每次換來源改這裡 |
| MATCH_KEYS | 比對規則（list of list） | `[["電話"], ["名稱", "縣市區"]]` |
| FILL_COLUMNS | 補齊欄位（主檔空白才補） | 見 config.py |
| FORCE_OVERWRITE_COLUMNS | 強制覆蓋欄位 | 通常留空 `[]` |
| CONFIRM_BEFORE_WRITE | 寫入前詢問確認 | `True` |

> **路徑變數（自動組合，不需修改）：**
> `SOURCE_FILE = INPUT_DIR / SOURCE_FILENAME`
> `MASTER_FILE = MASTER_DIR / MASTER_FILENAME`
> `OUTPUT_FILE = OUTPUT_DIR / OUTPUT_FILENAME`

---

## 三、主檔欄位定義（master_schema.py）

| 欄位名稱 | 說明 | 必填 |
|---|---|---|
| 公私立 | 公立 / 私立 / 空白 | 否 |
| 分類 | 幼兒園 / 國小 / 國中 / 高中 ... | 否 |
| 縣市區 | 臺北市 / 新北市 ... | 否 |
| 鄉鎮市區 | 中正區 / 板橋區 ... | 否 |
| 名稱 | 機構名稱 | **是** |
| 地址 | 完整地址 | 否 |
| Mail 電子郵件 | email | 否 |
| 電話 | 聯絡電話 | 否 |
| 傳真 | 傳真號碼 | 否 |
| 網址 | 官方網站 URL | 否 |
| 備註 | 備用欄位 | 否 |
| 資料來源 | 資料來源說明 | 否 |

---

## 四、比對結果分類

| 分類 | 條件 | 輸出 Sheet |
|---|---|---|
| MATCHED | 主檔找到唯一對應，補齊空白欄位 | 主檔（Sheet 1） |
| NEW | 主檔沒有這筆，視為新資料 | 新增資料（Sheet 2） |
| UNMATCHED | 比對不到或多筆命中 | 待人工確認（Sheet 3） |

---

## 五、暫存檔（temp/）

| 檔案 | 內容 | 由哪層產出 |
|---|---|---|
| layer1_clean.xlsx | 清洗後的 A 檔（標準格式） | Layer 1 |
| layer2_master.xlsx | 比對補齊後的主檔 | Layer 2 |
| layer2_new.xlsx | 新增資料 | Layer 2 |
| layer2_unmatched.xlsx | 待人工確認資料 | Layer 2 |

---

## 六、⚠️ 重要注意事項

- **換來源只改 config.py 的 `SOURCE_FILENAME` 和 `COLUMN_MAP`**，不動程式碼
- **A 檔放 input/，B 檔放 master/**，不需要填完整路徑
- **主檔有值的欄位不會被覆蓋**，除非放進 `FORCE_OVERWRITE_COLUMNS`
- 欄位名稱有空白會自動 strip（讀檔時處理）
- CSV big5 讀取失敗會自動 fallback，會印警告
- 網址欄位 `http://` 空值，清洗後自動變空字串
