# shuttle_app

動態共乘接駁 Demo(臺北市),目標是面試用的後端作品。

## 合作規則
- 我在學習:核心業務邏輯由我自己寫,你只給提示與 Review。我明確要求完整實作才可以直接寫。
- 一次一個有驗收條件的小任務;使用繁體中文,簡潔具體。
- 不自行 commit、push、merge,不做破壞性操作,不覆寫我未確認的修改。
- 不修改 demo_fastapi 專案。不刪除歷史練習檔。
- 沒實際執行的測試,不可說成已通過。

## 專案現況
- 分支 feature/map-demo;Python 3.10.12;FastAPI、uvicorn、PyYAML 已裝。
- main.py 是舊的終端機派車 Demo,保留當參考;執行它會寫回 test_vehicles.json,測試請只跑 test_assign_order.py。
- 座標一律用 {"lat","lng"} 命名欄位(OSRM 經度在前、Leaflet 緯度在前)。
- 路徑只查一次存成 routes.json,Demo 讀檔,不每次連網。
