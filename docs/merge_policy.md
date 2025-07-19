# v6 Merge Policy（合併策略）

## 1. 分支與 worktree
- 每個新功能/修正請建立 feature branch 或 worktree，避免直接在 main 開發。
- 建議命名規則：`feature/xxx`、`fix/xxx`、`refactor/xxx`。
- 可用 `git worktree add ../feature_xxx feature/xxx` 建立平行開發目錄。

## 2. Pull Request / Merge Request 流程
- 每次合併請建立 PR/MR，並指派 reviewer。
- PR 必須附上對應 checklist 狀態（可貼 YAML/JSON 或自動產生報表）。
- PR 必須通過所有自動化測試（pytest、contract test、checklist 驗證腳本）。
- PR 必須通過 code review，無跨層耦合、public 方法回傳純資料。
- 若有 conflict，需先 rebase/main，確保無衝突再合併。

## 3. CI/CD 驗證
- CI pipeline 會自動執行 pytest、coverage、tools/check_checklist.py。
- checklist 未全綠、覆蓋率未達標、或測試失敗時，CI 會拒絕合併。
- 建議每次合併前本地先執行 `python tools/check_checklist.py`。

## 4. 其他規範
- 重要 refactor/大規模合併請先討論設計與分工。
- 文件、API contract、測試必須同步更新。
- 若有 N/A 項目，請於 PR 備註說明。

> 本策略適用於 v6 及後續所有平行開發階段，請團隊成員共同遵守。 