# v6 View/Presenter 平行開發前事前準備 Checklist

本文件列出進行 v6 View (V) / Presenter (P) 平行開發前，必須完成的所有事前準備與前置條件，供團隊協作、review、進度追蹤。

| 項目 | 子項目/說明 | 驗證方式 | 完成狀態 |
|------|-------------|----------|----------|
| Model AST/資料結構 ready | 巢狀 struct/union/array/bitfield AST 結構正確 | 單元測試 | [  ] |
|  | AST 格式與 V2P API 文件一致 | contract/schema test | [  ] |
| AST/資料結構測試覆蓋 | 單元測試覆蓋率 > 90% | pytest + coverage | [  ] |
|  | XML/JSON 驅動多組巢狀結構測資 | pytest | [  ] |
|  | flatten/compare helper 可用 | helper 測試 | [  ] |
| V2P API/Context/事件流 mock/stub/contract test | mock Presenter/View 可單獨跑通 | pytest | [  ] |
|  | contract test 覆蓋所有事件/狀態流 | contract/schema test | [  ] |
|  | context schema 驗證 | schema validation | [  ] |
| Worktree/分支/CI/CD 準備 | worktree/feature branch 已建立 | git branch | [  ] |
|  | CI/CD pipeline 可自動跑測試 | CI/CD log | [  ] |
|  | 合併策略明確 | PR template | [  ] |
| 現有 GUI/Presenter/Model decouple/refactor | 無跨層直接存取 | code review | [  ] |
|  | Observer/callback 機制統一 | code review | [  ] |
|  | public 方法回傳純資料 | code review | [  ] |
| 現有測試/快取/狀態管理機制 review | layout cache/undo/redo/user_settings/debug 可共用 | pytest | [  ] |
|  | 測試覆蓋所有快取/狀態分支 | coverage | [  ] |
| V2P API 文件/contract 最終 review | 文件與 codebase 一致 | contract test + code review | [  ] |
|  | 欄位/事件/權限/版本/錯誤/測試皆覆蓋 | contract test | [  ] |
|  | API 版本號明確 | 文件檢查 | [  ] |

---

## 使用說明
- 請於每項完成時將 [  ] 改為 [x]，並可加註日期/負責人/備註。
- 建議每次平行開發/大規模 refactor 前都先 review 本 checklist。
- 若有新需求，請補充 checklist 項目。

---

## 進度追蹤範例

| 項目 | 子項目/說明 | 驗證方式 | 完成狀態 |
|------|-------------|----------|----------|
| Model AST/資料結構 ready | 巢狀 struct/union/array/bitfield AST 結構正確 | 單元測試 | [x] 2024-07-22 by Alice |
|  | AST 格式與 V2P API 文件一致 | contract/schema test | [x] 2024-07-22 by Alice |
| ... | ... | ... | ... |

---

## 自動化進度追蹤建議

- 建議將 checklist 狀態同步於 YAML/JSON 檔（如 v6_parallel_dev_checklist.yaml），CI pipeline 每次測試後自動更新。
- 可用 badge（如 GitHub Actions badge）顯示「Model AST 測試通過」「API contract 測試通過」等狀態。
- PR/merge request 時，要求勾選 checklist，CI 驗證未全綠則拒絕合併。
- 可產生自動化報表（HTML/Markdown）供團隊 review。

### YAML checklist 範例
```yaml
model_ast_ready: true
ast_schema_match: true
ast_test_coverage: 92
ast_data_driven: true
flatten_helper: true
v2p_mock_presenter: true
v2p_contract_test: true
v2p_schema_validation: true
worktree_ready: true
ci_cd_ready: true
merge_policy: true
decouple_no_cross_layer: true
decouple_observer: true
decouple_pure_data: true
cache_state_ready: true
cache_state_coverage: true
api_doc_review: true
api_fields_events: true
api_version: true
```

### CI 驗證腳本（pseudo code）
```bash
if grep -q 'false' v6_parallel_dev_checklist.yaml || [ $(yq .ast_test_coverage v6_parallel_dev_checklist.yaml) -lt 90 ]; then
  echo 'Checklist 未全綠，build fail'
  exit 1
fi
```

---

## 進度同步與自動化驗證

- 建議每次平行開發、合併、或大規模 refactor 前，逐項 review 並標註 checklist 狀態。
- 可將 checklist 狀態同步於 YAML/JSON 檔（如 v6_parallel_dev_checklist.yaml），供 CI pipeline 自動驗證。
- YAML/JSON 欄位可用 true/false 或百分比（如 ast_test_coverage: 92）。
- 若某項目暫不適用，請標註為 N/A，並於備註欄說明原因。
- CI pipeline 可依據 YAML/JSON 狀態自動決定是否允許合併（如有 false 或覆蓋率不足則拒絕合併）。
- 建議每次 PR/merge request 時，要求同步 checklist 狀態，並於 CI 驗證未全綠則拒絕合併。
- 可產生自動化報表（HTML/Markdown）供團隊 review。

> Checklist 狀態同步與自動化驗證，是確保平行開發品質與進度一致的關鍵步驟。

---

> 本文件為 v6 平行開發協作基礎，請團隊定期 review 與更新。 
> 若僅兩人平行開發，i18n/a11y/進階 scaffold 可標註 N/A，僅需確保 V/P contract、事件流、狀態流、mock/stub、基本權限/readonly 行為測試全綠即可。 