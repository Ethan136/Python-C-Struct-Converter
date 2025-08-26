## v14 開發計畫：GUI 支援 32-bit / 64-bit 模式切換（Pointer 4/8 bytes）

### 實作架構概覽
1. **改哪些地方**
   - `src/model/types.py`：新增 `set_pointer_mode/get_pointer_mode/reset_pointer_mode` 以允許指標大小於執行期切換。
   - `src/presenter/struct_presenter.py`：在 context 增加 `arch_mode` 並實作 `on_pointer_mode_toggle()` 觸發切換與 cache 失效。
   - `src/view/struct_view.py`：File 與 Manual 兩個 tab 加入「32-bit 模式」勾選框並綁定事件。
   - `docs/`、`tests/`：補充對應文件與測試案例。
2. **32-bit 開關如何影響內部機制**
   - `set_pointer_mode(32)` 透過覆蓋 `CUSTOM_TYPE_INFO["pointer"]` 讓 `get_type_info()` 回傳 4-byte `size/align`，佈局計算自動套用。
   - Presenter 呼叫切換後會清空 layout LRU cache 並重新推送 context。
3. **開啟 32-bit 開關後預期影響**
   - 任一包含 `pointer` 的結構其 offset/size 以 4-byte 對齊重新計算，總大小可能變小。
   - GUI 重新渲染佈局表與解析結果，Hex grid 切分邏輯維持不變。
   - 文件與測試需覆蓋兩種模式，確保行為一致。
4. **改動順序（內 → 外）**
   - 先實作 `types.py` 及模型層單元測試。
   - 驗證佈局計算與相關測試資料。
   - 加入 Presenter 邏輯。
   - 最後整合 View 與更新文件/測試。

### 目標
- 在 GUI 提供「32-bit 模式」勾選框（預設不勾選=64-bit），即時影響記憶體佈局與解析。
- 主要差異點：`pointer` 型別在 32-bit 時為 4 bytes（align 4），在 64-bit 時為 8 bytes（align 8）。
- 預設維持 64-bit（與現行行為相容）。

### 使用者故事
- 作為使用者，我可以在 GUI 切換 32-bit/64-bit 模式：
  - 切換後，`pointer` 欄位的 `size/align` 立刻變更為 4 或 8。
  - 佈局表（offset/size/bit_*）同步更新，總大小與 padding 亦正確反映。
  - Hex 輸入格數與每格寬度維持由總大小與使用者選的單位（1/4/8 Bytes）決定；位元模式只影響型別大小與對齊，不直接影響單位選擇。

### 影響範圍
- 型別與對齊：`src/model/types.py`
  - 現狀：`BASE_TYPE_INFO["pointer"] = {"size": 8, "align": 8}`。
  - 需求：允許於執行期切換 `pointer` 的 `size/align` 為 4/4 或 8/8。
- 佈局計算：`src/model/layout.py`
  - 佈局透過 `get_type_info()` 取得型別資訊，切換後會自動生效（無需直接修改佈局邏輯）。
- Presenter：`src/presenter/struct_presenter.py`
  - 在 context 新增 `arch_mode`（或 `pointer_mode`）並提供事件處理 `on_pointer_mode_change()`。
  - 切換時更新型別註冊器的 `pointer` 設定、清空 layout LRU cache、要求 View 重繪。
- View：`src/view/struct_view.py`
  - 在 File tab 與 Manual tab 的控制列新增「位元模式」下拉選單（32-bit/64-bit）。
  - 綁定事件呼叫 Presenter 切換模式，並觸發 layout/畫面更新。
- 文件與測試資料：`docs/`、`tests/`
  - 新增與更新範例與測試，確保兩種模式下的指標大小/對齊與佈局正確。

### 設計方案

#### 1) 型別註冊器（types.py）
- 新增公開 API 用於切換與查詢指標大小：

```python
# src/model/types.py（示意）
POINTER_BITS = 64  # default

def set_pointer_mode(bits: int) -> None:
    global POINTER_BITS
    size = 4 if bits == 32 else 8
    POINTER_BITS = 32 if bits == 32 else 64
    CUSTOM_TYPE_INFO["pointer"] = {"size": size, "align": size}

def get_pointer_mode() -> int:
    return POINTER_BITS

def reset_pointer_mode() -> None:
    # 測試用：還原為預設 64-bit
    set_pointer_mode(64)
```

- 實作重點：
  - 以 `CUSTOM_TYPE_INFO` 覆蓋 `BASE_TYPE_INFO`，讓既有 `get_type_info()` 流程無縫承接。
  - 對齊值目前與大小相同（4 對齊或 8 對齊），如未來需要可獨立配置。

#### 2) Presenter（struct_presenter.py）
- Context 內新增狀態：`arch_mode: "x64" | "x86"`（預設 `"x64"`）。
- 新增事件處理：

```python
# src/presenter/struct_presenter.py（示意）
from src.model.types import set_pointer_mode

@event_handler("on_pointer_mode_toggle")
def on_pointer_mode_toggle(self, enable_32bit: bool):
    mode = "x86" if enable_32bit else "x64"
    self.context["arch_mode"] = mode
    set_pointer_mode(32 if enable_32bit else 64)
    self.invalidate_cache()
    # 重新計算/推送畫面
    self.push_context()
```

- 切換模式後：
  - 既有 `compute_member_layout()` 與 `calculate_manual_layout()` 會基於新的 `pointer` 大小重算。
  - File tab 若已載入檔案，維持目前 struct，直接以新模式重新顯示 layout。

#### 3) View（struct_view.py）
- File tab 與 Manual tab 的控制列新增一個勾選框：
  - 標籤：`32-bit 模式`（預設未勾=64-bit）。
  - on-change 時呼叫 `presenter.on_pointer_mode_toggle(checked)`。
- 切換後：
  - 不變動「單位大小（1/4/8 Bytes）」選單，單位僅影響 Hex grid 的輸入切分；
  - 重新載入/刷新 layout 與解析相關顯示（沿用既有 `update_display` 與樹狀表格刷新流程）。

#### 4) 初始化與環境變數（可選）
- 預設 `64-bit`，與現有行為相容（`BASE_TYPE_INFO["pointer"] == 8`）。
- 可選：支援環境變數或 CLI 參數覆蓋預設，例如：
  - `STRUCT_POINTER_MODE=32` 啟動時套用 `set_pointer_mode(32)`。

### 使用方式
- GUI：在 File 與 Manual 兩個 tab 的控制列新增「32-bit 模式」勾選框，預設未勾（64-bit）。
  - 勾選後，Presenter 會呼叫 `on_pointer_mode_toggle(True)`，即時清除 layout cache 並重新推送畫面。
  - 取消勾選回到 64-bit 模式。
- 程式啟動時（可選）：設定環境變數 `STRUCT_POINTER_MODE=32` 可於初始化時套用 32-bit 模式。
  - 目前預設仍為 64-bit；如需常駐 32-bit，可在進程啟動後於初始化流程呼叫 `set_pointer_mode(32)`。

### 測試計畫
- 單元測試（新增/調整）：
  - `tests/model/test_type_registry.py` 或整合到現有 `test_type_registry.py`/`test_struct_model.py`：
    - 驗證 `set_pointer_mode(32/64)` 對 `get_type_info("pointer")` 之 `size/align` 輸出。
    - 切換模式前後，佈局中 `pointer` 欄位的 `size/offset` 與末端 padding 變化。
  - 資料驅動 XML（位於 `tests/data/`）：
    - 新增 32-bit 佈局案例，檢查 `pointer` 為 4 bytes 對齊，與 64-bit 為 8 bytes 對比。
  - Presenter/View 行為測試：
    - 觸發 `on_pointer_mode_change()` 後，LRU cache 被清空、`update_display` 被呼叫、layout 重新計算。
  - 依據偏好，測試用 .h 檔放在 `tests/` 目錄下而非 `examples/`。

### TDD 實作流程
1. **模型層測試先行**
   - 在 `tests/model/test_type_registry.py` 撰寫針對 `set_pointer_mode()` 的失敗測試，預期 32-bit 時 `pointer` 為 4 bytes、64-bit 為 8 bytes。
   - 執行測試確認失敗後，實作 `set_pointer_mode/get_pointer_mode/reset_pointer_mode` 使測試轉綠。
   - 測試範例：
     ```python
     def test_pointer_mode_switch():
         set_pointer_mode(32)
         info = get_type_info("pointer")
         assert (info.size, info.align) == (4, 4)
         reset_pointer_mode()
     ```
2. **佈局計算驗證**
   - 撰寫包含 `pointer` 欄位的結構範例，先寫測試檔驗證在不同模式下佈局結果（offset/size/padding）。
   - 實作或調整相關程式碼，再次跑測試確保佈局因模式切換而改變。
   - 例如：
     - `struct Sample { char c; void* p; };`
     - 64-bit：`c` offset 0、`p` offset 8、總大小 16。
     - 32-bit：`c` offset 0、`p` offset 4、總大小 8。
3. **Presenter/View 行為**
   - 為 `on_pointer_mode_change()` 與 View 勾選框撰寫行為測試，模擬使用者切換模式並期待 LRU cache 清空與畫面更新。
   - 先看測試失敗，再補上 Presenter 與 View 的實作直到測試通過。
   - 測試可使用 `MagicMock` 檢查：
     ```python
     presenter.invalidate_cache = MagicMock()
     presenter.push_context = MagicMock()
     presenter.on_pointer_mode_toggle(True)
     presenter.invalidate_cache.assert_called_once()
     presenter.push_context.assert_called_once()
     ```
4. **重構與迭代**
   - 在所有測試綠燈的前提下進行程式碼重構，確保資料流清晰且 `reset_pointer_mode()` 能在測試後恢復狀態。
   - 每次重構都重新執行測試，以維持行為一致。

### 相容性
- 預設 64-bit，維持所有既有測試通過。
- 僅在使用者切換為 32-bit 時，`pointer` 相關佈局才改為 4 bytes。
- 其他型別（`int/long long/...`）不受此功能影響。

### 風險與注意事項
- `types.py` 以全域覆蓋 `CUSTOM_TYPE_INFO["pointer"]` 的方式提供動態切換：
  - 測試需在 `setUp/tearDown` 或個別測試結尾呼叫 `reset_pointer_mode()`，避免交互污染。
  - 如果未來支援多筆文件同時以不同模式顯示，需改為將模式作為佈局計算參數傳遞，而非全域狀態（本版先不支援）。
- 切換模式後記得清空 Presenter 的 layout LRU cache，避免用到舊結果。

### 驗收標準（Acceptance Criteria）
- GUI 出現「32-bit 模式」勾選框，預設未勾（64-bit）。
- 勾選時，`pointer` 欄位 `size/align` 改為 4/4；取消勾選改為 8/8。
- 切換後佈局（offset/size/final padding）正確、解析可用，且不拋出例外。
- 既有測試維持綠燈；新增測試覆蓋兩種模式下的 `pointer` 大小與對齊。

### 任務拆解（WBS）
- 模型層：在 `src/model/types.py` 實作 `set_pointer_mode/get_pointer_mode/reset_pointer_mode`。
- Presenter：加入 `arch_mode` 狀態與 `on_pointer_mode_change()`；切換時清空 cache 並刷新畫面。
- View：兩個 tab 都加入「32-bit 模式」勾選框與事件綁定。
- 文件：更新 `docs/architecture/MANUAL_STRUCT_ALIGNMENT.md` 註記 pointer 在 32-bit 的對齊與大小差異。
- 測試：
  - 新增 32-bit 佈局案例（XML 與單元測試）。
  - Presenter 行為與 cache 失效測試。
  - 測試結束恢復 64-bit 以避免污染其他測試。



### 額外建議與修正項目（落地與一致性）

- Union 佈局對齊集中 registry（避免靜態快照）
  - 現狀：`src/model/layout.py` 的 `UnionLayoutCalculator._get_type_size_and_align` 使用模組載入時的 `TYPE_INFO` 靜態快照，可能無法反映執行期指標大小切換。
  - 建議：改為呼叫 `get_type_info(mtype)` 以統一走集中 registry，確保 32/64-bit 變更即時生效。
  - 參考修改：
    ```python
    # before
    def _get_type_size_and_align(self, mtype: str) -> Tuple[int, int]:
        info = TYPE_INFO[mtype]
        return info["size"], info["align"]

    # after
    from .types import get_type_info  # ensure imported at top
    def _get_type_size_and_align(self, mtype: str) -> Tuple[int, int]:
        info = get_type_info(mtype)
        return info["size"], info["align"]
    ```

- View 勾選框狀態與 context 同步
  - 現狀：已提供 File/Manual 兩處「32-bit 模式」勾選框，但 `update_display(...)` 尚未依 `context["arch_mode"]` 同步 `file_pointer32_var` 與 `manual_pointer32_var`，初始化或外部切換後 UI 可能與實際模式不同步。
  - 建議：在 `update_display` 結尾處根據 `context.get("arch_mode") == "x86"` 設置兩個 `BooleanVar`，避免 UI 失真。

- 啟動時環境變數/CLI（可選）
  - 文檔建議的 `STRUCT_POINTER_MODE=32` 目前未實作，可在 `src/model/types.py` 於 `_bootstrap_from_config()` 之後讀取環境變數並呼叫 `set_pointer_mode(32)`。
  - 保持預設 64-bit，相容既有行為。

- 文檔補強：`MANUAL_STRUCT_ALIGNMENT.md`
  - 文中提到需更新 `docs/architecture/MANUAL_STRUCT_ALIGNMENT.md`，目前檔案尚未提供。建議新增此文件，明確列出 32/64-bit 下 `pointer` 的 size/align 差異與示例（含 offset/final padding 對照表）。

- 文案與 UI 形式微差
  - 設計文使用「位元模式下拉選單」，目前 UI 以單一「32-bit 模式」勾選框呈現；兩者功能等效。建議文件註記實作以勾選框為準（或同時接受兩種等效呈現），不影響驗收標準。

#### 建議實作順序（針對本節）

1. Union 佈局改用集中 registry
   - 調整 `src/model/layout.py` 的 `UnionLayoutCalculator._get_type_size_and_align`，由 `TYPE_INFO` 改為 `get_type_info(mtype)`。
   - 新增/調整單元測試：包含 `union { char c; void* p; }` 或 struct 中含 union 的案例，驗證 64-bit 與 32-bit 下 `pointer` 尺寸與對齊變化會反映在 union 佈局。
2. View 勾選框與 context 同步
   - 在 `src/view/struct_view.py` 的 `update_display(nodes, context, ...)` 結尾，依 `context.get("arch_mode") == "x86"` 同步 `file_pointer32_var` 與 `manual_pointer32_var`。
   - 新增 Presenter/View 行為測試：模擬 `arch_mode` 改變後呼叫 `update_display`，兩個 `BooleanVar` 狀態正確更新。
3. 啟動時環境變數（可選）
   - 在 `src/model/types.py` 的初始化流程（`_bootstrap_from_config()` 之後）讀取 `STRUCT_POINTER_MODE`，如為 `"32"` 則呼叫 `set_pointer_mode(32)`。
   - 新增測試：設定環境變數後載入模組或呼叫初始化鉤子，驗證 `get_type_info('pointer')` 為 4/4；測試結尾 `reset_pointer_mode()` 復原。
4. 文件補強與連結
   - 新增 `docs/architecture/MANUAL_STRUCT_ALIGNMENT.md`，說明 32/64-bit 下 `pointer` 的 size/align 與 offset/final padding 例子，並自本文件與相關 README 連回。
5. 文面一致性註記
   - 於本文件與 `src/view/README.md` 註明實作以「勾選框」呈現，與「下拉選單」表述功能等效；無需程式碼更動。
6. 回歸測試與驗收
   - 執行全測，確保既有測試綠燈；新增的 union、view 同步、（可選）環境變數測試皆通過。
   - 依「驗收標準」再次檢查 GUI 勾選、佈局更新與 cache 失效是否符合預期。
