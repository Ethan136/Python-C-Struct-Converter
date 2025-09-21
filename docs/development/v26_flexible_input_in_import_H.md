# 基本規範
- 使用者需求，列在「需求草稿」，AI不要改這個 section 的內容
- AI 生成的內容，列在後續 section（可自行新增 section）

# 需求草稿（使用者需求在這邊提出）
在「匯入 .h」功能欄位，新增一個新的輸入方式
- 目前的輸入方式有：1byte / 4byte / 8byte 為單位輸入
- 新增的輸入方式為：輸入欄位直接是一個字串輸入框，裡面可以輸入多個byte 的內容
- 舉例如下
	- 假設現在要輸入3byte byte[0] = 0x01, byte[1] = 0x02, byte[2] = 0x03
	- 使用者可以在輸入寫入下列任一種寫法
		- 方式1：0x030201
		- 方式2：0x01, 0x02, 0x03
		- 方式3：0x01, 0x0302
		- 方式4: 0x0201, 0x03
上述輸入框的基本邏輯為
- 輸入欄位驗證
	- 僅允許 ^0[xX][0-9A-Fa-f_]+$；0x 或 0X 之後必須至少一個十六進位字元（否則報錯）。
	- 解析流程以「移除底線 _ 後」再檢查長度、奇數位補 0 與小端展開。
- 把輸入的字串，拆成多個輸入的 byte 組
	- 例如 "0x0201, 0x03" -> 拆成 0x0201 和 0x03
- 輸入的字串，以任意數目的「,」或「空格」或「tab」，或『任意數目的前述三者的任意組合』來代表字串拆分點
	- 例如 "0x0201 0x03" -> 拆成 "0x0201" 和 "0x03"
	- 例如 "0x0201,0x03" -> 拆成 "0x0201" 和 "0x03"
	- 例如 "0x0201	0x03" -> 拆成 "0x0201" 和 "0x03"
	- 例如 "0x0201 , 0x03" -> 拆成 "0x0201" 和 "0x03"
	- 例如 "0x0201	, 0x03" -> 拆成 "0x0201" 和 "0x03"
	- 例如 "0x0201   0x03" -> 拆成 "0x0201" 和 "0x03"
- 每個 token 以小端序展開
- 支援底線 _、大小寫；無 "0x" 前綴則不支援
- 前綴同時允許 0x 與 0X
- 若十六進位數字長度為奇數，左側補 0
- 超長時裁切：最終 bytes 超過 N 時，從「尾端（高位）」開始裁掉多餘 bytes；並在 UI 顯示被裁掉的區段，含對應的 token 來源與位移範圍
	- 例：輸入最終為 01 02 03，N=2 → 保留 01 02、裁掉 03（屬高位端）
	- 超長的時候「接受但告警」
- 固定長度欄位對齊：不足時「尾端」補 0x00 至 N bytes。
	- 不足的時候「接受但告警」，並列出哪幾個 byte 補 0
- 錯誤訊息一致性：
	- 無效字元、缺少數字（如僅 0x）、含空白於 token 內等，統一報錯格式，指明「第幾個 token」與片段內容。
- 串接順序再次明示：
	- 「各 token 先小端展開，再依輸入順序串接」；例：0x01, 0x0302 → 01 + 02 03 → 01 02 03。
- 空整串輸入在非固定長度欄位的行為 -> 接受，視為全 0
- 分割後的空 token：「忽略」以容忍前後分隔符。

# 功能規格
- 輸入模式新增「字串 Bytes」：以單一文字框輸入多個十六進位 token，支援以逗號/空白/tab 的任意組合分隔。
- Token 規則：
	- 僅允許 `^0[xX][0-9A-Fa-f_]+$`；支援大小寫與底線 `_` 分組。
	- 解析時先移除底線 `_`，若 hex 位數為奇數，左側補 `0`。
	- 每個 token 以小端序展開為 bytes；多個 token 依輸入順序串接。
- 長度規則：
	- 固定長度欄位：
		- 不足：尾端補 `0x00` 至 N bytes，接受但告警，並列出補齊的位元組範圍。
		- 超長：從尾端（高位）裁掉多餘 bytes，接受但告警，並標示被裁掉的位元組與其來源 token/位移範圍。
	- 非固定長度欄位：接受任意長度。空輸入視為長度 0。
- 驗證與錯誤訊息：
	- 不符合 token 規則（如僅 `0x`、含非 hex 字元、token 內含空白）時，逐一指出第幾個 token 與原字串片段。
	- 分割後的空 token 忽略，不構成錯誤。
- 預覽與提示（UI）：
	- 即時顯示解析後 bytes（格式 `01 02 03`）與總長度。
	- 若有補零/裁切，於旁顯示告警徽章與詳細列表。

# 開發規劃（TDD）
- 單元測試（Parser）
	- 基本解析：`0x030201` → `01 02 03`；`0x01,0x02,0x03`；`0x01, 0x0302`；`0x0201 0x03`。
	- 分隔容忍：逗號/空白/tab 與其任意組合；重複分隔不產生空 token 錯誤。
	- 格式邊界：大小寫、含底線、奇數位左補 0；無 `0x/0X` 前綴視為錯誤。
	- 錯誤案例：僅 `0x`、含非 hex 字元、token 內含空白，逐一回報第幾個 token。
	- 長度規則：
		- 固定長度不足補零並回報補零範圍。
		- 固定長度超長裁切並回報被裁掉的 bytes 與來源 token/位移。
		- 非固定長度接受任意長度，空輸入長度 0。
- Presenter 測試
	- 新增輸入模式選擇，委派解析器，成功/失敗訊息映射。
	- 固定長度欄位時的補零/裁切告警內容傳遞與格式一致性。
- View（UI）測試
	- 模式切換：新增「字串 Bytes」輸入框顯示/隱藏。
	- 即時預覽與長度顯示；補零/裁切時顯示告警徽章與詳情彈出。
	- 分隔混用輸入互動測試（鍵入逗號/空白/tab）。
- 整合測試
	- 以既有資料流（import .h → model → presenter → view）驗證 bytes 寫入與版位計算無回歸。
	- 對齊既有 1/4/8-byte 模式：相同數值輸入，輸出 bytes 一致（小端）。

# 實作細節
- 受影響模組與新增模組：
	- 新增 `src/model/flexible_bytes_parser.py`
		- `tokenize_flexible_hex(input_str: str) -> list[str]`
			- 以 `[,\s]+` 切分；移除空 token；保留原輸入順序。
		- `parse_token_to_bytes(token: str) -> bytes`
			- 驗證 `^0[xX][0-9A-Fa-f_]+$`；移除底線；去前綴；奇數位左補 `0`；小端展開。
		- `assemble_bytes(tokens: list[str], target_len: int|None) -> tuple[bytes, dict]`
			- 串接所有 token 的 bytes；若 `target_len`：不足尾補 `0x00`；超長自尾端（高位）裁切；回傳 `meta`（補零/裁切的位元組範圍、來源 token 與位移）。
		- `parse_flexible_input(input_str: str, target_len: int|None) -> ParseResult`
			- `ParseResult` 含：`data: bytes`、`warnings: list[str]`、`trunc_info: list[dict]`、`byte_spans: list[dict]`（每個 byte 的來源 token 與位移）。
	- 既有 `src/model/input_field_processor.py`
		- 新增薄封：`process_flexible_input(input_str: str, target_len: int|None) -> ParseResult`（委派 `flexible_bytes_parser`）。
	- `src/presenter/struct_presenter.py`
		- 新增輸入模式狀態（儲存於 `context['extra']['input_mode']`，預設 `grid`）。
		- 新增：`set_input_mode(mode: str)`（`grid` | `flex_string`）。
		- 新增：`parse_flexible_hex_input()`
			- 由 View 取得原字串與 `total_size`、端序；呼叫 `process_flexible_input`；將 `ParseResult.data.hex()` 傳入既有 `model.parse_hex_data(...)`。
			- 根據 `ParseResult.warnings/trunc_info` 組合使用者訊息（採用既有 i18n key 或新增 key）。
	- `src/view/struct_view.py`
		- UI：在載入 .h 的頁籤新增「輸入模式」選擇（`grid`／`字串 Bytes`）。
		- 當模式為 `flex_string`：顯示單行 `Entry` 作為輸入框、bytes 預覽區、警告區。
		- 新增方法：
			- `get_input_mode() -> str`
			- `get_flexible_input_string() -> str`
			- `show_flexible_preview(hex_bytes: str, total_len: int, warnings: list[str], trunc_info: list[dict]) -> None`
		- 解析按鈕邏輯：
			- 若 `grid`：走原 `presenter.parse_hex_data()`；
			- 若 `flex_string`：呼叫 `presenter.parse_flexible_hex_input()`，並在回傳時更新預覽與結果表格。

- 串接與資料流：
	1) View 依模式提供輸入（`get_hex_input_parts` 或 `get_flexible_input_string`）。
	2) Presenter 依模式路由至對應處理：
		- grid：現有 `_process_hex_parts` → `model.parse_hex_data(...)`。
		- flex：`process_flexible_input` → `bytes.hex()` → `model.parse_hex_data(...)`。
	3) Model 沿用既有解析流程；不改動 AST/版位計算邏輯。

- 執行順序（開發步驟）：
	1) 新增 `flexible_bytes_parser` 與 `process_flexible_input`，完成單元測試。
	2) Presenter 新增 `set_input_mode`/`parse_flexible_hex_input` 與訊息映射，完成 Presenter 測試。
	3) View 新增 UI 與方法、預覽與警告顯示，完成 View 測試。
	4) 整合：兩種模式在相同檔案流程下可互相切換；回歸測試既有 grid 模式。

# 測試細節
- Model（`flexible_bytes_parser`/`input_field_processor`）
	- `tokenize_flexible_hex`：逗號/空白/tab 與混用；連續分隔；前後分隔；空字串。
	- `parse_token_to_bytes`：
		- 基本：`0x01`、`0x0201`、`0x030201` 小端展開；
		- 奇數位補 0：`0xABC` → `BC 0A`；
		- 底線：`0xAB_CD_EF`；大小寫 `0Xab`; 無 `0x` 應報錯。
	- `assemble_bytes` 固定長度：
		- 不足補零並回報補零範圍；
		- 超長自尾端裁切並回報被裁掉 bytes 與來源 token/位移。
	- `parse_flexible_input`：整合以上、回傳 `byte_spans` 對映正確。

- Presenter（`struct_presenter`）
	- `set_input_mode` 影響 context；
	- `parse_flexible_hex_input`：
		- 將 `ParseResult.data.hex()` 正確傳遞給 `model.parse_hex_data`；
		- 補零/裁切時回傳對應訊息（含 token/位移）；
		- 錯誤輸入（非法 token、僅 `0x` 等）能轉為一致的錯誤訊息（使用 i18n key）。

- View（`struct_view`）
	- 模式切換：`grid` ↔ `flex_string`，UI 顯示/隱藏切換正確；
	- 解析按鈕在 `flex_string` 模式呼叫 presenter 新 API；
	- 預覽顯示 bytes（`01 02 03`）與總長度；補零/裁切告警徽章與詳情列表更新正確；
	- 分隔混用輸入互動（鍵入逗號/空白/tab）不造成例外。

- 整合/回歸
	- 匯入 .h → 顯示 layout → `flex_string` 輸入 → 解析並顯示欄位值；
	- 與 `1/4/8-byte` grid 模式對齊：相同數值輸入應輸出一致 bytes；
	- CSV 匯出流程不因新模式破壞（必要時以 `ParseResult.data.hex()` 提供 `hex_input`）。

## 整合測試（實作細節）
- 測試目標：驗證 import .h → model → presenter → view 的完整資料流在 `flex_string` 模式下與 `grid` 模式一致，並確保 CSV 匯出可帶出 `hex_input`。

- 測試樣本（最小）：
	- 以 3 bytes 的結構驗證（如：`struct S { char a; short b; };`），LE 小端。
	- 預期 bytes：`01 02 03`（`hex_raw == '010203'`）。

- 驗證路徑：
	1) `StructModel.load_struct_from_file(...)` 取得 `layout/total_size`。
	2) `StructPresenter.set_input_mode('flex_string')` 使 context.extra.input_mode 為 `flex_string`。
	3) View 回傳 `get_flexible_input_string()` 的字串（例如 `0x01,0x0302`）。
	4) `StructPresenter.parse_flexible_hex_input()` → 呼叫 `process_flexible_input` → `model.parse_hex_data(...)`。
	5) 檢查 `parsed_values[0].hex_raw == '010203'`，且在補零/裁切時有 `warnings/trunc_info`。

- 與 grid 模式的一致性：
	- grid 模式（1-byte）依序輸入 `01`、`02`、`03`，與 flex 輸入 `0x030201`/`0x01,0x02,0x03`/`0x01, 0x0302`/`0x0201 0x03` 結果一致。
	- 以兩種模式結果的 `hex_raw` 比較相等作為斷言。

- CSV 匯出 `hex_input`（行為建議與驗證）：
	- 建議 Presenter 在 `parse_flexible_hex_input()` 成功後，於 `context['extra']['last_flex_hex']` 儲存 `ParseResult.data.hex()`。
	- View 匯出 `_on_export_csv()` 取得 `hex_input` 時：
		- 若為 `flex_string` 模式且存在 `context['extra']['last_flex_hex']`，則用它；
		- 否則沿用現有 grid 模式將 `get_hex_input_parts()` 合併的內容。
	- 測試可以 stub 取代實際寫檔，檢查組裝 `CsvExportOptions.hex_input` 或匯出內容包含 `010203`。

- 非 GUI 測試策略：
	- Presenter 測試：以 Mock View 實作 `get_flexible_input_string()`、`get_selected_endianness()`、`update_display()`、`on_values_refreshed()`，避免 GUI 依賴。
	- View 測試：以 `object.__new__(StructView)` 建立最小實例並注入 `presenter`、`flex_input_var` 等必需欄位，驗證 `get_input_mode()`、`get_flexible_input_string()`、`show_flexible_preview()` 的最小契約。

- 負向案例（整合）：
	- 提供非法 token（如 `0x`、`0xGG`、缺前綴 `01`）時，`parse_flexible_hex_input()` 回傳 `type=='error'`，訊息映射到 `dialog_invalid_input`。
	- 分隔符混用與連續分隔：`",,,  0x01 , 0x02  ,,,"` 解析成功（空 token 忽略）。
