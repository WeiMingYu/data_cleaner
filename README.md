# data_cleaner 📊

> 通用資料清洗框架 — 任何外來 Excel / CSV → 標準清洗 → 比對補齊 → 匯出主檔

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Author](https://img.shields.io/badge/Author-WeiMing%20Yu-orange)](https://github.com/WeiMingYu)

---

## 🎯 這個專案在做什麼？

在整合多來源資料時，常見的痛點：

- 政府開放資料、爬蟲資料、手動收集資料，**欄位名稱各自不同**
- 想補齊主檔裡的空白欄位（例如 email、電話），但不知道哪些是新的、哪些已經有了
- 比對完不確定哪些資料要人工確認

`data_cleaner` 把這個流程標準化成三層架構：

```
任何來源（A檔）→ 清洗成標準格式 → 比對主檔（B檔）→ 匯出結果
```

比對結果自動分三類，一次產出三個 sheet：
| Sheet | 內容 |
|---|---|
| 主檔 | 補齊空白欄位後的完整主檔 |
| 新增資料 | 來源有、主檔沒有的，待確認後合併 |
| 待人工確認 | 比對不到的資料，附說明備註 |

---

## 📁 目錄結構

```
data_cleaner/
│
├── input/              ← 【A檔放這裡】來源檔（外來資料，要清洗的）
├── master/             ← 【B檔放這裡】主檔（要被比對補齊的）
├── output/             ← 【結果輸出到這裡】自動產生
├── temp/               ← 暫存檔（自動建立）
│
├── config.py           ← ⭐ 所有設定（使用者只改這裡）
├── master_schema.py    ← 主檔欄位定義（唯一真相）
├── pipeline.py         ← 執行入口
│
├── layer1_clean/       ← 第一層：清洗
│   ├── base_cleaner.py
│   ├── excel_cleaner.py
│   └── clean_rules.py
│
├── layer2_match/       ← 第二層：比對
│   ├── matcher.py
│   └── dedup.py
│
└── layer3_export/      ← 第三層：匯出
    └── exporter.py
```

---

## 🚀 快速開始

### 1. 安裝相依套件

```bash
pip install -r requirements.txt
```

### 2. 放入資料

```
input/   ← 把 A 檔（來源資料）放這裡
master/  ← 把 B 檔（主檔）放這裡
```

### 3. 設定 config.py（只填檔名）

```python
# 只填檔名，不需要填完整路徑
SOURCE_FILENAME = "ece_data.xlsx"                  # A 檔
MASTER_FILENAME = "整合_學校類_含MAIL_補齊.xlsx"    # B 檔
OUTPUT_FILENAME = "整合_學校類_含MAIL_補齊_更新.xlsx"  # 輸出
```

### 4. 設定欄位對應

```python
# 來源欄位名稱 → 主檔欄位名稱
COLUMN_MAP = {
    "區":    "鄉鎮市區",       # 來源叫「區」，主檔叫「鄉鎮市區」
    "email": "Mail 電子郵件",  # 來源叫 email
    # ... 依實際欄位填寫
}
```

### 5. 設定比對規則

```python
# 依序嘗試，第一個命中的規則算數
MATCH_KEYS = [
    ["電話"],               # 先用電話比對
    ["名稱", "縣市區"],     # 找不到再用名稱+縣市區
]
```

### 6. 執行

```bash
python pipeline.py
```

看完統計後輸入 `y` 確認，結果自動輸出到 `output/`。

---

## 🔧 執行選項

```bash
# 一鍵跑完整流程（建議正式使用）
python pipeline.py

# 分層測試（建議首次使用時逐層確認）
python pipeline.py --layer 1    # 只清洗 A 檔
python pipeline.py --layer 2    # 只比對
python pipeline.py --layer 3    # 只匯出

# 臨時指定不同 A 檔
python pipeline.py --source 另一個來源.xlsx
```

---

## 📋 主檔標準欄位

| 欄位名稱 | 必填 | 說明 |
|---|---|---|
| 公私立 | | 公立 / 私立 |
| 分類 | | 幼兒園 / 國小 / 國中... |
| 縣市區 | | 臺北市 / 新北市... |
| 鄉鎮市區 | | 中正區 / 板橋區... |
| 名稱 | ✅ | 機構名稱（唯一必填）|
| 地址 | | 完整地址 |
| Mail 電子郵件 | | |
| 電話 | | |
| 傳真 | | |
| 網址 | | |
| 備註 | | |
| 資料來源 | | 例：全國教保資訊網 |

欄位定義在 `master_schema.py`，所有層共用同一份，不各自定義。

---

## 🧩 三層架構說明

### Layer 1 — 清洗層 `layer1_clean/`

- 讀取任意 Excel / CSV 來源
- 套用 `clean_rules.py` 裡的清洗規則（全形轉半形、去前綴、標準化縣市名稱...）
- 輸出符合主檔格式的標準 DataFrame

**遇到新的髒資料格式** → 在 `clean_rules.py` 新增函數即可，不動其他程式碼。

### Layer 2 — 比對層 `layer2_match/`

- `dedup.py`：先檢查來源自身有無重複，發現重複只警告，不自動刪除
- `matcher.py`：依 `MATCH_KEYS` 規則與主檔比對，結果分三類：
  - **MATCHED**：找到唯一對應 → 補齊主檔空白欄位
  - **NEW**：主檔沒有 → 整筆放入新增清單
  - **UNMATCHED**：比對不到或多筆命中 → 放入待人工確認

### Layer 3 — 匯出層 `layer3_export/`

- 產出三個 sheet 的 Excel
- 微軟正黑體、標題列藍底白字、欄位自動寬度、凍結標題列

---

## ➕ 擴充方式

### 新增清洗規則

```python
# layer1_clean/clean_rules.py 新增函數
def clean_xxxxx(v) -> str:
    s = clean_str(v)
    # 清洗邏輯
    return s
```

```python
# layer1_clean/base_cleaner.py 的 _apply_rules() 呼叫
if "目標欄位" in df.columns:
    df["目標欄位"] = df["目標欄位"].apply(rules.clean_xxxxx)
```

### 支援新的來源格式

繼承 `BaseCleaner`，實作 `load()` 和 `map_columns()` 兩個方法：

```python
from layer1_clean.base_cleaner import BaseCleaner

class JsonCleaner(BaseCleaner):
    def load(self):
        import json, pandas as pd
        with open(self.source_file, encoding="utf-8") as f:
            return pd.DataFrame(json.load(f))

    def map_columns(self, raw_df):
        # 依 COLUMN_MAP 做欄位對應
        ...
```

---

## ⚠️ 注意事項

- **換來源只改 `config.py`**，不需要動程式碼
- 主檔已有值的欄位**不會被覆蓋**，除非加入 `FORCE_OVERWRITE_COLUMNS`
- CSV 讀取失敗時自動 fallback utf-8-sig → big5
- `http://` 空網址清洗後自動變空字串
- 比對鍵（電話、名稱）為空的資料會跳過該條規則

---

## 📦 相依套件

```
pandas >= 2.0.0
openpyxl >= 3.1.0
xlrd >= 2.0.0
```

---

## 👤 作者

**俞威名 WeiMing Yu**
- GitHub：[@WeiMingYu](https://github.com/WeiMingYu)

---

## 📄 License

MIT License
