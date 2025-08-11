# v9 Parser Top-Level Union / Pragma Pack / `_split_member_lines` Development Checklist

## 背景
- 此清單延續 v9 解析器規劃，聚焦於 **頂層 `union` 支援**、**`#pragma pack` 解析** 與 **穩健的 `_split_member_lines`**。
- 透過 TDD 小步迭代，確保每項功能均以測試保護並維持既有行為。

## 核心檢查項目
### 1. 頂層 `union` 支援
- [ ] 新增 `test_parse_top_level_union_returns_ast`
- [ ] `parse_aggregate_definition` 能建立 `UnionNode` 根節點
- [ ] 處理匿名或帶 `__attribute__` 的 `union`
- [ ] 解析失敗時提供明確錯誤訊息

### 2. `#pragma pack` 支援
- [ ] 新增 `test_parse_struct_with_pragma_pack_applies_alignment`
- [ ] `_handle_directives` 維護 pack 堆疊並套用到節點
- [ ] 測試巢狀 `push/pop` 與未配對 `pop`
- [ ] 未知 `pragma` 指令觸發警告或錯誤

### 3. `_split_member_lines` 改寫
- [ ] 新增 `test_split_member_lines_handles_nested_union`
- [ ] 以括號深度追蹤避免巢狀聚合被誤切
- [ ] 處理行內註解與 `\\\n` 續行符號
- [ ] 支援含巨集或位元欄位的成員宣告

## TDD 迭代建議
1. Commit 1：新增頂層 `union` 失敗測試（Red）
2. Commit 2：實作 `parse_aggregate_definition`（Green）
3. Commit 3：重構入口函式與 AST 建立（Refactor）
4. Commit 4：新增 `pragma pack` 測試案例（Red）
5. Commit 5：導入 `_handle_directives` 與對齊堆疊（Green）
6. Commit 6：整理指令解析與錯誤處理（Refactor）
7. Commit 7：新增 `_split_member_lines` 邊界測試（Red）
7. Commit 8：改寫 `_split_member_lines` 以支援續行與巨集（Green）
9. Commit 9：模組化拆分函式並更新文件（Refactor）

## 開發時程
- **週 1**：完成頂層 `union` 支援與相關測試
- **週 2**：導入 `#pragma pack` 解析與錯誤處理
- **週 3**：重寫 `_split_member_lines`，涵蓋註解與巨集情境
- **週 4**：整合回歸測試與文件整理，準備釋出 v9

---

此清單協助追蹤 v9 解析器於頂層 `union`、`#pragma pack` 與 `_split_member_lines` 的 TDD 開發進度，確保各項功能完整落實。
