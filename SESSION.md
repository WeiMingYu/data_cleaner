# SESSION.md — data_cleaner
**專案：通用資料清洗框架**
**路徑：** `C:\bk\py\data_cleaner\`
**最後更新：2026-05-27**
**規則：每次對話結束前更新，下次開頭貼給 Claude**

---

## 目前狀態
- 完成度：約 40%
- 系統可執行：⚠️ 結構建好，尚未實際測試
- 已測試來源：❌（尚未）
- VARIABLES.md：✅ 已同步

---

## 上次做到
- 建立完整三層專案結構
- Layer 1：clean_rules.py / base_cleaner.py / excel_cleaner.py
- Layer 2：matcher.py / dedup.py
- Layer 3：exporter.py
- pipeline.py 一鍵主流程（含 --layer 參數可單層測試）
- config.py 以 ECE 幼兒園資料為範例設定

---

## 今天要做
- 把現有的 import_to_master.py 和 merge_sources.py 邏輯搬進三層架構
- 測試跑 ece_data.xlsx → 整合_學校類_含MAIL_補齊.xlsx

---

## 已知問題
- 尚未實際跑過，可能有 import 路徑問題（Windows 路徑）
- layer2 matcher 的 CONFLICT 邏輯目前直接丟到 UNMATCHED，有需要再細化

---

## 踩過的坑
（本次為初始建立，尚無踩坑記錄）

---

## 下次開頭貼給 Claude

> 專案 data_cleaner，路徑 C:\bk\py\data_cleaner\，無 port
> 上次做到：三層架構建立完成（layer1/2/3 + pipeline），尚未實際測試
> 今天要做：測試跑 ece_data.xlsx 比對補齊主檔
> 已知問題：尚未實際跑過，可能有 import 路徑問題
