# Model Layer 說明文件

> **2024/07 補充：手動 struct（MyStruct）現在會自動依 C++ 標準 struct align/padding 機制產生記憶體佈局。所有成員型別會自動推斷（byte/bit 欄位自動對應 char/short/int/long long/bitfield），並自動補齊必要的 padding，結構體結尾也會補齊 align。這讓手動 struct 的記憶體佈局與 C++ 編譯器產生的結果完全一致。**

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

## Struct 成員資訊的資料結構

StructModel 解析 struct 後，會將每個成員（含 padding）資訊儲存於一個「dict 組成的 list」中，並存放於 `self.layout` 屬性。

每個 dict 代表一個 struct 成員或 padding，包含下列欄位：
- `name`：成員名稱（或 "(padding)"）
- `type`：型態名稱（如 char、int、long long、padding 等）
- `size`：所佔位元組數
- `offset`：在 struct 記憶體區塊中的起始位移

例如：
```python
[
    {"name": "status", "type": "char", "size": 1, "offset": 0},
    {"name": "(padding)", "type": "padding", "size": 7, "offset": 1},
    {"name": "user_id", "type": "long long", "size": 8, "offset": 8}
]
```

### 設計理念
- **可讀性**：以 dict 儲存欄位名稱，易於維護與理解
- **完整性**：每個成員的型態、大小、位移皆明確記錄，方便後續操作
- **精確對應記憶體**：padding 也明確標示，確保記憶體佈局正確
- **擴充性**：未來如需新增屬性，只需於 dict 增加欄位即可

詳細說明請參見 [結構解析機制說明](../../docs/architecture/STRUCT_PARSING.md) 的「Final Data Structure Details」段落。 

### 為什麼 struct member info 沒有「數值」欄位？

- `self.layout`（list of dict）只負責描述 struct 的「靜態結構」與「記憶體配置」，不包含任何成員的實際數值。
- 這樣設計可分離「結構描述」與「資料內容」，讓同一份 layout 可重複用於不同資料解析。
- struct member 的「數值」是根據 hex 輸入、endianness 等動態解析出來的，屬於資料處理的結果，不應混入 layout 結構。
- 當需要 struct member 的數值時，請呼叫 `StructModel.parse_hex_data(hex_data, byte_order)`，它會根據 layout 解析 hex 資料，回傳包含 name、value、hex_raw 等欄位的 list。

例如：
```python
[
    {"name": "user_id", "value": 123456, "hex_raw": "0001e240"},
    ...
]
```

這樣可確保結構與資料分離、重用性高、維護容易。 