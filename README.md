# v6 GUI Presenter

[![CI](https://github.com/<YOUR_GITHUB_ORG>/<YOUR_REPO>/actions/workflows/python-app.yml/badge.svg)](https://github.com/<YOUR_GITHUB_ORG>/<YOUR_REPO>/actions)
[![codecov](https://codecov.io/gh/<YOUR_GITHUB_ORG>/<YOUR_REPO>/branch/main/graph/badge.svg?token=YOUR_CODECOV_TOKEN)](https://codecov.io/gh/<YOUR_GITHUB_ORG>/<YOUR_REPO>)

## 專案簡介

本專案為 v6 GUI Presenter，實作 MVP 架構，支援 AST 結構顯示、事件鏈路、context 狀態流轉、權限控管、效能壓力測試等，並具備完整 TDD/integration 測試與 CI/CD 自動化。

## 安裝與本地測試

```bash
# 建立虛擬環境
python3 -m venv .venv
source .venv/bin/activate
# 安裝依賴
pip install -r requirements.txt
# 執行所有測試
python run_all_tests.py
# 或直接用 pytest
pytest --cov=src --cov-report=term
```

## CI/CD 狀態
- 每次 push/PR 會自動執行所有單元/整合/壓力測試，並產生 coverage 報告。
- 狀態徽章如上，詳細請見 [Actions](https://github.com/<YOUR_GITHUB_ORG>/<YOUR_REPO>/actions) 與 [Codecov](https://codecov.io/gh/<YOUR_GITHUB_ORG>/<YOUR_REPO>).

## 開發/測試流程
1. 依 v6 文件規劃，所有功能皆採 TDD 開發，先寫測試再實作。
2. Presenter/Model/View 事件、context、權限、效能、壓力、合約測試皆有覆蓋。
3. PR/commit 時 CI 會自動驗證所有測試通過。
4. 測試覆蓋率可於本地或 Codecov 查詢。

## 常見問題（FAQ）
- **Q: CI 失敗怎麼辦？**
  - 請先本地執行 pytest/coverage，確認所有測試通過。
- **Q: 如何新增/修改 Presenter 事件？**
  - 請同步補齊對應單元/合約測試，確保 context/debug_info/狀態流轉正確。
- **Q: 如何執行效能/壓力測試？**
  - 直接執行 pytest，壓力測試已納入單元測試。
- **Q: 如何查詢 context schema 或事件 API？**
  - 請參考 `docs/development/v6_GUI_presenter.md` 與 `src/presenter/context_schema.py`。

## 參考文件
- [docs/development/v6_GUI_presenter.md](docs/development/v6_GUI_presenter.md)
- [tests/presenter/test_struct_presenter.py](tests/presenter/test_struct_presenter.py)
- [tests/integration/test_presenter_view_contract.py](tests/integration/test_presenter_view_contract.py)

---
> 歡迎貢獻、提問與 issue！
