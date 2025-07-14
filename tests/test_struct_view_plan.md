# StructView 測試計畫

## 1. 測試目標

本計畫旨在為 `src/view/struct_view.py` 中的 `StructView` 類別提供一個全面的自動化測試方案。由於 `StructView` 是 MVP 架構中的被動視圖 (Passive View)，測試將主要集中在以下三個方面：

1.  **UI 元件的正確初始化**：驗證視圖的所有視覺元件（如文字方塊、按鈕、標籤）是否都已成功創建並設定初始狀態。
2.  **使用者操作的正確傳遞**：確保使用者在 UI 上的操作（例如，點擊「轉換」按鈕）能夠觸發對 Presenter 對應方法的呼叫。
3.  **資料顯示的正確性**：驗證從 Presenter 傳遞過來的資料（例如，轉換後的 Python 程式碼或錯誤訊息）能否被正確地顯示在 UI 元件上。

## 2. 測試策略

為了將 View 與 Presenter 和 Model 的邏輯解耦，我們將採用 **Mocking (模擬)** 的策略。

-   **模擬 Presenter**：在測試過程中，我們將使用 `unittest.mock.Mock` 來取代真實的 `StructPresenter` 物件。這使我們能夠：
    -   在不依賴 Presenter 實際邏輯的情況下，獨立測試 View。
    -   驗證 View 是否在正確的時機、以正確的參數呼叫了 Presenter 的方法。
-   **UI 互動模擬**：我們將直接呼叫 `StructView` 中與 UI 事件綁定的方法（例如 `_on_convert_button_click`），以模擬使用者的操作，而不是試圖用自動化工具去點擊實際的 GUI 按鈕。

## 3. 測試案例

### 3.1. UI 元件初始化測試

-   **`test_view_initialization`**:
    -   **目的**: 驗證 `StructView` 初始化後，所有的 UI 元件都已創建。
    -   **步驟**:
        1.  初始化 `StructView`。
        2.  斷言（Assert）各個 UI 元件（`input_text`, `output_text`, `convert_button` 等）不是 `None`。

### 3.2. 使用者輸入與操作測試

-   **`test_get_input_text`**:
    -   **目的**: 驗證 `get_input_text` 方法能正確地從輸入文字方塊中獲取 C 結構體程式碼。
    -   **步驟**:
        1.  初始化 `StructView`。
        2.  在 `input_text` 元件中插入測試用的 C 結構體字串。
        3.  呼叫 `get_input_text()` 方法。
        4.  斷言返回的字串與我們插入的字串相符。

-   **`test_convert_button_click_triggers_presenter`**:
    -   **目的**: 驗證點擊「轉換」按鈕會觸發對 Presenter `convert_struct` 方法的呼叫。
    -   **步驟**:
        1.  初始化 `StructView`，並傳入一個 Mock Presenter。
        2.  呼叫與按鈕點擊事件綁定的 `_on_convert_button_click` 方法。
        3.  斷言 Mock Presenter 的 `convert_struct` 方法被呼叫了一次。

### 3.3. 資料顯示測試

-   **`test_set_output_text`**:
    -   **目的**: 驗證 `set_output_text` 方法能將指定的文字內容設定到輸出文字方塊中。
    -   **步驟**:
        1.  初始化 `StructView`。
        2.  定義一個測試字串（例如，"class MyStruct:"）。
        3.  呼叫 `set_output_text` 方法並傳入該字串。
        4.  斷言 `output_text` 元件的內容與傳入的字串相符。

-   **`test_show_error_message`**:
    -   **目的**: 驗證 `show_error_message` 方法能正確地顯示錯誤訊息。
    -   **步驟**:
        1.  初始化 `StructView`。
        2.  定義一個錯誤訊息字串。
        3.  （可選）模擬 `messagebox.showerror` 函式，以驗證它是否被正確呼叫。
        4.  呼叫 `show_error_message` 方法。
        5.  斷言 `messagebox.showerror` 被以正確的參數呼叫。

### 3.4. GUI 細節一致性與同步測試

-   **`test_treeview_column_consistency`**:
    -   **目的**: 驗證 MyStruct 與 .H tab 的 Treeview 欄位、欄位寬度、標題完全一致。
-   **`test_scrollbar_presence`**:
    -   **目的**: 驗證兩個 tab 主框架皆有右側 scrollbar。
-   **`test_bitfield_and_padding_display`**:
    -   **目的**: 驗證 bitfield 與 padding 欄位於 Treeview 內正確顯示。
-   **`test_debug_bytes_format_consistency`**:
    -   **目的**: 驗證 debug bytes 格式於兩個 tab 完全一致。
-   **`test_tab_switch_sync`**:
    -   **目的**: 驗證 tab 切換時，Treeview、hex grid、欄位驗證等 GUI 行為即時同步。
-   **`test_field_validation_realtime`**:
    -   **目的**: 驗證欄位驗證（長度、合法字元）於輸入時即時顯示。

## 4. 測試環境

-   **框架**: `unittest`
-   **輔助工具**: `unittest.mock`
-   **執行方式**: 測試將在 CI/CD 流程中自動執行，無需實際渲染 GUI。
