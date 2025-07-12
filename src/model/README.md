# Model Layer 說明文件

本目錄包含 C++ Struct 解析工具的 Model 層，負責核心業務邏輯與資料處理。

## 檔案說明

### struct_model.py
- **用途**：
  - 提供 StructModel 類別，負責解析 C++ struct 定義、計算記憶體佈局、解析十六進制資料。
- **執行機制**：
  - 透過 `parse_struct_definition` 解析 struct 檔案內容，取得成員與型態。
  - 使用 `calculate_layout` 計算每個成員的 offset、size、alignment，並處理 padding。
  - `parse_hex_data` 會根據 struct 佈局與使用者指定的位元組順序，將 hex 字串轉換為結構化資料。
- **與其他模組關聯**：
  - 由 Presenter 呼叫，回傳 struct 解析結果給 View 顯示。
  - 依賴 input_field_processor.py 處理欄位輸入。

### input_field_processor.py
- **用途**：
  - 提供 InputFieldProcessor 類別，負責欄位輸入的自動補零、位元組序轉換、產生原始 bytes。
- **執行機制**：
  - `pad_hex_input` 會自動將 hex 字串左補零至指定長度。
  - `process_input_field` 結合補零與 bytes 轉換，支援 little/big endian。
- **與其他模組關聯**：
  - 被 struct_model.py 與 presenter/struct_presenter.py 呼叫，用於欄位輸入驗證與轉換。

## 相關設計文檔
- [結構解析機制說明](../../docs/architecture/STRUCT_PARSING.md)
- [欄位輸入處理分析](../../docs/analysis/input_field_processor_analysis.md) 