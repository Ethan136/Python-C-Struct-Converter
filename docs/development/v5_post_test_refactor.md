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
<struct_parsing_tests>
    <test_case name="nested_struct_basic" type="parse">
        <struct_definition><![CDATA[
            struct Outer {
                struct Inner {
                    int x;
                    char y;
                } a;
                int b;
            };
        ]]></struct_definition>
        <expected_struct_name>Outer</expected_struct_name>
        <expected_members>
            <member type="struct" name="a">
                <nested_members>
                    <member type="int" name="x" />
                    <member type="char" name="y" />
                </nested_members>
            </member>
            <member type="int" name="b" />
        </expected_members>
    </test_case>
</struct_parsing_tests>
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
- 建議繼承 base_xml_test_loader.py，依主題擴充 parse_common_fields/parse_extra。
- loader 應能解析 struct_definition、expected_members、input_data、expected_results 等欄位。
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