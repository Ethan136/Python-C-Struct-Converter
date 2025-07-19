# v5 Post Test Refactor（AST/TDD 重構後測試規劃）

## 1. 目標
- **強化 AST/Parser 測試覆蓋率**：涵蓋巢狀 struct/union/array、匿名 struct/union、N-D array、bitfield 等情境。
- **推動 XML 驅動測試**：將重複、資料驅動測試集中於 XML，提升可維護性。
- **抽象共用驗證 helper**：遞迴比對 AST 結構、展平結果，減少重複驗證邏輯。
- **測試分層與主題分類**：依 model/view/presenter/integration/data_driven/utils 分層管理測試。
- **平行開發測試同步**：各主題分支測試規劃、stub、TDD 流程明確，便於協作。

## 2. AST/Parser 測試重構重點

### 2.1 巢狀 struct/union/array
- 以 TDD 流程重構 `parse_struct_definition_ast`，逐步讓巢狀 struct 測試綠燈。
- 測試涵蓋：
    - 巢狀 struct/union/array
    - 匿名 struct/union（暫 skip，待後續主題）
    - N-D array（暫 skip，待後續主題）
    - 匿名 bitfield（暫 skip，待後續主題）
- 驗證方式：
    - 遞迴比對 AST 結構
    - 展平成員名稱
    - XML 驅動測試（建議）

### 2.2 XML 驅動測試
- 將重複、資料驅動測試集中於 XML，減少 hardcode 測試。
- 測試資料建議集中於 `tests/data/`，格式與 v4 相容。
- Loader/驗證 helper 建議抽象共用，便於各主題複用。
- **struct/AST/layout 測試也應 XML 驅動**，以利未來維護與擴充。

### 2.3 測試分層與主題分類
- 依 v4 建議，測試分為 model/view/presenter/integration/data_driven/utils/data。
- 各主題測試檔案明確標註覆蓋重點、XML 驅動整合方式。
- 測試 stub、TDD 流程、XML 驅動建議同步補充於主題文件。

## 3. 平行開發測試同步建議
- 各主題分支（如 union、N-D array、bitfield、pragma pack）應：
    - 依主題文件規劃 stub、TDD 流程、XML 驅動測試。
    - 測試 stub/skip 明確，便於後續恢復。
    - 共用驗證 helper 集中於 utils，減少重複。
    - 測試資料集中於 data/，便於管理。
- 合併前，建議以 pytest/CI/CD 驗證全測試綠燈。

## 4. 進度與後續建議
- 巢狀 struct AST/TDD 重構已完成，測試全綠。
- 進階主題測試（union/array/bitfield/pragma pack）可依分支平行開發，stub/skip 明確。
- 測試與文件同步，建議逐步精簡、集中 XML 驅動、抽象共用驗證邏輯。
- 持續檢查覆蓋率，補齊 edge case。

## 5. 參考文件
- v5_nested_struct.md
- v5_union.md
- v5_nd_array.md
- v5_anonymous_bitfield.md
- v5_pragma_pack.md
- v4_test_refactor.md 

## 6. 具體實作細節與範例

### 6.1 XML 驅動測試格式範例
```xml
<struct_parser_v2_struct_tests>
    <test_case name="simple_struct">
        <struct_definition><![CDATA[
            struct Simple {
                char a;
                int b;
            };
        ]]></struct_definition>
        <expected_struct_name>Simple</expected_struct_name>
        <expected_members>
            <member type="char" name="a"/>
            <member type="int" name="b"/>
        </expected_members>
        <expected_layout>
            <item name="a" type="char" offset="0" size="1"/>
            <item name="padding" type="padding" offset="1" size="3"/>
            <item name="b" type="int" offset="4" size="4"/>
        </expected_layout>
        <expected_total_size>8</expected_total_size>
        <expected_align>4</expected_align>
    </test_case>
</struct_parser_v2_struct_tests>
```

### 6.2 驗證 helper 抽象建議
- 建議將 AST 遞迴比對、展平成員名稱等驗證邏輯抽象為共用 helper，例如：
```python
def flatten_member_names(sdef):
    # 遞迴展平所有成員名稱（含 array 展開）
    ...

def assert_ast_equal(ast1, ast2):
    # 遞迴比對兩個 AST 結構與型別
    ...
```
- 集中於 tests/utils/，各主題測試可直接 import 使用。

### 6.3 XML loader 實作建議
- 建議 loader 支援 struct/AST/layout 驗證，解析 struct_definition、expected_members、expected_layout、expected_total_size、expected_align 等欄位。
- 例：
```python
class StructModelXMLTestLoader(BaseXMLTestLoader):
    def parse_common_fields(self, case):
        data = super().parse_common_fields(case)
        # 解析 <input_data><hex> 作為 input_hex
        ...
        return data
```

### 6.4 測試分層與覆蓋率同步建議
- 測試分層建議：model/view/presenter/integration/data_driven/utils/data。
- 各主題測試檔案明確標註覆蓋重點、XML 驅動整合方式。
- 測試 stub、TDD 流程、XML 驅動建議同步補充於主題文件。
- 覆蓋率同步建議：
    - 每次主題開發/合併前，執行 pytest/CI/CD，確保全測試綠燈。
    - 持續檢查 edge case，補齊測試資料與驗證邏輯。 

### 6.5 共用驗證 helper 實作範例
```python
# tests/utils/ast_helpers.py

def flatten_member_names(sdef):
    """遞迴展平所有成員名稱（含 array 展開）"""
    result = []
    def walk(m, prefix=""):
        if hasattr(m, 'array_dims') and m.array_dims:
            from itertools import product
            dims = [range(d) for d in m.array_dims]
            for idxs in product(*dims):
                idx_str = ''.join(f"[{i}]" for i in idxs)
                if getattr(m, 'nested', None):
                    for nm in m.nested.members:
                        walk(nm, prefix + m.name + idx_str + ".")
                else:
                    result.append(prefix + m.name + idx_str)
        elif getattr(m, 'nested', None):
            for nm in m.nested.members:
                walk(nm, prefix + (m.name + "." if m.name else ""))
        else:
            result.append(prefix + m.name)
    for m in sdef.members:
        walk(m)
    return result

def assert_ast_equal(ast1, ast2):
    """遞迴比對兩個 AST 結構與型別"""
    assert type(ast1) == type(ast2)
    if hasattr(ast1, 'name'):
        assert ast1.name == ast2.name
    if hasattr(ast1, 'type'):
        assert ast1.type == ast2.type
    if hasattr(ast1, 'members'):
        assert len(ast1.members) == len(ast2.members)
        for m1, m2 in zip(ast1.members, ast2.members):
            assert_ast_equal(m1, m2)
    if hasattr(ast1, 'nested') and ast1.nested:
        assert_ast_equal(ast1.nested, ast2.nested)
```

### 6.6 XML loader 實作片段
```python
# tests/data_driven/xml_struct_model_loader.py
from tests.data_driven.base_xml_test_loader import BaseXMLTestLoader

class StructModelXMLTestLoader(BaseXMLTestLoader):
    def parse_common_fields(self, case):
        data = super().parse_common_fields(case)
        input_data_elem = case.find('input_data')
        input_hex = None
        if input_data_elem is not None:
            hex_elem = input_data_elem.find('hex')
            if hex_elem is not None and hex_elem.text:
                input_hex = hex_elem.text.strip()
        data['input_hex'] = input_hex
        # 將 expected_results 數值欄位轉為 int
        for member in data.get('expected', []):
            for key in ('offset', 'size', 'bit_offset', 'bit_size'):
                if key in member:
                    member[key] = int(member[key])
        return data
```

### 6.7 測試 stub/skip 實作建議
- 針對尚未支援的主題（如 union/N-D array/bitfield），建議先以 pytest.mark.skip 或 unittest.skip 註記 stub，待主題完成後恢復。
```python
import pytest
@pytest.mark.skip(reason="union not supported in MVP")
def test_union_ast():
    ...
```

### 6.8 CI/CD pytest 用法與覆蓋率檢查建議
- 建議以 pytest 執行所有測試，並加上 --maxfail=10 方便快速定位錯誤。
- 覆蓋率檢查可用 pytest-cov：
```sh
pytest --maxfail=10 --cov=src tests/
```
- CI/CD 可設置自動執行 pytest、覆蓋率門檻、artifact 上傳等。 

## 7. Model 層測試精煉/重構規劃

### 7.1 已完成 XML 驅動
- struct/AST/layout 測試已 XML 驅動，並補充 loader 實作。
- 主要覆蓋 struct 定義、AST 結構、layout 結果、bitfield、array、巢狀 struct 等情境。

### 7.2 可進一步資料驅動的測試
- 手動 struct/bitfield 測試（如 set_manual_struct、calculate_manual_layout、bitfield layout 驗證等）可考慮設計 XML/JSON 驅動，提升可維護性。
- 匯出 .h 檔案內容驗證（如 export_manual_struct_to_h）可將輸入/預期片段資料化。

### 7.3 建議保留 hardcode 的測試
- 物件初始化、例外處理、極端錯誤情境等，維持 unit test 直觀性。
- 複雜結構驗證（如 test_combined_example_struct）可視需求資料驅動，但目前 hardcode 便於直接閱讀。

### 7.4 後續建議
- 若需進一步精煉，建議設計 test_struct_model_manual_config.xml，描述 members、total_size、預期驗證點（如 layout、錯誤訊息、匯出內容），並新增 loader 與 XML 驅動測試類別。 

### 7.5 執行優先順序建議
1. 先盤點現有 hardcode 測試，分類哪些適合資料驅動、哪些建議保留。
2. 針對手動 struct/bitfield 測試、.h 匯出驗證，設計 XML schema 並建立測試資料。
3. 新增 loader 與 XML 驅動測試類別，逐步搬移 hardcode 測試。
4. 每完成一類型搬移，執行 pytest 並確認覆蓋率。
5. 文件同步更新，標註已完成/待辦項目。

### 7.6 XML schema 範例
```xml
<manual_struct_tests>
    <test_case name="bitfield_layout">
        <members>
            <member name="a" type="unsigned int" bit_size="3"/>
            <member name="b" type="unsigned int" bit_size="5"/>
            <member name="c" type="unsigned int" bit_size="8"/>
        </members>
        <total_size>4</total_size>
        <expected_layout>
            <item name="a" type="unsigned int" offset="0" size="4" bit_offset="0" bit_size="3"/>
            <item name="b" type="unsigned int" offset="0" size="4" bit_offset="3" bit_size="5"/>
            <item name="c" type="unsigned int" offset="0" size="4" bit_offset="8" bit_size="8"/>
        </expected_layout>
    </test_case>
    <test_case name="export_to_h">
        <members>
            <member name="a" type="unsigned int" bit_size="3"/>
            <member name="b" type="unsigned int" bit_size="5"/>
        </members>
        <total_size>1</total_size>
        <expected_h_contains>
            <line>struct MyStruct</line>
            <line>unsigned int a : 3;</line>
            <line>unsigned int b : 5;</line>
            <line>// total size: 1 bytes</line>
        </expected_h_contains>
    </test_case>
</manual_struct_tests>
```

### 7.6.1 驗證重點與 edge case
- bitfield packing、欄位順序、alignment、padding、pointer、混合欄位、巢狀 struct、N-D array、匿名 bitfield、空 struct、極短/極長 hex 輸入、big/little endian 差異、final padding、layout 計算（offset/size/bit_offset/bit_size）
- 例外處理：struct 定義錯誤、hex 長度不足、欄位名稱重複、bit_size 非法、total_size 非法等

### 7.6.2 進階 XML schema 範例
```xml
<struct_model_tests>
    <test_case name="bitfield_and_padding">
        <struct_definition><![CDATA[
            struct B {
                int a : 1;
                int b : 2;
                int c : 5;
                char d;
            };
        ]]></struct_definition>
        <input_data>
            <hex>8d410000</hex>
        </input_data>
        <expected_results>
            <member name="a" value="1"/>
            <member name="b" value="2"/>
            <member name="c" value="17"/>
            <member name="d" value="65"/>
        </expected_results>
        <expected_layout>
            <item name="a" type="int" offset="0" size="4" bit_offset="0" bit_size="1"/>
            <item name="b" type="int" offset="0" size="4" bit_offset="1" bit_size="2"/>
            <item name="c" type="int" offset="0" size="4" bit_offset="3" bit_size="5"/>
            <item name="d" type="char" offset="4" size="1"/>
            <item name="(final padding)" type="padding" offset="5" size="3"/>
        </expected_layout>
    </test_case>
    <test_case name="anonymous_bitfield">
        <struct_definition><![CDATA[
            struct C {
                int a : 3;
                int : 2;
                int b : 5;
            };
        ]]></struct_definition>
        <input_data>
            <hex>f1000000</hex>
        </input_data>
        <expected_results>
            <member name="a" value="5"/>
            <member name="(anonymous)" value="3"/>
            <member name="b" value="17"/>
        </expected_results>
    </test_case>
    <test_case name="error_case">
        <struct_definition><![CDATA[
            struct D {
                int a;
                int a;
            };
        ]]></struct_definition>
        <expect_error>成員名稱 'a' 重複</expect_error>
    </test_case>
</struct_model_tests>
```

### 7.7 已完成/待辦 checklist
- [x] struct/AST/layout 測試 XML 驅動化
- [ ] 手動 struct/bitfield 測試資料驅動化
- [ ] 匯出 .h 驗證資料驅動化
- [x] 文件同步規劃與說明 

### 7.8 測試資料與驗證同步設計建議
- 測試資料（XML）與驗證邏輯（loader、assert）應同步設計，確保每個欄位都能被驗證到。
- loader 應支援自動比對 layout、bitfield、padding、匿名欄位、錯誤情境等細節。
- 每次擴充 edge case，建議先設計 XML 測試資料，再同步補充驗證邏輯。 

### 7.9 執行細節與實作步驟
1. 盤點現有 hardcode 測試，依 7.6.1 條列分類，標註優先精煉項目。
2. 針對每一類型（如 bitfield、manual struct、.h 匯出），設計對應 XML schema，並先以最小可行範例建立測試資料。
3. 新增 loader，確保能正確解析 XML 並支援 layout、bitfield、padding、匿名欄位、錯誤情境等驗證。
4. 重構/搬移 hardcode 測試，逐步改為 XML 驅動，並保留必要的 hardcode unit test（如例外處理、極端情境）。
5. 每搬移一類型，執行 pytest，確保所有 edge case 覆蓋且測試全綠。
6. 文件同步更新，記錄每次搬移的進度、遇到的問題與解法。
7. 定期 review 測試覆蓋率，補齊尚未資料驅動的 edge case。
8. 團隊協作時，建議每次 PR 附上對應 XML 測試資料與 loader 變更，確保規格與驗證同步。 

### 7.10 edge case XML 驗證規劃
- 已設計 edge case 類型：
  - padding、final padding
  - 空 struct
  - 極短 hex、極長 hex
  - bitfield、匿名 bitfield
- XML schema 範例：
```xml
<manual_struct_tests>
    <test_case name="padding_and_final_padding">
        <members>
            <member name="a" type="char" bit_size="0"/>
            <member name="b" type="int" bit_size="0"/>
        </members>
        <total_size>8</total_size>
        <expected_layout>
            <item name="a" type="char" offset="0" size="1"/>
            <item name="(padding)" type="padding" offset="1" size="3"/>
            <item name="b" type="int" offset="4" size="4"/>
        </expected_layout>
    </test_case>
    <test_case name="empty_struct">
        <members></members>
        <total_size>0</total_size>
        <expected_layout></expected_layout>
    </test_case>
    <test_case name="short_hex_struct">
        <members>
            <member name="a" type="int" bit_size="0"/>
            <member name="b" type="int" bit_size="0"/>
        </members>
        <total_size>8</total_size>
        <expected_layout>
            <item name="a" type="int" offset="0" size="4"/>
            <item name="b" type="int" offset="4" size="4"/>
        </expected_layout>
    </test_case>
</manual_struct_tests>
```
- 驗證重點：
  - layout 結果正確（offset/size/padding/bitfield/匿名欄位）
  - 空 struct 不產生 layout
  - 支援極短/極長 hex 對應 layout
- 擴充方式：
  - 依 7.6.1 條列 edge case，持續新增 XML 測試資料即可。
  - 每次擴充後執行 pytest，確保驗證邏輯與資料一致。 

### 7.11 錯誤情境 XML 驗證規劃
- 可驗證錯誤情境：
  - 欄位名稱重複
  - bit_size 非法（負數、超過型別上限）
  - total_size 非法（負數、過小）
  - hex 長度不足/過長
  - 不支援型別
- XML schema 範例：
```xml
<manual_struct_error_tests>
    <test_case name="duplicate_member_name">
        <members>
            <member name="a" type="int" bit_size="0"/>
            <member name="a" type="char" bit_size="0"/>
        </members>
        <total_size>8</total_size>
        <expect_error>成員名稱 'a' 重複</expect_error>
    </test_case>
    <test_case name="invalid_bit_size">
        <members>
            <member name="a" type="int" bit_size="-1"/>
        </members>
        <total_size>4</total_size>
        <expect_error>bit_size 需為 0 或正整數</expect_error>
    </test_case>
    <test_case name="invalid_total_size">
        <members>
            <member name="a" type="int" bit_size="0"/>
        </members>
        <total_size>-1</total_size>
        <expect_error>結構體大小需為正整數</expect_error>
    </test_case>
</manual_struct_error_tests>
```
- 驗證重點：
  - 正確捕捉並比對例外訊息
  - 支援多種錯誤情境
- 擴充方式：
  - 依 7.6.1 條列錯誤情境，持續新增 XML 測試資料即可。
  - 每次擴充後執行 pytest，確保驗證邏輯與資料一致。 