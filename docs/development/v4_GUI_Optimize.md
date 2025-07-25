# v4 GUI 優化規劃與 TDD 流程

## 一、現況分析
- GUI（Tkinter, src/view/struct_view.py）在手動 struct 編輯、成員變動、layout 更新時，會頻繁重建 Model/Presenter 並重算 layout，造成效能浪費。
- 當 struct 成員未變動時，仍會重複 layout 計算與 UI refresh。
- 隨 struct 成員數量增加，效能瓶頸逐漸明顯。

## 二、優化目標
- 減少不必要的 Model/Presenter 實例化與 layout 重算。
- 實作 layout 計算快取（cache），僅在成員或 size 變動時才重算。
- 提升 GUI 操作流暢度，特別是大量成員或頻繁操作時。
- 保持現有功能、驗證、錯誤提示完全正確。

## 三、TDD 優化流程

### 1. 建立效能基準測試（Performance Baseline）
- 新增 GUI 操作自動化測試（可用 unittest.mock/pytest + tkinter event 模擬）。
- 量測：
  - 新增/刪除成員時的 layout 計算次數（可 mock presenter/model 方法計數）。
  - 大型 struct（>100 members）操作時的 UI refresh 時間。
  - 典型操作流程（新增、複製、刪除、切換 tab）平均耗時。
- 記錄現有行為作為 baseline。

### 2. 設計快取與重算觸發條件
- 只在 struct 成員或 size 變動時，才觸發 layout 重算。
- 其他 UI 操作（如僅切換欄位、驗證提示）不重算 layout。
- presenter/model 提供 layout cache，view 只取用現有結果。

### 3. 單元測試（Unit Test）
- 測試 layout cache 正確性：
  - 成員未變動時，layout 結果不變且不重算。
  - 成員/size 變動時，cache 自動失效並重算。
- 測試 presenter/model cache 行為覆蓋所有分支。

### 4. 整合測試（Integration Test）
- GUI 操作流程自動化，驗證：
  - 操作流暢度提升（可用 mock/patch 計算重算次數）。
  - 功能、驗證、錯誤提示與原本一致。

### 5. 效能回歸測試（Performance Regression）
- 與 baseline 比較：
  - layout 計算次數顯著下降。
  - 大型 struct 操作明顯加速。
  - 無功能/驗證回歸。

## 四、可量化指標
- layout 計算次數降低 80% 以上（以 mock/patch 統計）。
- 大型 struct 操作平均耗時下降 50% 以上。
- 所有 GUI 測試、驗證、TDD 全數通過。

## 五、預期效益
- 大幅提升 GUI 操作流暢度，減少卡頓。
- 減少不必要的物件建立與計算，降低資源消耗。
- 維持高測試覆蓋率與正確性。

## 六、後續追蹤與自動化
- 可將效能測試納入 CI/CD，定期監控回歸。
- 若有更大 struct 或複雜 GUI 操作需求，可進一步優化。

## 七、細節補充與測試規劃

### 1. 效能基準測試腳本設計
- 使用 `pytest` + `pytest-benchmark` 或 `time` 模組，量測下列操作：
  - 新增 100 個 struct member，量測 UI refresh 與 layout 計算次數。
  - 批次刪除/複製/切換 tab，量測平均耗時。
- 以 `unittest.mock.patch` mock `presenter.compute_member_layout`，統計 layout 計算被呼叫次數。
- 範例：
  ```python
  from unittest.mock import patch
  def test_layout_call_count():
      with patch('src.presenter.struct_presenter.StructPresenter.compute_member_layout') as mock_layout:
          # 執行 GUI 操作流程
          ...
          assert mock_layout.call_count < 預期上限
  ```

### 2. Cache 實作細節
- Presenter 層新增 cache 欄位，key 為 (members, total_size) hash。
- 當 struct 成員或 size 變動時，自動清空 cache。
- View 層僅在 cache miss 時才觸發重算。
- 可用 property/setter 監控 members/size 變動。

### 3. 單元測試（Unit Test）
- 驗證 cache 命中/失效行為：
  - 連續操作不變時，layout 結果一致且不重算。
  - 只要有一個 member 內容變動，cache 失效並重算。
- 範例：
  ```python
  def test_layout_cache_behavior():
      presenter = StructPresenter(...)
      m1 = [{"name": "a", "type": "char", "bit_size": 0}]
      m2 = [{"name": "a", "type": "char", "bit_size": 0}, {"name": "b", "type": "int", "bit_size": 0}]
      l1 = presenter.compute_member_layout(m1, 8)
      l2 = presenter.compute_member_layout(m1, 8)
      assert l1 is l2  # cache hit
      l3 = presenter.compute_member_layout(m2, 8)
      assert l3 is not l1  # cache miss
  ```

### 4. 整合測試（Integration Test）
- 使用 `pytest-qt` 或 tkinter event 模擬，批次操作 GUI，驗證：
  - 操作流暢度（可用 time/perf_counter 量測）
  - 功能、驗證、錯誤提示與 baseline 一致

### 5. Mock/Patch 技巧
- 用 `unittest.mock.patch` 監控/統計 presenter/model 方法呼叫次數。
- 用 `pytest-benchmark` 比較優化前後效能。

### 6. CI/CD 效能監控建議
- 在 GitHub Actions 加入效能回歸測試，若 layout 計算次數/操作耗時超過門檻則警告。
- 可自動產生效能報告（如 coverage report 一樣）。

### 7. 具體改動細節

#### (1) Presenter 層 cache 實作步驟
- 新增 `_layout_cache` 屬性，型別為 dict，key 為 (tuple(members), total_size)，value 為 layout 結果。
- `compute_member_layout(members, total_size)`：
  - 先將 members 轉為 tuple of tuple（確保可 hash）。
  - 查詢 cache，若命中直接回傳。
  - 若 miss，計算 layout，存入 cache 並回傳。
- 新增 `invalidate_cache()` 方法，於 members/size 變動時自動呼叫。
- 若有異常（如 members 格式錯誤），cache 不更新，直接拋出例外。

#### (2) View 層介面設計
- 監控 members/size 變動（如 _on_manual_struct_change），自動呼叫 presenter.invalidate_cache()。
- 只在 cache miss 時才觸發 presenter.compute_member_layout。
- UI refresh 時，僅取用現有 layout 結果。

#### (3) 邊界與異常處理
- 測試空 struct、極大 struct、bitfield 混用、型別錯誤等情境。
- cache 失效後能正確重算，異常時不污染 cache。

### 8. 更完整 TDD 測試腳本範例

#### (1) Cache 行為與異常測試
```python
import pytest
from unittest.mock import patch
from src.presenter.struct_presenter import StructPresenter

def test_layout_cache_hit_and_miss():
    presenter = StructPresenter(...)
    m1 = [{"name": "a", "type": "char", "bit_size": 0}]
    m2 = [{"name": "a", "type": "char", "bit_size": 0}, {"name": "b", "type": "int", "bit_size": 0}]
    l1 = presenter.compute_member_layout(m1, 8)
    l2 = presenter.compute_member_layout(m1, 8)
    assert l1 is l2  # cache hit
    presenter.invalidate_cache()
    l3 = presenter.compute_member_layout(m1, 8)
    assert l3 is not l1  # cache miss after invalidation
    l4 = presenter.compute_member_layout(m2, 8)
    assert l4 is not l3  # new layout for new members

def test_layout_cache_with_invalid_member():
    presenter = StructPresenter(...)
    m_invalid = [{"name": "a", "type": "unknown_type", "bit_size": 0}]
    with pytest.raises(Exception):
        presenter.compute_member_layout(m_invalid, 8)
    # cache 不應被污染
    m1 = [{"name": "a", "type": "char", "bit_size": 0}]
    l1 = presenter.compute_member_layout(m1, 8)
    assert l1 is presenter.compute_member_layout(m1, 8)
```

#### (2) 效能回歸自動化腳本範例
```python
import time
from src.presenter.struct_presenter import StructPresenter

def test_large_struct_performance():
    presenter = StructPresenter(...)
    members = [{"name": f"f{i}", "type": "int", "bit_size": 0} for i in range(200)]
    start = time.perf_counter()
    for _ in range(10):
        presenter.compute_member_layout(members, 256)
    elapsed = time.perf_counter() - start
    assert elapsed < 1.0  # 1 秒內完成
```

#### (3) GUI 操作流程自動化
- 可用 pytest + tkinter event 模擬，或以 mock patch 統計 presenter/model 方法呼叫次數。
- 驗證 UI refresh、驗證提示、錯誤處理皆與 baseline 一致。

### 9. 進階細化主題與規範

#### 1. GUI Layout Cache 機制設計細節
- **Cache key/hash 計算**：
  - 將 members 轉為 tuple of (name, type, bit_size)，再與 total_size 組成 key。
  - 範例：`key = (tuple((m['name'], m['type'], m.get('bit_size', 0)) for m in members), total_size)`
- **Cache 失效觸發點**：
  - 新增/刪除/修改 member
  - 修改 struct size
  - 匯入/重設 struct
- **Cache 清理策略**：
  - 若 struct 操作頻繁，可設計 LRU cache 或定期清空
  - 預設僅保留最近一次 layout 結果即可

#### 2. GUI 操作流程與異常情境清單
- **常見操作流程**：
  | 操作         | 預期 cache 行為 | 需重算 layout |
  |--------------|----------------|--------------|
  | 新增成員     | cache 失效     | 是           |
  | 刪除成員     | cache 失效     | 是           |
  | 修改型別     | cache 失效     | 是           |
  | 切換 tab     | cache 不變     | 否           |
  | 僅驗證提示   | cache 不變     | 否           |
- **異常情境與處理**：
  - 型別錯誤：raise 並不寫入 cache
  - bit_size 不合法：raise 並不寫入 cache
  - UI 卡死：log error 並顯示提示
  - cache 污染：invalidate 並強制重算

#### 3. 效能指標與回歸門檻
- **效能指標**：
  - 200 members 操作 10 次，layout 計算不得超過 2 次，總耗時 < 1 秒
  - 單次 UI refresh < 100ms
- **回歸門檻**：
  - CI/CD 若 layout 計算次數 > 2 或總耗時 > 1 秒則警告

#### 4. 自動化測試腳本設計規範
- **命名慣例**：
  - 單元測試：`test_cache_hit_miss`、`test_cache_invalidation_on_member_change`
  - 整合測試：`test_gui_add_member_performance`
- **Mock/patch 技巧**：
  - 用 patch 統計 presenter/model 方法呼叫次數
- **測試資料生成**：
  - 隨機產生 100~500 members，覆蓋極端情境

#### 5. CI/CD 效能監控與報告格式
- **自動化流程**：
  - 在 GitHub Actions 加入效能測試步驟
  - 失敗時自動產生 markdown 報告，內容包含：
    - 測試名稱、操作次數、layout 計算次數、總耗時、是否通過
- **報告範例**：
  ```markdown
  | 測試        | 操作次數 | layout 計算 | 總耗時(s) | 結果 |
  |-------------|----------|-------------|----------|------|
  | add_member  | 10       | 2           | 0.85     | 通過 |
  ```

#### 6. 文件與程式碼同步機制
- **同步原則**：
  - 每次 cache/GUI/測試邏輯變動，必須同步更新本文件與 README
  - PR/merge 時 reviewer 檢查文件是否同步
- **審查流程建議**：
  - 每次 major 變動，先更新細節文件，review 通過後再進行 code 實作

### 10. 細節展開與具體規格

#### 1. Cache Key/Hash 設計與流程圖
- **Key 算法**：
  - 將 members 轉為 tuple of (name, type, bit_size)，排序後與 total_size 組成 key。
  - 範例：
    ```python
    def make_cache_key(members, total_size):
        key = tuple(sorted((m['name'], m['type'], m.get('bit_size', 0)) for m in members))
        return (key, total_size)
    ```
- **碰撞處理**：
  - 若 key 相同但 layout 結果不符，log warning 並強制重算。
- **失效觸發流程圖**：
  ```mermaid
  flowchart TD
    A[UI 操作] --> B{members/size 是否變動?}
    B -- 是 --> C[cache 失效, 重算 layout]
    B -- 否 --> D[cache 命中, 直接取用]
  ```

#### 2. GUI 操作流程圖與異常分支表
- **操作流程圖**：
  ```mermaid
  flowchart TD
    S[開始] --> A[新增/刪除/修改成員]
    A -->|cache 失效| B[重算 layout]
    S --> C[切換 tab/驗證提示]
    C -->|cache 不變| D[直接顯示]
    B --> E[UI refresh]
    D --> E
  ```
- **異常分支表**：
  | 操作         | 可能異常         | 處理方式           | 用戶提示           |
  |--------------|------------------|--------------------|--------------------|
  | 新增成員     | 型別錯誤         | raise, 不寫入 cache| 顯示型別錯誤訊息   |
  | 修改 bit_size| 非法 bit_size    | raise, 不寫入 cache| 顯示 bitfield 錯誤 |
  | 匯入 struct  | 格式不符         | raise, cache 清空  | 顯示匯入失敗訊息   |
  | UI 卡死      | 計算超時         | log, 強制重算      | 顯示效能警告       |

#### 3. 效能指標分級表與 CI/CD 回報流程
- **分級表**：
  | 規模         | 操作次數 | layout 計算上限 | 總耗時上限 | 等級 |
  |--------------|----------|----------------|------------|------|
  | 50 members   | 10       | 2              | 0.3s       | A    |
  | 200 members  | 10       | 2              | 1.0s       | A    |
  | 500 members  | 10       | 3              | 2.5s       | B    |
- **CI/CD 回報流程圖**：
  ```mermaid
  flowchart TD
    T[效能測試] --> A{是否超過門檻?}
    A -- 否 --> B[標記通過]
    A -- 是 --> C[產生報告, PR 警告]
    C --> D[需人工 review]
  ```

#### 4. 測試命名/覆蓋率/範例
- **命名規則**：
  - `test_cache_key_uniqueness`、`test_cache_invalidation_on_import`、`test_gui_performance_large_struct`
- **覆蓋率要求**：
  - cache 行為、異常分支、極端 struct、效能回歸皆需覆蓋
- **範例**：
  ```python
  def test_cache_key_uniqueness():
      k1 = make_cache_key([{"name": "a", "type": "int", "bit_size": 0}], 8)
      k2 = make_cache_key([{"name": "a", "type": "int", "bit_size": 0}], 8)
      assert k1 == k2
  def test_cache_invalidation_on_import():
      ... # 匯入新 struct 後 cache 必須失效
  ```

#### 5. CI/CD 報告 markdown/html 範例與產生流程
- **Markdown 報告範例**：
  ```markdown
  ## GUI 效能測試報告
  | 測試        | 規模      | 操作次數 | layout 計算 | 總耗時(s) | 結果 |
  |-------------|-----------|----------|-------------|----------|------|
  | add_member  | 200       | 10       | 2           | 0.85     | 通過 |
  | import      | 500       | 5        | 3           | 2.1      | 通過 |
  ```
- **HTML 報告產生**：
  - 可用 pytest-html 或 coverage.py 產生互動式報告，附連結於 PR

#### 6. 文件同步 checklist/自動檢查腳本/審查流程圖
- **Checklist**：
  - [ ] cache/GUI/測試/效能邏輯有無變動？
  - [ ] 文件/README 是否同步？
  - [ ] 測試/CI/CD 報告有無更新？
- **自動檢查腳本**：
  - 可用 pre-commit hook 比對文件與 code 變動
- **審查流程圖**：
  ```mermaid
  flowchart TD
    S[PR 開啟] --> A[自動檢查文件同步]
    A -- 通過 --> B[人工 review]
    A -- 不通過 --> C[要求補文件]
    B --> D[merge]
    C --> D
  ```

---

> 本文件已展開所有細節主題，包含 cache 算法、流程圖、異常分支、效能分級、測試規範、CI/CD 報告與文件同步機制，確保開發流程高效、可追蹤、可維護。 

## v4.1 Presenter 快取與效能統計（2024/07）

### Cache 統計介面
- `get_cache_stats()`：回傳 (hit, miss) 統計，供效能分析與測試。
- `reset_cache_stats()`：重設統計。
- TDD 覆蓋：hit/miss 行為、reset、異常情境（空、極大、格式錯誤）皆有自動化測試。

### Layout 計算效能 hook
- `get_last_layout_time()`：回傳最近一次 layout 計算（非 cache）所花秒數（float）。
- 僅在 cache miss 時更新，cache hit 不變。
- TDD 覆蓋：cache miss/hit 時效能統計正確，所有測試通過。

### 介面範例
```python
presenter = StructPresenter(model)
layout = presenter.compute_member_layout(members, total_size)
hits, misses = presenter.get_cache_stats()
last_time = presenter.get_last_layout_time()
```

### 測試覆蓋
- `tests/test_struct_presenter.py`：
  - cache hit/miss 統計
  - cache 行為異常/極端 case
  - layout 計算效能 hook
- `tests/test_struct_view.py`：
  - GUI 所有操作觸發 cache 失效

## 八、進階優化主題與 TDD 執行順序（2024/07）

### 1. Cache hit/miss 統計與 log（最小改動）
- 目標：在 presenter 加入 cache hit/miss 統計，log 到 console 或測試報告。
- TDD 測試：驗證 cache hit/miss 次數與預期一致。
- 效益：可量化 cache 效能，便於回歸監控。

### 2. Presenter/View cache 介面 docstring/註解補強
- 目標：所有 cache 相關 method（如 invalidate_cache、compute_member_layout）皆有明確 docstring/註解。
- TDD 測試：可用 doctest 或人工 review 驗證。
- 效益：提升維護性與 mock/stub 一致性。

### 3. Exception/Edge Case 測試
- 目標：補充異常與極端 struct/bitfield 測試，確保 cache 不被污染。
- TDD 測試：members 欄位缺失、型別錯誤、極大 struct、極端 bitfield 組合等。
- 效益：提升健壯性。

### 4. UI/邏輯分離（Presenter 回傳純資料，View 負責顯示）
- 目標：Presenter 不直接依賴 Tkinter 物件，回傳純資料，View 負責顯示。
- TDD 測試：mock View 驗證 presenter 回傳資料正確。
- 效益：提升可測性、可維護性。

### 5. Observer pattern/自動 cache 失效（進階）
- 目標：用 observer/callback pattern 讓 presenter 自動監控 members/size 變動，減少 view 重複呼叫。
- TDD 測試：模擬多種變動情境，驗證 cache 自動失效。
- 效益：減少耦合，提升彈性。

### 6. Cache 清理策略（如 LRU，最大改動）
- 目標：實作 LRU cache 或定期清理，避免記憶體佔用過高。
- TDD 測試：大量 struct 操作下 cache 不會無限增長。
- 效益：提升大專案可擴展性。

---

> 建議依上述順序逐步 TDD 實作，每步驟皆有明確測試與驗證指標，確保效能、正確性與可維護性同步提升。 

## v4.2 UI/邏輯分離與 Observer Pattern 優化（2024/07）

### 1. UI/邏輯分離
- Presenter 所有 public 方法僅回傳純資料（dict/list），不直接操作 View。
- View 層根據 Presenter 回傳資料決定 UI 呈現與錯誤提示。
- 目標：減少耦合、提升可測性、支援多 UI 框架。
- TDD：mock View 驗證 Presenter 回傳資料正確，View 測試只驗證 UI 呈現。

### 2. Observer Pattern/自動 cache 失效
- Presenter 提供 observer 註冊/通知介面，View 註冊自身為 observer。
- 當 members/size 變動時，Presenter 自動通知 observer，並自動失效 cache。
- 目標：減少手動同步錯誤，支援多視窗/多 Presenter 協同。
- TDD：模擬多種變動情境，驗證 cache 自動失效與 observer 通知正確。

### 3. TDD 與文件同步
- 每步驟皆同步更新本文件，明確記錄介面、流程、TDD 覆蓋。
- 單元測試與整合測試覆蓋所有分層與 observer 行為。

---

> 建議依上述順序逐步 TDD 實作，確保分層、彈性、可維護性同步提升。 

## v4.2+ UI/邏輯分離與 Observer Pattern 重構開發流程（2024/07）

### 1. Presenter public 方法回傳純資料（低風險）
- 移除所有 `self.view.xxx` 呼叫，改為 return dict/list 結果。
- 先從純資料方法（如 layout/解析）著手，逐步推廣至所有 public 方法。
- TDD：mock View 驗證 Presenter 回傳資料正確。

### 2. 統一錯誤/狀態回傳格式
- Presenter 所有 public 方法遇到錯誤時，return 統一格式（如 `{type: 'error', message: ...}`）。
- View 根據 type 決定顯示/彈窗/狀態。
- TDD：異常情境下 View 能正確顯示錯誤。

### 3. View callback 統一只處理顯示
- View 只根據 Presenter 回傳資料決定 UI 呈現，不再負責邏輯判斷。
- 減少 View 內部 if/else，提升可維護性。

### 4. Observer pattern 實作（中風險）
- Presenter 提供 observer 註冊/通知介面，View 註冊自身為 observer。
- members/size 變動時，Presenter 自動通知 observer，View 被動更新。
- TDD：模擬多種變動情境，驗證 observer 通知與 cache 失效正確。

### 5. 多視窗/多 Presenter 支援（高風險/進階）
- 若有多個 View/Presenter 實例，確保 observer 註冊/通知機制正確。
- TDD：多 observer 註冊、移除、通知流程。

---

> 建議依上述順序逐步 TDD 實作，每步驟皆有明確測試與驗證指標，確保分層、彈性、可維護性同步提升。 

## 九、2024/07 進階優化規劃與改動清單

### 1. 目前可再優化重點
- **效能/重複運算**：Hex grid、member table、Treeview 每次成員/size變動都整體重建，對大型 struct 有效能瓶頸。
- **UI/UX 體驗**：欄位自動 focus、tab 鍵順序未優化，錯誤提示僅在 label，未即時 highlight 錯誤欄位。
- **可維護性/擴充性**：file tab/manual tab 的 hex grid/member table 產生邏輯重複，未共用。事件 callback 命名與分層可再優化。
- **進階功能/可觀察性**：View 層尚未支援 observer pattern，UI 無性能統計/分析介面。

### 2. 所有需改動的地方（依主題分類）

1. **效能優化**
   - `src/view/struct_view.py`：
     - `_render_member_table`、`_build_hex_grid`、`_update_manual_layout_tree`、`rebuild_hex_grid`、`_rebuild_manual_hex_grid`：改為增量更新或 debounce。
     - Treeview/Entry 清空與重建邏輯，改為 diff/patch 或 reuse row widget。
   - 測試：`tests/test_struct_view.py`、`tests/test_struct_view_v3.py` 增加大 struct 操作效能與 refresh 次數統計。

2. **UI/UX 提升**
   - `src/view/struct_view.py`：
     - 新增自動 focus 新增欄位、tab 鍵順序管理。
     - 錯誤欄位高亮、tooltip、即時驗證。
   - 測試：增加 UI 行為驗證（如 focus、tab、錯誤高亮）。

---

### 2024/07 UI/UX 小幅提升執行規劃

- **目標**：
  - 新增欄位時自動 focus 到新欄位名稱輸入框。
  - 編輯表格支援 tab 鍵順序（名稱→型別→bit size→操作）。
  - 欄位驗證錯誤時自動高亮（紅框），並可加 tooltip。
- **TDD 步驟**：
  1. 先於 tests/test_struct_view.py 撰寫/補強對應行為測試（focus、tab、錯誤高亮）。
  2. 再於 src/view/struct_view.py 以最小增量方式實作。
  3. 每步驟皆可獨立 commit，確保可回溯。
- **影響檔案**：
  - src/view/struct_view.py
  - tests/test_struct_view.py
- **驗證指標**：
  - 新增欄位後，名稱欄位自動取得焦點。
  - tab 鍵可依序切換欄位。
  - 欄位驗證錯誤時，該欄位紅框高亮，並可顯示 tooltip。
- **備註**：
  - 不影響主流程，僅提升用戶體驗。
  - 可與其他優化（如效能、observer pattern）獨立進行。

---

### 2024/07 UI/UX 小幅提升實做細節與影響範圍

- **需改動的 code**：
  - `src/view/struct_view.py`
    - `_add_member`：新增欄位後，記錄 index，render table 時 focus 新增的名稱欄位 Entry。
    - `_render_member_row`：每個 row 的 Entry/OptionMenu 需記錄並可設 focus，tab order 依序設置。
    - `_render_member_table`：render 完畢後自動 focus 新增欄位（若有）。
    - `show_manual_struct_validation`：根據錯誤訊息高亮對應欄位（如 Entry.config(highlightbackground='red')），可加 tooltip。
- **需補強/新增的測試**：
  - `tests/test_struct_view.py`
    - `test_add_member_auto_focus`：驗證新增欄位後名稱 Entry 自動取得焦點。
    - `test_tab_order`：驗證 tab 鍵可依序切換欄位。
    - `test_error_highlight`：驗證欄位驗證錯誤時自動紅框高亮。
- **TDD 步驟**：
  1. 先補/寫測試。
  2. 再小步驟實作。
  3. 每步驟皆可獨立 commit。
- **驗證指標**：
  - 新增欄位後，名稱欄位自動取得焦點。
  - tab 鍵可依序切換欄位。
  - 欄位驗證錯誤時，該欄位紅框高亮，並可顯示 tooltip。

---

3. **效能優化（局部）**
   - 針對 `_render_member_table`、`_build_hex_grid` 實作 debounce，先不做 row-level diff。
   - 測試：mock patch presenter/model，統計 refresh 次數。

4. **共用元件/重構（局部）**
   - 先抽出 hex grid 產生邏輯為 helper，file/manual tab 共用。
   - 測試：helper class 單元測試。

5. **效能優化（進階）**
   - 導入 row-level update/diff 機制，僅 patch 變動 row。
   - 測試：大 struct 操作效能明顯提升。

6. **共用元件/重構（進階）**
   - 抽象 member table 為共用 helper/class，進一步減少重複碼。
   - 測試：覆蓋所有分支。

7. **UI observer pattern**
   - StructView 實作 observer 介面，註冊到 Presenter/Model。
   - 測試：多視圖/多 observer 測試。

> 每步驟皆以 TDD 驅動，先設計/補齊對應單元測試與整合測試，確保每次 commit 都可回溯、驗證。 

# 進階 LRU Cache 策略與自動清空規劃

本節補充 v4 GUI 優化的進階 LRU cache 策略與自動清空設計，包含動態容量調整、定時自動清空、整合測試等，確保 cache 行為靈活且可監控。

## 1. 動態 LRU Cache 容量調整
- Presenter 層新增 `set_lru_cache_size(size: int)`，可於執行時動態調整 cache 容量。
- 當容量變小時，會自動淘汰最舊 cache 項目，確保不超過新容量。
- 支援 `get_lru_cache_size()` 查詢目前容量。
- 可由 config、環境變數或 UI 設定 cache 容量。
- **測試規劃**：  
  - 設定容量變小時，cache 自動淘汰。
  - 設定容量變大時，cache 不丟失現有項目。
  - 設定容量為 0 時，cache 不儲存任何項目。
  - 多次動態調整容量，cache 行為正確。

## 2. 定時自動清空 Cache
- Presenter 層新增 `enable_auto_cache_clear(interval_sec: int)`，可定時自動清空 cache。
- 新增 `disable_auto_cache_clear()` 停用自動清空，`is_auto_cache_clear_enabled()` 查詢狀態。
- Timer thread-safe，避免重複啟動或殭屍 timer。
- 可由 UI/Debug tab 控制啟用/停用與顯示狀態。
- **測試規劃**：  


## 移除 MyStruct Tab Debug 欄位

### 1. 需求概述
- 簡化介面，僅在載入 `.h` 檔或 Debug Tab 顯示 Debug Bytes
- MyStruct 頁面不再建立 `manual_debug_text`，視覺上僅留解析按鈕與結果

### 2. 影響檔案
- `src/view/struct_view.py`：移除 `manual_debug_frame`、`manual_debug_text` 與相關方法
- `tests/test_struct_view.py`：刪除或調整所有存取 `manual_debug_text` 的測試
- `tests/README.md` 等文件同步更新描述

### 3. 需調整的程式與測試位置
- `src/view/struct_view.py`
  - 刪除 `_create_manual_debug_frame` 區塊中 `manual_debug_text` 相關程式碼
  - 移除 `show_manual_debug_bytes` 方法與相依呼叫處
  - `_on_parse_manual_hex` 不再呼叫 `show_manual_debug_bytes`
- `tests/test_struct_view.py`
  - 移除 `test_manual_struct_hex_input_and_parse_debug`
  - 移除所有 `manual_debug_text` 存取斷言
  - 新增 `test_manual_struct_no_debug_widget` 驗證 `StructView` 不含 `manual_debug_text`

### 4. TDD 流程
1. **修改測試**：
   - 移除 `test_manual_struct_hex_input_and_parse_debug` 等驗證 Debug Bytes 的斷言
   - 新增 `test_manual_struct_no_debug_widget` 確認 `StructView` 未建立 `manual_debug_text`
2. **調整程式碼**：
   - 刪除建立 Debug Bytes 區塊的 UI 代碼
   - 移除 `show_manual_debug_bytes` 及 `_on_parse_manual_hex` 內對此欄位的使用
   - 版面改回單欄顯示，必要時更新 grid 計算
3. **回歸測試**：
   - 執行 `run_all_tests.py` 確認所有測試通過
   - 手動檢查 Debug Tab 仍能顯示 debug bytes

### 5. 提交順序
1. 調整/新增測試
2. 更新 `StructView` 程式碼
3. 更新相關文件
