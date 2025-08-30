### v19 TDD 開發文件：匯入 .H 解析結果輸出為 CSV

本文件規劃 v19 新增功能：「將既有匯入 .H 後的解析結果輸出成 CSV」。採 TDD 驅動，優先定義驗收與測試，並精確列出需實作的功能點、資料流、介面、測試套件與 TestXml 規格，供後續完全依此施工。

---

## 1. 範圍與目標
- **目標**：在既有的 .H 解析流程完成後，新增 CSV 匯出器，將解析後的結構化資料以 CSV 檔輸出。
- **範圍**：新增 CSV 匯出模組、公開介面、命令列/服務層入口，以及對應單元測試、整合測試、TestXml 驅動的端對端測試。
- **不變更**：現有 .H 解析器語意與輸出資料模型不變（如有缺欄位，於本功能新增安全映射與預設）。

---

## 2. 名詞定義
- **.H**：已存在之匯入檔案，經解析器輸出為結構化資料（欄位清單等）。
- **解析結果（Parsed Model）**：下述「解析資料模型」中定義之結構。
- **CSV**：逗號分隔值格式，支援自訂分隔符、引號、BOM、換行符等。

---

## 3. 版本與相容性
- **版本**：v19 新增。
- **相容性**：預設不改變既有流程。若未設定輸出 CSV，系統行為與 v18 相同。
- **設定鍵名與 CLI**：新增不破壞既有，向後相容。

---

## 4. 解析資料模型（既有輸出，供 CSV 映射）
為了精確定義 CSV 欄位映射，本功能假設解析器輸出至少包含：

```ts
type ParsedField = {
  entityName: string            // 所屬實體/結構名稱（若無則用空字串）
  fieldOrder: number           // 欄位序（從 1 起）
  fieldName: string            // 欄位名稱
  physicalName?: string        // 實體物理名稱（可無）
  dataType: string             // 資料型別（如 CHAR, VARCHAR, NUMERIC…）
  length?: number              // 長度（若適用）
  precision?: number           // 精度（若適用）
  scale?: number               // 小數位數（若適用）
  nullable: boolean            // 是否可為空
  defaultValue?: string        // 預設值
  comment?: string             // 註解
  sourceFile: string           // 來源檔名
  sourceLine: number           // 來源行號（若不可得則填 0）
  tags?: string[]              // 額外標籤（可無）
}
type ParsedModel = {
  fields: ParsedField[]         // 全部欄位（跨多實體亦可）
  metadata?: Record<string,string> // 全域中繼資料（可無）
}
```

若實際模型不同，須以「安全映射」策略處理（見 7.4）。

---

## 5. CSV 規格與輸出格式
- **預設分隔符**：`,`（可自訂 `;`、Tab 等）
- **預設引號字元**：`"`（遇到分隔符、引號、換行、首尾空白則加引號，內部 `"` 以 `""` 轉義）
- **標頭列**：預設輸出，欄位順序如下：
  1. entity_name
  2. field_order
  3. field_name
  4. physical_name
  5. data_type
  6. length
  7. precision
  8. scale
  9. nullable
  10. default
  11. comment
  12. source_file
  13. source_line
  14. tags
- **編碼**：預設 UTF-8（BOM 預設 false，可開關）
- **換行**：預設 `\n`（可自訂 `\r\n`）
- **空值呈現**：預設輸出空字串（可改 `NULL`）
- **欄位排序**：預設依 `entity_name ASC, field_order ASC`（可設定排序鍵）
- **欄位挑選與重排**：可由選項設定輸出欄位子集合與順序

---

## 6. 公開介面（Service 與 API）
服務層匯出介面：

```ts
// 同步或串流式實作皆可，推薦串流
interface CsvExportService {
  exportToCsv(
    parsedModel: ParsedModel,
    output: OutputTarget,        // 檔案路徑或 Writable Stream
    options?: CsvExportOptions
  ): ExportReport               // 回傳輸出統計與摘要
}

type OutputTarget =
  | { type: 'file', path: string }
  | { type: 'stream', stream: Writable }

type CsvExportOptions = {
  delimiter?: string             // 預設 ","
  quoteChar?: string             // 預設 """
  includeHeader?: boolean        // 預設 true
  encoding?: 'UTF-8' | 'UTF-8-BOM' | 'MS950' | 'CP932' | string  // 預設 UTF-8
  lineEnding?: '\n' | '\r\n'     // 預設 '\n'
  nullStrategy?: 'empty' | 'NULL'| 'dash'                         // 預設 'empty'
  decimalSeparator?: '.' | ','   // 僅影響數值序列化（若有）
  includeBom?: boolean           // 預設 false
  columns?: string[]             // 欲輸出欄位清單（預設第 5 節順序）
  sortBy?: Array<{ key: string, order: 'ASC'|'DESC' }> // 預設 entity_name, field_order
  safeCast?: boolean             // 預設 true：不破例，使用安全映射
}

type ExportReport = {
  recordsWritten: number
  headerWritten: boolean
  filePath?: string              // 當 target 為 file 時回填
  durationMs: number
  warnings: string[]
}

class CsvExportError extends Error {
  code: 'IO_ERROR' | 'ENCODING_ERROR' | 'INVALID_OPTIONS' | 'EMPTY_MODEL'
  details?: any
}
```

命令列/外部入口（可選）：

```
--export-csv <path> \
  [--delimiter , --no-header --encoding UTF-8 --bom \
   --line-ending CRLF --null NULL \
   --columns "field_name,data_type" \
   --sort "entity_name:ASC,field_order:ASC"]
```

---

## 7. 邏輯規則
- **7.1 欄位序列化**：
  - 布林：`true|false`。
  - 數值：保留精度與 scale；若 `decimalSeparator=','` 則小數點切換。
  - 陣列 `tags`：以 `|` 連接（內含 `|` 以 `\|` 轉義）。
- **7.2 引號與轉義**：
  - 若值含分隔符、引號、換行、首尾空白，即加引號；值內 `"` → `""`。
- **7.3 空值策略**：
  - `empty` → 空字串；`NULL` → 字面 `NULL`；`dash` → `-`。
- **7.4 安全映射（safeCast=true）**：
  - 遺漏欄位以空策略輸出；未知型別以文字原樣輸出；負序/非法長度歸零並加 warning。
  - `safeCast=false` 時遇到不合法資料立即丟 `CsvExportError`（INVALID_OPTIONS）。
- **7.5 大量資料**：
  - 使用串流寫出，不一次載入全部字串。每寫入 N 筆 flush。
- **7.6 排序**：
  - 預設 `entity_name ASC, field_order ASC`。若 `sortBy` 提供不存在欄位，加入 warning 並忽略該鍵。

---

## 8. 錯誤處理與日誌
- 主要錯誤碼：IO_ERROR、ENCODING_ERROR、INVALID_OPTIONS、EMPTY_MODEL。
- 記錄 warning：欄位缺失、自動修正、未知欄位、排序鍵無效。
- 日誌層級：DEBUG（輸出選項、首行樣本）、INFO（完成統計）、WARN（資料修正）、ERROR（失敗）。

---

## 9. 測試策略（TDD）
- 測試金字塔：單元測試 > 組合測試 > 端對端（TestXml 駆動）。
- 覆蓋目標：
  - 單元：匯出器 95% line/branch。
  - 組合：涵蓋主要選項組合。
  - 端對端：以實際 .H 樣本覆蓋多語系、特殊字元、異常路徑。

---

## 10. 單元測試案例一覽（Given/When/Then）
- V19-CSV-UNIT-001 基本輸出（預設選項，含表頭，逗號分隔）。
- V19-CSV-UNIT-002 引號與轉義（含逗號、換行、引號、首尾空白）。
- V19-CSV-UNIT-003 Null 策略（empty/NULL/dash 的差異）。
- V19-CSV-UNIT-004 自訂分隔符與無表頭（`;`、Tab，`includeHeader=false`）。
- V19-CSV-UNIT-005 欄位挑選與重排（僅輸出 subset，順序正確）。
- V19-CSV-UNIT-006 排序鍵（預設與自訂，無效鍵忽略且產生 warning）。
- V19-CSV-UNIT-007 編碼與 BOM（UTF-8、BOM on/off；多國語言字元）。
- V19-CSV-UNIT-008 大量資料串流（10 萬列以上不 OOM，計時統計合理）。
- V19-CSV-UNIT-009 安全映射（缺欄/非法長度自動修正、warning）。
- V19-CSV-UNIT-010 嚴格模式（safeCast=false 遇非法資料拋錯）。
- V19-CSV-UNIT-011 I/O 例外（目錄不存在、權限不足、磁碟滿模擬）。
- V19-CSV-UNIT-012 Line ending（LF 與 CRLF 正確）。

---

## 11. 整合測試（解析 + 匯出）
- V19-CSV-IT-001 以標準 .H 樣本解析後匯出，逐欄比對 CSV。
- V19-CSV-IT-002 多實體/分節 .H（多個 `entity_name`）輸出排序與欄位序正確。
- V19-CSV-IT-003 含中文/日文註解與全形標點之 .H 正確轉碼與引號處理。
- V19-CSV-IT-004 缺少選填欄位的 .H（如無 `precision/scale`）輸出符合空值策略。
- V19-CSV-IT-005 自訂 columns 與 sortBy 組合（端對端）。

---

## 12. TestXml 規格與範例
- 建議位置：`tests/resources/v19/cases.xml`（路徑可依專案調整）
- XSD（簡化描述）：

```xml
<TestSuite version="19">
  <Case id="" name="">
    <Input file="inputs/sample1.h" />
    <Options
      delimiter="," 
      includeHeader="true"
      encoding="UTF-8"
      includeBom="false"
      lineEnding="LF"
      nullStrategy="empty"
      columns="entity_name,field_order,field_name,data_type"
      sortBy="entity_name:ASC,field_order:ASC"
      safeCast="true"
    />
    <Output file="expected/sample1.csv" />
  </Case>
  <!-- 可擴充更多屬性對應 CsvExportOptions -->
  <!-- 驗證：若 Output 指向 *.error.txt，則比對錯誤碼與訊息樣式 -->
  <!-- 比對策略：位元級別相等（含換行/編碼/BOM） -->
  <!-- 測試執行器：逐 Case 執行 解析→匯出→比對 或 捕捉錯誤 -->
  <!-- 日誌：建議記錄每個 Case 的 ExportReport 與 warnings -->
  
</TestSuite>
```

- 範例 `cases.xml`：

```xml
<TestSuite version="19">
  <Case id="V19-CSV-E2E-001" name="Basic export with header">
    <Input file="inputs/basic.h"/>
    <Options delimiter="," includeHeader="true" encoding="UTF-8" includeBom="false"
             lineEnding="LF" nullStrategy="empty"
             columns="entity_name,field_order,field_name,physical_name,data_type,length,precision,scale,nullable,default,comment,source_file,source_line,tags"
             sortBy="entity_name:ASC,field_order:ASC" safeCast="true"/>
    <Output file="expected/basic.csv"/>
  </Case>
  <Case id="V19-CSV-E2E-002" name="Semicolon without header">
    <Input file="inputs/semicolon.h"/>
    <Options delimiter=";" includeHeader="false" encoding="UTF-8" includeBom="true"
             lineEnding="CRLF" nullStrategy="NULL" safeCast="true"/>
    <Output file="expected/semicolon.csv"/>
  </Case>
  <Case id="V19-CSV-E2E-003" name="Strict mode error">
    <Input file="inputs/invalid.h"/>
    <Options delimiter="," includeHeader="true" safeCast="false"/>
    <Output file="expected/invalid.error.txt"/>
  </Case>
  
</TestSuite>
```

- 執行邏輯：
  - 對每個 Case：讀取 `.h` → 解析 → 依 Options 匯出 → 與 `expected` 檔逐位元比對；若為 `.error.txt` 則比對錯誤碼與訊息樣式。

---

## 13. 輸出 CSV 範例

```
entity_name,field_order,field_name,physical_name,data_type,length,precision,scale,nullable,default,comment,source_file,source_line,tags
Customer,1,Id,ID,NUMERIC,,10,0,false,,Primary key,customer.h,12,
Customer,2,Name,NAME,VARCHAR,100,,,,false,,"Customer ""display"" name",customer.h,13,core|pii
Customer,3,Note,NOTE,VARCHAR,200,,,,true,,May contain newlines,customer.h,14,
```

---

## 14. 組態項與 CLI（如有）
- 新增組態鍵（建議命名）：
  - `export.csv.enabled`（bool, 預設 false）
  - `export.csv.path`（string，相對或絕對路徑）
  - `export.csv.options.*`（對應 `CsvExportOptions`）
- CLI：`--export-csv <path>` 與對應選項（同第 6 節）

---

## 15. 要改動的地方（Func、資料流、介面、Test、TestXml）
- **15.1 Func（新/修）**
  - 新增 `CsvExportService` 及其實作 `DefaultCsvExportService`
  - 新增 `CsvRowSerializer`（負責欄位→字串、引號轉義、null 策略）
  - 新增 `CsvWritePipeline`（串流分段寫入、flush、BOM、編碼、換行）
  - 既有 UseCase/Workflow：在「.H 解析完成事件」後掛接「CSV 匯出步驟」（受 `export.csv.enabled` 控制）
- **15.2 資料流**
  - Input `.H` → 解析器 → `ParsedModel` → `CsvExportService.exportToCsv` → 檔案/串流
- **15.3 介面**
  - 公開 `CsvExportService` 與 `CsvExportOptions`（見第 6 節）
  - 既有 UseCase 新增依賴注入點（若使用 DI，註冊為 Scoped/Singleton 規則依專案而定）
- **15.4 Test**
  - 單元：對 `CsvRowSerializer`、`DefaultCsvExportService`、異常路徑、串流大檔
  - 整合：解析器 + 匯出整合場景（見第 11 節）
- **15.5 TestXml**
  - 新增 `tests/resources/v19/inputs/*.h`、`expected/*.csv`、`cases.xml`
  - 測試執行器支援 v19 `TestSuite` 格式（見第 12 節）

---

## 16. 驗收標準
- 必要選項（分隔符、引號、表頭、換行、BOM、null 策略、欄位挑選/排序）皆可用並符合規格。
- 單元與整合測試 100% 通過；端對端（TestXml）案例全部通過。
- 大量資料測試於預期記憶體占用內完成，不 OOM。
- 錯誤處理符合預期：IO、編碼、非法選項、空模型等。
- 產出 `ExportReport` 數值合理（筆數、耗時、表頭旗標）。

---

## 17. 風險與緩解
- 大量資料記憶體壓力 → 串流寫入 + 批次 flush。
- 多國語言編碼 → 一律以 UTF-8 處理，必要時加 BOM；新增編碼測試樣本。
- 現有模型欄位缺漏 → safeCast 預設開啟，並以 warning 記錄。

---

## 18. 開發步驟（TDD 導入順序）
1. 建立單元測試雛型（V19-CSV-UNIT-001/002/003），先紅燈。
2. 最小實作 `CsvRowSerializer` 令基本案例過綠。
3. 加入選項（null 策略、分隔符、表頭、引號），擴充測試。
4. 串流寫入管線與 BOM/換行測試。
5. 排序、欄位挑選/重排測試與實作。
6. 整合測試：接上解析器，端對端輸出比對。
7. TestXml 執行器案例補齊（含嚴格模式拋錯案例）。
8. 大量資料與 I/O 例外測試。
9. 收斂警告訊息格式、ExportReport。
10. 文件化 CLI/組態與使用說明。

---

## 19. 交付物
- 程式碼：CSV 匯出模組、服務、序列化器、管線、UseCase 介面接點。
- 測試：單元/整合/端對端（含 `cases.xml` 與樣本 `.h`/`.csv`）。
- 文件：本 TDD 規格、使用說明、範例指令。

---

## 附：實作位置（v19）
- 程式碼：`src/export/csv_export.py`
- 單元測試：`tests/export/test_csv_export_unittest.py`
- CLI：`tools/export_csv_from_h.py`

