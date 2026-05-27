# 專案變數總表
**專案：data_cleaner — 通用資料清洗框架**
**路徑：** `C:\bk\py\data_cleaner\`
**最後更新：2026-05-27**
**規則：每次修改來源設定或新增功能，同步更新此文件**

---

## 一、主檔欄位定義（master_schema.py）

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

## 二、config.py 關鍵設定

| 變數 | 說明 | 範例值 |
|---|---|---|
| SOURCE_FILE | 來源檔案路徑 | `C:\bk\py\ece_data.xlsx` |
| MASTER_FILE | 主檔路徑 | `C:\bk\py\整合_學校類_含MAIL_補齊.xlsx` |
| OUTPUT_FILE | 輸出路徑 | `C:\bk\py\整合_學校類_含MAIL_補齊_更新.xlsx` |
| COLUMN_MAP | 來源欄位 → 主檔欄位對應 dict | 每次換來源改這裡 |
| MATCH_KEYS | 比對規則（list of list） | `[["電話"], ["名稱", "縣市區"]]` |
| FILL_COLUMNS | 補齊欄位清單 | 主檔空白才補 |
| FORCE_OVERWRITE_COLUMNS | 強制覆蓋欄位 | 通常留空 |
| CONFIRM_BEFORE_WRITE | 寫入前詢問確認 | `True` |

---

## 三、比對結果分類

| 分類 | 說明 | 輸出 Sheet |
|---|---|---|
| MATCHED | 找到主檔對應資料，補齊空白欄位 | 主檔（補齊後） |
| NEW | 主檔沒有這筆，視為新增 | 新增資料 |
| UNMATCHED | 比對不到或多筆命中，無法確定 | 待人工確認 |

---

## 四、暫存檔（temp/）

| 檔案 | 內容 | 由哪層產出 |
|---|---|---|
| layer1_clean.xlsx | 清洗後的來源資料（標準格式） | Layer 1 |
| layer2_new.xlsx | 新增資料 | Layer 2 |
| layer2_unmatched.xlsx | 待人工確認資料 | Layer 2 |

---

## 五、⚠️ 重要注意事項

- **換來源只改 config.py 的 COLUMN_MAP 和 SOURCE_FILE**，不需要動其他檔案
- **比對邏輯由 MATCH_KEYS 定義**，可設多組規則，依序嘗試
- **主檔有值的欄位不會被覆蓋**，除非放進 FORCE_OVERWRITE_COLUMNS
- 來源欄位名稱有空白會自動 strip（讀檔時處理）
- CSV big5 編碼讀取失敗會自動 fallback，會印警告
- 網址欄位如果是 `http://` 或 `https://` 空值，清洗後會變空字串

---

## 六、檔案結構

```
data_cleaner/
├── config.py               ← 所有設定（換來源只改這裡）
├── master_schema.py        ← 主檔欄位定義（唯一真相）
├── pipeline.py             ← 一鍵主流程
│
├── layer1_clean/
│   ├── __init__.py
│   ├── base_cleaner.py     ← 清洗基底（抽象類別）
│   ├── excel_cleaner.py    ← Excel/CSV 清洗器
│   └── clean_rules.py      ← 清洗規則庫（遇到新髒資料加這裡）
│
├── layer2_match/
│   ├── __init__.py
│   ├── matcher.py          ← 比對主邏輯
│   └── dedup.py            ← 去重檢查
│
├── layer3_export/
│   ├── __init__.py
│   └── exporter.py         ← 匯出 Excel（多 sheet）
│
├── temp/                   ← 暫存檔（自動建立）
├── VARIABLES.md
├── SESSION.md
├── requirements.txt
└── .gitignore
```
