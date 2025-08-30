## v16 Referenced Struct/Union Support（引用型 struct/union 展開與陣列支援）

### 背景與問題
- 目前 inline 定義的 struct/union 陣列可正確展開（例如 `struct { int x; } nd[2][2];`）。
- 但「引用已命名的 struct/union 型別」時，解析分支只建立 `nested` 但 `members=[]`：
  - 位置：`src/model/struct_parser.py` 的 `ref_match` 分支。
  - 結果：`layout` 在 `_process_array_member` 呼叫時，由於 `nested.members` 為空，無法展開元素（尺寸也為 0）。

### 目標
- 支援於同一個匯入的 .h 檔案中，對已命名的 `struct`/`union` 型別進行引用解析與展開：
  - `struct Inner { int x; }; struct Outer { struct Inner a; };` → `a.x` 正常出現。
  - 陣列版本 `struct Outer { struct Inner arr[2]; };` → `arr[0].x`, `arr[1].x`。
  - N-D 陣列與 `union` 的相同情境。
  - 支援「先用後定義」（forward reference）。
- 維持既有語意：指標陣列（例如 `struct Inner* p[3];`）仍視為 pointer 陣列，不展開為成員。

### 範圍與假設
- 單檔解析：僅針對使用者當前載入的 .h 檔內的型別定義與引用，不處理跨檔 `#include`。
- C 語法簡化：不處理 typedef 與複雜宣告（本次聚焦 `struct`/`union` 名稱的直接引用與其陣列）。

### 設計概述
1) 型別登錄（Type Registry）
   - 在 `parse_struct_definition_ast` 過程中建立 `known_types: Dict[str, StructDef|UnionDef]`。
   - 當遇到「具名」的 inline 定義（`struct Name { ... }` 或 `union Name { ... }`）時，將其 `members` 收錄至 `known_types[Name]`。

2) 引用解析（Ref Binding）
   - 針對 `ref_match` 分支：`struct|union <TypeName> <var_token>`
     - 解析出 `var_name, dims = _extract_array_dims(var_token)`。
     - 若 `TypeName` 已存在於 `known_types`：
       - 建立 `nested=StructDef/UnionDef(name=TypeName, members=deepcopy(known_types[TypeName].members))`。
     - 若尚未出現（forward reference）：
       - 建立 `nested=StructDef/UnionDef(name=TypeName, members=[])` 並標記 placeholder（可加 `__placeholder__=True` 或以外部表追蹤）。

3) 解析後解參考（Resolution Pass）
   - 在 `parse_struct_definition_ast` 結束後，對產生的頂層 `StructDef` 做一次遞迴走訪：
     - 對於 `MemberDef` 若 `nested` 存在且 `nested.members` 為空，且 `nested.name` 在 `known_types` 中，填入 `members=deepcopy(known_types[nested.name].members)`。
     - 遞迴處理子層，直到所有可解析的 placeholder 都被替換為完整成員。
   - 避免無窮展開：
     - 僅針對「直接內嵌」的引用展開；若發現自我參照（例如 `struct Node { struct Node child; }`），標示為非法或忽略（C 僅允許指標自我參照）。
     - 規則：若 `nested.name` 與當前所在的型別名稱相同，且非指標語境，拒絕展開（保留空，並可在後續加上錯誤/警告）。

4) Layout/Presenter
   - `src/model/layout.py` 的 `_process_array_member` 已支援「nested 不為 None 且有 members」時的陣列展開；因此無需更動。
   - `StructPresenter` 也已能將 AST 轉為顯示節點。引用型展開後會自然顯示在樹狀。

### 實作重點（檔案/函式）
- `src/model/struct_parser.py`
  - `parse_struct_definition_ast`
    - 新增：`known_types` 建立與填充（遇到具名 inline 定義時登錄）。
    - `ref_match` 分支：由原本 `members=[]` 改為優先從 `known_types` 取出深拷貝；未命中時建立 placeholder。
    - 新增：`_resolve_references(root_struct_def, known_types)`，在完成初步解析後呼叫，補齊 placeholder 的 `members`。
  - 風險控制：維持 `parse_member_line` 舊行為，避免影響基本型別/指標處理。

### 測試計畫
- 單元測試（新增於 `tests/model/`）
  1. 引用型單一成員：
     ```c
     struct Inner { int x; char y; };
     struct Outer { struct Inner a; };
     ```
     - 期望：`a.x`, `a.y` 被展開。
  2. 引用型陣列（1D, 2D）：
     ```c
     struct Inner { int x; };
     struct Outer { struct Inner arr[2]; };
     struct Outer2 { struct Inner nd[2][2]; };
     ```
     - 期望：`arr[0].x`, `arr[1].x` 與 `nd[0][0].x`、`nd[1][1].x`。
  3. 引用型 union 陣列：
     ```c
     union U { int a; char b; };
     struct S { union U u_arr[2]; };
     ```
     - 期望：展開為 `u_arr[0].a/b`、`u_arr[1].a/b`（依 layout 規則）。
  4. forward reference：
     ```c
     struct Outer { struct Inner a; };
     struct Inner { int x; };
     ```
     - 期望：`a.x` 展開成功。
  5. 自我參照（僅指標合法）：
     ```c
     struct Node { struct Node *next; };
     ```
     - 期望：`next` 為 pointer 欄位，不展開成員。

### 相容性與效能
- 相容性：不影響現有 inline 展開、基本型別、bitfield、pointer 陣列。
- 效能：解析多一個 registry 與一次走訪（O(N)）。可視需求於大型檔案加入快取/短路。

### 風險與緩解
- 型別名衝突：以「最後一個同名定義生效」的近似策略；必要時可發出警告。
- 不完整/非法宣告：placeholder 最終仍無法解析時，保留空 members（行為與先前一致），並可於未來加上警示。

### 交付清單（實作任務）
- 建立 `known_types` 與 `_resolve_references`（`src/model/struct_parser.py`）。
- 更新 `ref_match` 分支填入已知型別的 `members` 深拷貝。
- 新增單元測試：引用型單一、1D/2D 陣列、union 陣列、forward reference、自我參照指標。
- 手動驗證：以 `examples/` 與 `tests/data/*.h` 驗證 GUI 展開正確。

### 快速驗證
- 可使用 `examples/v16_example_struct.h` 驗證以下情境：
  - 多個頂層定義與目標結構切換（Target Struct）。
  - 引用型 struct/union（含 1D 陣列、union 陣列）。
  - forward reference 展開（`Outer` 先於 `Inner` 宣告）。
  - 指標成員不展開 nested（`struct Inner *p;`）。

---

### TDD 開發計畫（v16）

目標：支援同檔案中「引用型 struct/union」的解析與展開（含陣列與 N-D 陣列），並處理 forward reference。

1) 測試清單（先測再做）
   - 單元測試：`tests/model/test_struct_parser_v16_referenced_types.py`
     - `test_referenced_struct_single_member`：
       ```c
       struct Inner { int x; char y; };
       struct Outer { struct Inner a; };
       ```
       - 期望：AST/成員包含 `a.x`, `a.y`（透過 layout 展開或 AST 走訪確認）。
     - `test_referenced_struct_array_1d`：
       ```c
       struct Inner { int x; };
       struct Outer { struct Inner arr[2]; };
       ```
       - 期望：`arr[0].x`, `arr[1].x`。
     - `test_referenced_struct_array_2d`：
       ```c
       struct Inner { int x; };
       struct Outer { struct Inner nd[2][2]; };
       ```
       - 期望：`nd[0][0].x`、`nd[1][1].x`。
     - `test_referenced_union_array`：
       ```c
       union U { int a; char b; };
       struct S { union U u_arr[2]; };
       ```
       - 期望：展開為 `u_arr[0].a/b` 與 `u_arr[1].a/b`。
     - `test_forward_reference`：
       ```c
       struct Outer { struct Inner a; };
       struct Inner { int x; };
       ```
       - 期望：`a.x` 可展開（解析後解參考 pass 生效）。
     - `test_self_reference_pointer_only`：
       ```c
       struct Node { struct Node *next; };
       ```
       - 期望：`next` 維持 pointer，不展開子成員。

   - 佈局測試：`tests/model/test_layout_v16_referenced_types.py`
     - 驗證上述情境在 `calculate_layout` 下產出正確展平名稱與 offset/size。

   - 整合測試（Presenter）：`tests/presenter/test_presenter_v16_referenced_types.py`
     - 用檔案載入上述案例，`get_display_nodes("tree")` 中節點展開正確。

2) 實作步驟
   - 實作 1：在 `parse_struct_definition_ast` 內建立 `known_types` registry。
   - 實作 2：遇到具名 inline 定義時，將其成員登錄到 `known_types`（名稱→members）。
   - 實作 3：`ref_match` 分支：優先從 `known_types` 取深拷貝填入 `nested.members`；無則建立 placeholder。
   - 實作 4：新增 `_resolve_references(root, known_types)`，在完成解析後對整棵 AST 做一次解參考（含 forward reference），處理自我參照防呆。
   - 實作 5：確認 `layout` 對 nested array 的展開行為正確（通常無需改動）。

3) 驗收標準
   - 全數新增測試通過；既有測試不回歸失敗。
   - GUI 實測：載入包含引用型 struct/union 的 .h，樹狀節點展開與 byte layout 正確。



