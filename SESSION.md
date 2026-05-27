# SESSION.md — data_cleaner
**專案：通用資料清洗框架**
**路徑：** `C:\bk\py\data_cleaner\`
**GitHub：** https://github.com/WeiMingYu/data_cleaner
**最後更新：2026-05-27**

---

## 目前狀態
- 完成度：約 50%
- 系統可執行：⚠️ 結構完整，尚未實際測試
- 已測試來源：❌（尚未）
- VARIABLES.md：✅ 已同步
- SESSION.md：✅ 已同步

---

## 上次做到
- 建立完整三層專案結構（layer1/2/3 + pipeline）
- 改善目錄設計：input/ master/ output/ 三個固定資料夾
- config.py 改為只填檔名，路徑自動組合，不需手動填完整路徑
- pipeline.py 加入啟動檢查（A檔/B檔不存在時提示放置位置）
- 產出開發文件 v1.0（.docx）
- 更新 VARIABLES.md / SESSION.md

---

## 待完成
- 實際測試：ece_data.xlsx → 整合_學校類_含MAIL_補齊.xlsx
- 補齊 README.md（GitHub 用）
- 開發文件 v1.1（補目錄設計說明）

---

## 已知問題 / 待確認
- 尚未實際跑過，可能有 Windows import 路徑問題
- layer2 多筆命中目前直接丟 UNMATCHED，有需要再細化
- GitHub 上的版本是否與本地同步？需確認

---

## 踩過的坑
（本次為初始建立，尚無踩坑記錄）

---

## 下次開頭貼給 Claude

> 專案 data_cleaner，路徑 C:\bk\py\data_cleaner\，GitHub: https://github.com/WeiMingYu/data_cleaner
> 上次做到：三層架構 + input/master/output 目錄設計完成，尚未實際測試
> 今天要做：（填入今天目標）
> 已知問題：尚未實際跑過，可能有 import 路徑問題
