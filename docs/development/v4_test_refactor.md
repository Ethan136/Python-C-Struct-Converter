# v4 測試程式碼重構計畫

## 1. 目標
- **擴大自動化測試覆蓋**：將更多 hardcode 的資料驅動測試案例，遷移到 XML 設定檔中。
- **提升測試程式碼的可維護性**：讓測試案例更容易新增、修改與管理。

## 2. 擴大 XML 驅動測試

### 2.1. 優先處理 `test_input_field_processor.py`
- **背景**：此檔案的測試案例最單純，幾乎都是純粹的「輸入-輸出」對應，是 XML 化的最佳起點。
- **計畫 (TDD)**：
    1.  **建立新測試類**：在 `test_input_field_processor.py` 中建立一個新的測試類 `TestInputFieldProcessorXML`,並標記為使用 `unittest.skip` 暫時跳過。
    2.  **擴充 XML**：在 `tests/data/test_input_field_processor_config.xml` 中，新增一個測試案例，對應一個目前在 `TestInputFieldProcessor` 中的 hardcode 測試。
    3.  **修改 Loader**：擴充 `xml_input_field_processor_loader.py`，使其能解析新的測試案例格式。
    4.  **實作新測試**：在 `TestInputFieldProcessorXML` 中，撰寫一個測試方法，使用 loader 載入新的 XML 案例並執行斷言。
    5.  **執行與驗證**：執行測試，確認新的 XML 測試案例通過。
    6.  **移除舊測試**：刪除 `TestInputFieldProcessor` 中對應的 hardcode 測試。
    7.  **重複**：逐步將其他適合的 hardcode 測試案例，重複以上步驟，遷移到 XML 中。

### 2.2. 逐步遷移 `test_struct_model.py`
- **背景**：`test_struct_model.py` 和 `test_struct_model_integration.py` 中，也存在大量適合資料驅動的測試案例。
- **計畫 (TDD)**：
    1.  **識別目標**：從 `test_struct_model.py` 中，挑選一個純資料驗證的測試方法，例如 `test_parse_hex_data_bitfields`。
    2.  **建立新測試類**：建立一個新的測試類 `TestStructModelXML`，並暫時跳過。
    3.  **擴充 XML**：在 `tests/data/test_struct_model_config.xml` 中，新增對應的測試案例，包含 struct 定義、hex 輸入和預期結
    4.  **修改 Loader**：擴充 `xml_struct_model_loader.py` 以支援新的測試案例格式。
    5.  **實作與驗證**：撰寫新的測試方法，載入 XML 並執行斷言，確保測試通過。
    6.  **移除舊測試**：刪除 `test_struct_model.py` 中對應的 hardcode 測試。
    7.  **重複**：逐步遷移其他適合的測試案例。

## 3. 維持 Hardcode 的測試

- **原則**：對於測試「行為」、「例外處理」和「UI 互動」的案例，繼續維持 hardcode 的方式，因為這類測試難以用純資料描述，硬要 XML 化反而會降低可讀性。
- **範例**：
    - `test_load_struct_from_file_invalid` (例外處理)
    - `test_is_supported_field_size` (API 邊界)
    - `test_struct_view.py` 中的 UI 事件觸發測試 (GUI 行為)

## 4. 進度紀錄

- `test_input_field_processor.py` 已全面使用 `test_input_field_processor_config.xml`，其中 `pad_hex_input` 與 `convert_to_raw_bytes` 測試皆改為 XML 驅動。
- `test_struct_model_integration.py` 的多數案例現已由 `test_struct_model_integration_config.xml` 載入。
- `test_struct_model.py` 大多數解析、layout 與複雜範例測試皆改以 XML 描述，配置檔為 `test_struct_model_config.xml`。
- 仍維持 hardcode 的僅剩行為與例外處理相關測試，例如上列三項。
