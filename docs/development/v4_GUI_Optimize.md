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

---

> 本文件持續補充具體改動細節與測試腳本，歡迎貢獻更多自動化測試與效能數據。 