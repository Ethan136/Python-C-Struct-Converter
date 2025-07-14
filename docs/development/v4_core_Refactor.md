# v4 核心程式碼重構計畫

## 1. 目標
- **提升程式碼品質**：簡化複雜函式、移除重複程式碼，並強化 MVP 架構的職責分離。
- **提高可維護性**：讓程式碼結構更清晰，未來更容易擴充與修改。

## 2. `StructView` 程式碼整理 (`src/view/struct_view.py`)

### 2.1. 合併重複的 hex grid 建立邏輯
- **問題**：`rebuild_hex_grid` 和 `_rebuild_manual_hex_grid` 方法的程式碼幾乎完全相同。
- **計畫**：
    1.  建立一個新的私有方法 `_build_hex_grid(frame, entry_list, total_size, unit_size)`，將共用邏輯封裝進去。
    2.  修改 `rebuild_hex_grid` 和 `_rebuild_manual_hex_grid`，讓它們只負責準備參數並呼叫 `_build_hex_grid`。

### 2.2. 移除 View 中的業務邏輯
- **問題**：View 層包含了一些應屬於 Presenter 的資料處理邏輯，違反了 MVP 職責分離原則。
- **計畫**：
    1.  將 `_compute_member_layout` 方法的邏輯移至 `StructPresenter`。Presenter 計算完後，再將結果傳給 View 顯示。
    2.  將 `show_manual_struct_validation` 中計算剩餘空間的邏輯移至 `StructPresenter`。

## 3. `StructModel` 簡化 (`src/model/struct_model.py`)

### 3.1. 統一 Struct 的內部表示法
- **問題**：從檔案載入的 struct 和手動定義的 struct 在 Model 中有不同的處理流程與資料結構，導致 `parse_manual_hex_data` 等方法變得複雜且多餘。
- **計畫**：
    1.  設計一個統一的內部資料結構來表示 struct 成員，無論其來源為何。
    2.  重構 `set_manual_struct` 和 `load_struct_from_file`，讓它們都產生這個統一的資料結構。
    3.  移除 `parse_manual_hex_data`，讓 `parse_hex_data` 可以處理所有情況。

### 3.2. 拆分複雜的驗證邏輯
- **問題**：`validate_manual_struct` 函式過於龐大，單一函式負責了多種驗證（型別、名稱、大小等），難以閱讀和測試。
- **計畫**：
    1.  將 `validate_manual_struct` 拆分為數個更小的函式，每個函式只負責一種類型的驗證，例如：
        - `_validate_member_types`
        - `_validate_member_names`
        - `_validate_total_size`
    2.  `validate_manual_struct` 負責依序呼叫這些小函式並彙總錯誤。

## 4. `struct_parser.py` 清理

### 4.1. 合併重複的解析函式
- **問題**：檔案中存在多個版本的解析函式，如 `parse_member_line`、`parse_member_line_v2`，以及 `parse_struct_definition`、`parse_struct_definition_v2`，功能重疊且命名混亂。
- **計畫**：
    1.  分析各版本函式的功能，整併為一組核心 API。
    2.  將舊函式標記為棄用 (deprecated)，並更新所有呼叫點，使其統一使用新的 API。