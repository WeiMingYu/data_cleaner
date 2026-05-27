

# data_cleaner 通用資料清洗框架 v1.0

### 文件名稱 	data_cleaner 通用資料清洗框架 開發文件
### 版本	v1.0
### 日期	2026-05-27
### 作者	俞威名（WeiMing）
### 專案路徑	C:\bk\py\data_cleaner\
### 說明	任意外來資料 → 標準清洗 → 比對補齊 → 匯出主檔
 
# 一、專案概述
## 1.1 目的
data_cleaner 是一個通用資料清洗框架，設計目標是讓任何外來資料都能透過統一的三層流程進行清洗、比對、補齊，最後匯出為標準主檔格式。
本框架的核心概念：
•	外來資料格式不一致（Excel/CSV、欄位名稱各異）→ 第一層統一清洗成標準格式
•	清洗後與既有主檔比對 → 第二層找出哪些是已有資料（補齊空白）、哪些是新資料
•	確認後匯出多 sheet Excel → 第三層產出更新後主檔、新增清單、待人工確認清單

## 1.2 適用場景
凡需要整合多來源資料並維護統一主檔的情境，均可套用此框架。目前已知的應用場景：
•	教育機構資料整合（幼兒園、國小、國中、高中）
•	政府開放資料與自建主檔的比對補齊
•	爬蟲資料與現有資料庫的去重合併

## 1.3 主檔固定欄位 (依不同的需求改變設定)

| 欄位名稱 | 必填 | 說明 |
| -------- | -------- | -------- |
| 公私立     |否     | 公立 / 私立 / 空白    |
| 分類       | 否    | 幼兒園 / 國小 / 國中 / 高中...     |
| 縣市區     | 否     | 臺北市 / 新北市...     |
| 鄉鎮市區   | 否    | 中正區 / 板橋區...（無則空白）     |
| 名稱       | 是     | 機構名稱（必填，空白視為無效）     |
| 地址       | 否     | 完整地址     |
| Mail電子郵件| 否     | 聯絡 email     |
| 電話       | 否    | 聯絡電話     |
| 傳真     | 否     | 傳真號碼    |
| 網址     |否     | 官方網站 URL     |	
| 備註     | 否     | 備用欄位     |		
| 資料來源    | 否     | 例：全國教保資訊網     |		


# 二、系統架構
## 2.1 三層架構設計
整個框架分為三個獨立的層次，每層只負責一件事，互不耦合：

| 層次 |	名稱|	職責|
|-----|--------|----|
| Layer 1 |	清洗層（layer1_clean）|	讀取任意來源 → 套用清洗規則 → 輸出標準格式 DataFrame|
| Layer 2 |	比對層（layer2_match）|	來源資料 vs 主檔比對 → 分類為 MATCHED / NEW / UNMATCHED |
| Layer 3 |	匯出層（layer3_export）|	比對結果 → 寫出多 sheet Excel（主檔/新增/待確認）|

## 2.2 資料流程
完整資料流如下：

任意來源檔案（Excel / CSV）
    ↓  Layer 1：ExcelCleaner.clean()
標準格式 DataFrame（符合 MASTER_COLUMNS）
    ↓  Layer 2：DedupChecker → Matcher.run()
三種結果：updated_master / new_df / unmatched_df
    ↓  Layer 3：Exporter.export()
輸出 Excel（主檔 / 新增資料 / 待人工確認）

## 2.3 檔案結構

```
data_cleaner/
├── config.py               ← 所有設定（換來源只改這裡）
├── master_schema.py        ← 主檔欄位定義（唯一真相）
├── pipeline.py             ← 一鍵主流程入口
│
├── layer1_clean/
│   ├── base_cleaner.py     ← 清洗基底（抽象類別）
│   ├── excel_cleaner.py    ← Excel / CSV 清洗器
│   └── clean_rules.py      ← 清洗規則庫（遇到新髒資料加這裡）
│
├── layer2_match/
│   ├── matcher.py          ← 比對主邏輯
│   └── dedup.py            ← 來源自身去重檢查
│
├── layer3_export/
│   └── exporter.py         ← 匯出多 sheet Excel
│
├── temp/                   ← 暫存檔（自動建立）
├── VARIABLES.md / SESSION.md / requirements.txt
```

# 三、模組說明
## 3.1 master_schema.py — 主檔欄位定義
整個框架的「唯一真相」。所有欄位名稱、順序、必填設定都在此定義，其他模組都從這裡 import，不各自定義。

| 常數 / 函數	| 說明 |
|---------------|------|
MASTER_COLUMNS	|主檔欄位清單（list），決定 Excel 輸出的欄位順序
REQUIRED_COLUMNS	|必填欄位（list），清洗後若空白則視為無效資料移除
empty_record()	|回傳一筆空的主檔格式 dict，供清洗層填充

## 3.2 config.py — 所有設定
換來源只改這個檔案，不需要動其他程式碼。

變數	預設值	說明
SOURCE_FILE	ece_data.xlsx	來源檔案路徑
MASTER_FILE	整合_學校類_含MAIL_補齊.xlsx	主檔路徑
OUTPUT_FILE	整合_...更新.xlsx	輸出路徑
COLUMN_MAP	（dict）	來源欄位 → 主檔欄位對應表
MATCH_KEYS	[['電話'],['名稱','縣市區']]	比對規則（由使用者定義）
FILL_COLUMNS	（list）	補齊欄位（主檔空白才補）
FORCE_OVERWRITE_COLUMNS	[]	強制覆蓋欄位（謹慎使用）
CONFIRM_BEFORE_WRITE	True	寫入前詢問 y/n 確認

## 3.3 Layer 1 — 清洗層
### 3.3.1 clean_rules.py — 清洗規則庫
所有清洗函數集中在此。遇到新的髒資料格式，在這裡加規則即可，不影響其他模組。

函數	說明
clean_str(v)	基本清洗：None/NaN 轉空字串、去首尾空白
clean_str_fullwidth(v)	全形轉半形（數字、英文、空格）
clean_name_prefix(v)	去掉名稱前面的縣市區前綴（例：臺北市中正區→）
clean_county(v)	縣市名稱標準化（台→臺、去除多餘空白）
clean_phone(v)	電話清洗：統一分隔符、去空白
clean_address(v)	地址清洗：去除 [01] 類前綴編碼
clean_email(v)	Email：轉小寫、去空白
clean_url(v)	網址：過濾 http:// 空網址

### 3.3.2 base_cleaner.py — 清洗基底
定義清洗的標準流程，子類別只需實作「讀檔」和「欄位對應」兩件事，通用流程（套規則、驗證、補欄位）由基底類別統一處理。

### 3.3.3 excel_cleaner.py — Excel/CSV 清洗器
支援 .xlsx / .xls / .csv。讀取失敗時自動 fallback（utf-8-sig → big5）。欄位對應依 config.COLUMN_MAP 執行。

## 3.4 Layer 2 — 比對層
### 3.4.1 matcher.py — 比對主邏輯
依 config.MATCH_KEYS 定義的規則，逐筆比對來源資料與主檔。比對結果分三類：

|結果 |	條件	|處理方式|
|----|---------|------|
MATCHED|	主檔找到唯一對應筆數	|補齊主檔空白欄位（FILL_COLUMNS）
NEW	|主檔找不到這筆資料	|整筆放入「新增資料」sheet
UNMATCHED|	比對不到或多筆命中	|放入「待人工確認」sheet，加比對備註

MATCH_KEYS 支援多組規則，依序嘗試，第一組命中即停止。範例：
MATCH_KEYS = [
    ["電話"],              # 第一優先：電話完全相同
    ["名稱", "縣市區"],    # 第二優先：名稱+縣市區都相同
]

### 3.4.2 dedup.py — 來源去重檢查
在進入 Matcher 之前，先檢查來源資料自身有沒有重複（同樣的電話、同樣的名稱+縣市區），避免同一筆資料被比對兩次。發現重複只警告，不自動刪除。

## 3.5 Layer 3 — 匯出層
### 3.5.1 exporter.py — 匯出多 sheet Excel
把比對結果寫成三個 sheet 的 Excel 檔：
•	Sheet「主檔」：補齊後的完整主檔（原有資料已補空白欄位）
•	Sheet「新增資料」：來源有、主檔沒有的新資料（待手動審核後決定是否合併主檔）
•	Sheet「待人工確認」：比對不到的資料，附加「比對備註」欄說明原因
輸出 Excel 套用微軟正黑體、標題列藍底白字、欄位自動寬度、凍結標題列。

 

# 四、使用說明
## 4.1 環境安裝
```
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

```
## 4.2 換新來源資料的步驟
只需修改 config.py，其他程式碼完全不動。

| 步驟	| 動作	| 說明|
|--------|--------|----|
1|	修改 SOURCE_FILE	|指向新的來源檔案路徑|
2|	修改 COLUMN_MAP	|對應來源欄位名稱 → 主檔欄位名稱
3|	確認 MATCH_KEYS	|調整比對規則（用電話？還是名稱+縣市區？）
4|	修改 OUTPUT_FILE	|設定輸出路徑
5|	執行 pipeline.py	|跑完三層流程

## 4.3 執行方式
一鍵跑完全流程

'''
python pipeline.py
'''

#### 會依序跑三層，最後顯示統計後詢問「確定要寫入嗎？(y/n)」。輸入 y 才真正寫出 Excel。

### 單層測試（建議先逐層驗證）
#### python pipeline.py --layer 1    # 只跑清洗，看 temp/layer1_clean.xlsx
#### python pipeline.py --layer 2    # 確認清洗結果 OK 再跑比對
#### python pipeline.py --layer 3    # 只跑匯出（需要先有 Layer 2 暫存檔）

'''
指定不同來源檔案
python pipeline.py --source C:\bk\py\new_source.xlsx
'''

## 4.4 COLUMN_MAP 設定範例
以 ECE 幼兒園資料（ece_data.xlsx）為例，來源欄位和主檔欄位名稱不同時的設定方式：
COLUMN_MAP = {
    "公私立":   "公私立",         # 名稱相同，直接對應
    "區":       "鄉鎮市區",       # 來源叫「區」，主檔叫「鄉鎮市區」
    "email":    "Mail 電子郵件",  # 來源叫 email，主檔叫「Mail 電子郵件」
    "學校名稱": "名稱",           # 來源叫「學校名稱」，主檔叫「名稱」
}
來源沒有的欄位不需要列，對應的主檔欄位自動填空白。

## 4.5 比對規則設定範例
MATCH_KEYS 是 list of list，外層多組依序嘗試，內層欄位全部相同才算命中：
```
# 電話比對
MATCH_KEYS = [["電話"]]

# 先試電話，找不到再試名稱+縣市區
MATCH_KEYS = [["電話"], ["名稱", "縣市區"]]

# 名稱比對（名稱有唯一性時）
MATCH_KEYS = [["名稱"]]
```


# 五、擴充指南
## 5.1 新增清洗規則
遇到新的髒資料格式，在 layer1_clean/clean_rules.py 新增函數，然後在 base_cleaner.py 的 _apply_rules() 中呼叫。
# clean_rules.py 新增函數
def clean_xxxxx(v) -> str:
    """說明這個規則在清洗什麼"""
    s = clean_str(v)
    # ... 清洗邏輯 ...
    return s

# base_cleaner.py 的 _apply_rules() 中呼叫
if "目標欄位" in df.columns:
    df["目標欄位"] = df["目標欄位"].apply(rules.clean_xxxxx)

## 5.2 支援新的來源格式
繼承 BaseCleaner，實作 load() 和 map_columns() 兩個方法，即可支援任何格式的來源資料。
# 例：新增 JSON 來源清洗器

```
from layer1_clean.base_cleaner import BaseCleaner

class JsonCleaner(BaseCleaner):
    def load(self):
        import json, pandas as pd
        with open(self.source_file, encoding="utf-8") as f:
            return pd.DataFrame(json.load(f))

    def map_columns(self, raw_df):
        # 根據 config.COLUMN_MAP 做欄位對應
```
        

## 5.3 一鍵完成（未來規劃）
當三層流程測試穩定後，可以把「確認後新增到主檔」的動作也納入 pipeline，實現真正一鍵完成：
•	Layer 3 輸出後，把「新增資料」sheet 的內容直接 append 到主檔
•	加入 --auto 參數，跳過 y/n 確認（適合排程自動執行）

 

# 六、踩坑與注意事項

| 問題	| 原因	| 解法 |
|--------|---------|-----|
|CSV big5 讀取錯誤	|部分政府資料用 big5 編碼	|ExcelCleaner 自動 fallback，會印警告訊息|
電話被轉成 float|Excel讀取時把數字欄當 |float read_excel 加 dtype=str，全部讀成字串
欄位名稱有空白|Excel 欄位名稱帶頭尾空格|讀檔後統一 strip 欄位名稱
網址欄有空網址|爬蟲抓到 http:// |空值	clean_url() 過濾，變空字串
名稱帶縣市區前綴|部分來源名稱含地區前綴|	clean_name_prefix() 自動去除，可用 CLEAN_NAME_PREFIX=False 關閉
同名稱多筆資料|來源或主檔有重複 dedup.py | 事先警告，不自動刪除讓使用者確認
import 路徑問題（Windows）|相對路徑在 Windows 有時出錯|	各模組用 sys.path.insert 明確加根目錄

 

# 七、版本記錄
|   日期	 |  版本   |   異動內容   |
|---------|---------|-------------|
| 2026-05-27	|v1.0	|初始建立：三層架構（layer1/2/3）、pipeline.py、master_schema.py、config.py|

