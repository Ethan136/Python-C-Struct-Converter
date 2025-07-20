# v7 開發實作規劃 - 巢狀結構 AST 重構與展平優化

## 1. 開發目標與範圍

### 1.1 核心目標
- **AST 遞迴重構**：優化巢狀 struct/union/array 的 AST 結構，提升遞迴解析效能
- **展平算法優化**：改進複雜巢狀結構的展平算法，支援匿名結構和位元欄位
- **GUI 整合優化**：基於 v6 GUI 架構，優化複雜結構的顯示和互動
- **測試覆蓋強化**：建立完整的 XML 驅動測試，覆蓋所有邊界情況

### 1.2 功能範圍
- 巢狀 union/struct/array 的遞迴 AST 解析
- 匿名 struct/union/bitfield 的展平與命名
- N-D array 與巢狀結構的混合處理
- 複雜結構的記憶體佈局計算優化
- GUI 樹狀顯示的效能優化

### 1.3 不包含功能
- 多語系支援 (i18n)
- 無障礙功能 (a11y)
- 複雜事件流程
- 版本控制整合
- 進階權限管理

## 2. 技術架構設計

### 2.1 AST 結構優化
```python
# 優化後的 AST 節點結構
@dataclass
class ASTNode:
    id: str                    # 唯一識別符
    name: str                  # 節點名稱
    type: str                  # 型別 (struct/union/array/bitfield/basic)
    children: List[ASTNode]    # 子節點
    is_struct: bool           # 是否為 struct
    is_union: bool            # 是否為 union
    is_array: bool            # 是否為陣列
    is_bitfield: bool         # 是否為位元欄位
    array_dims: List[int]     # 陣列維度
    bit_size: Optional[int]   # 位元欄位大小
    bit_offset: Optional[int] # 位元欄位偏移
    offset: int               # 記憶體偏移
    size: int                 # 記憶體大小
    alignment: int            # 對齊要求
    is_anonymous: bool        # 是否為匿名結構
    flattened_name: str       # 展平後的名稱
    metadata: Dict[str, Any]  # 額外元資料
```

### 2.2 展平算法設計
```python
class FlatteningStrategy:
    """展平策略介面"""
    
    def flatten_node(self, node: ASTNode, prefix: str = "") -> List[FlattenedNode]:
        """展平單一節點"""
        pass
    
    def generate_name(self, node: ASTNode, prefix: str = "") -> str:
        """生成展平後的名稱"""
        pass
    
    def calculate_layout(self, node: ASTNode) -> LayoutInfo:
        """計算佈局資訊"""
        pass

class StructFlatteningStrategy(FlatteningStrategy):
    """Struct 展平策略"""
    
class UnionFlatteningStrategy(FlatteningStrategy):
    """Union 展平策略"""
    
class ArrayFlatteningStrategy(FlatteningStrategy):
    """Array 展平策略"""
```

### 2.3 GUI 整合架構
```python
class V7Presenter:
    """v7 Presenter，基於 v6 架構擴充"""
    
    def __init__(self):
        self.ast_root: Optional[ASTNode] = None
        self.flattened_nodes: List[FlattenedNode] = []
        self.context: Dict[str, Any] = self._init_context()
        self.flattening_strategy: FlatteningStrategy = self._create_strategy()
    
    def load_struct_definition(self, content: str) -> bool:
        """載入結構定義"""
        pass
    
    def get_ast_tree(self) -> ASTNode:
        """取得 AST 樹狀結構"""
        pass
    
    def get_flattened_layout(self) -> List[FlattenedNode]:
        """取得展平後的佈局"""
        pass
    
    def switch_display_mode(self, mode: str):
        """切換顯示模式"""
        pass
```

## 3. 實作步驟與里程碑

### 3.1 第一階段：AST 重構 (Week 1-2)
**目標**：建立優化的 AST 結構和解析器

#### 3.1.1 AST 節點重構
- [x] 定義新的 `ASTNode` dataclass
- [x] 實作節點 ID 生成策略
- [x] 建立節點類型驗證機制
- [x] 實作節點序列化/反序列化

#### 3.1.2 解析器優化
- [x] 重構 `parse_struct_definition_ast` 支援新 AST 結構
- [x] 優化巢狀結構的遞迴解析
- [x] 實作匿名結構的識別和處理
- [x] 建立解析錯誤處理機制

#### 3.1.3 測試建立
- [x] 建立 AST 節點單元測試
- [x] 建立解析器整合測試
- [x] 建立 XML 驅動測試框架

### 3.2 第二階段：展平算法實作 (Week 3-4)
**目標**：實作各種結構的展平策略

#### 3.2.1 展平策略實作
- [x] 實作 `StructFlatteningStrategy`
- [x] 實作 `UnionFlatteningStrategy`
- [x] 實作 `ArrayFlatteningStrategy`
- [x] 實作 `BitfieldFlatteningStrategy`

#### 3.2.2 命名策略
- [x] 實作匿名結構的命名規則
- [x] 實作陣列索引的命名策略
- [x] 實作位元欄位的命名策略
- [x] 建立命名衝突解決機制

#### 3.2.3 佈局計算
- [x] 優化記憶體佈局計算
- [x] 實作複雜對齊規則
- [x] 建立位元欄位的佈局計算
- [x] 實作 pragma pack 支援（預留/部分）

### 3.3 第三階段：GUI 整合 (Week 5-6)
**目標**：整合 v6 GUI 架構，優化顯示效能

#### 3.3.1 Presenter 擴充
- [ ] 擴充 `V7Presenter` 類別
- [ ] 實作 AST 到 GUI 節點的轉換
- [ ] 實作展平節點的顯示邏輯
- [ ] 建立效能優化機制

#### 3.3.2 View 優化
- [ ] 優化樹狀顯示的效能
- [ ] 實作大型結構的虛擬化顯示
- [ ] 建立節點展開/收合的動畫效果
- [ ] 實作搜尋和篩選功能

#### 3.3.3 互動功能
- [ ] 實作節點選擇和高亮
- [ ] 實作右鍵選單功能
- [ ] 實作拖拽和排序功能
- [ ] 建立鍵盤快捷鍵支援

### 3.4 第四階段：測試與優化 (Week 7-8)
**目標**：建立完整測試覆蓋，優化效能

#### 3.4.1 測試覆蓋
- [x] 建立完整的單元測試套件
- [x] 建立整合測試
- [x] 建立效能測試
- [x] 建立壓力測試

#### 3.4.2 效能優化
- [x] 優化 AST 解析效能
- [x] 優化展平算法效能
- [ ] 優化 GUI 渲染效能
- [x] 建立記憶體使用優化

#### 3.4.3 文件與範例
- [x] 更新技術文件
- [x] 建立使用範例
- [x] 建立 API 文件
- [x] 建立最佳實踐指南

## 3.5 Debug/Migration 策略（2024/07/09 補充）
- 採用 stepwise migration，從 minimal layout.py 開始，逐步還原 union/array/bitfield/struct flatten 功能。
- 每步都以 TDD 驗證所有 flatten/AST/bitfield/array/union 測試。
- union flatten/array flatten 僅保留最大分支，prefix/offset 嚴格對齊 C/C++。
- 針對 union/array flatten prefix/offset 問題，建立 minimal 測試案例，debug print 追蹤 prefix 傳遞與 offset 累加。
- 任何 flatten/命名/offset 修正都需同步更新測試與文件。
- CI/CD 持續整合，確保每次修正不破壞既有功能。

## 4. 測試策略

### 4.1 單元測試
```python
class TestASTNode:
    """AST 節點測試"""
    
    def test_node_creation(self):
        """測試節點建立"""
        pass
    
    def test_node_serialization(self):
        """測試節點序列化"""
        pass
    
    def test_node_validation(self):
        """測試節點驗證"""
        pass

class TestFlatteningStrategy:
    """展平策略測試"""
    
    def test_struct_flattening(self):
        """測試 struct 展平"""
        pass
    
    def test_union_flattening(self):
        """測試 union 展平"""
        pass
    
    def test_array_flattening(self):
        """測試陣列展平"""
        pass
```

### 4.2 XML 驅動測試
```xml
<v7_test_suite>
    <test_case name="complex_nested_structure">
        <input>
            <![CDATA[
            struct Complex {
                struct {
                    int x;
                    char y;
                } anonymous;
                union {
                    int a;
                    struct {
                        unsigned int b1 : 3;
                        unsigned int : 2;
                        unsigned int b2 : 5;
                    } bits;
                } u;
                int arr[2][3];
            };
            ]]>
        </input>
        <expected_ast>
            <!-- AST 結構驗證 -->
        </expected_ast>
        <expected_flattened>
            <!-- 展平結果驗證 -->
        </expected_flattened>
    </test_case>
</v7_test_suite>
```

### 4.3 效能測試
```python
class TestPerformance:
    """效能測試"""
    
    def test_large_structure_parsing(self):
        """測試大型結構解析效能"""
        pass
    
    def test_complex_flattening(self):
        """測試複雜結構展平效能"""
        pass
    
    def test_gui_rendering(self):
        """測試 GUI 渲染效能"""
        pass
```

## 5. 開發環境與工具

### 5.1 開發分支策略
```
main
 ├─ v7_ast_refactor (AST 重構)
 ├─ v7_flattening (展平算法)
 ├─ v7_gui_integration (GUI 整合)
 └─ v7_integration (最終整合)
```

### 5.2 工具與依賴
- **Python 3.8+**：核心開發語言
- **pytest**：測試框架
- **mypy**：型別檢查
- **black**：程式碼格式化
- **flake8**：程式碼品質檢查
- **tkinter**：GUI 框架

### 5.3 CI/CD 整合
```yaml
# .github/workflows/v7_tests.yml
name: v7 Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.8
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest tests/v7/
      - name: Run type checking
        run: mypy src/v7/
      - name: Run linting
        run: flake8 src/v7/
```

## 6. 風險管理與品質保證

### 6.1 技術風險
- **複雜度風險**：巢狀結構的複雜性可能導致效能問題
  - *緩解策略*：建立效能基準，實作漸進式優化
- **相容性風險**：新 AST 結構可能影響現有功能
  - *緩解策略*：建立向後相容層，逐步遷移

### 6.2 品質保證
- **程式碼審查**：所有變更需要至少一名審查者
- **測試覆蓋率**：目標 90% 以上的測試覆蓋率
- **文件同步**：程式碼變更時同步更新文件
- **效能監控**：建立效能基準和監控機制

### 6.3 發布策略
- **Alpha 版本**：內部測試和驗證
- **Beta 版本**：有限用戶測試
- **RC 版本**：候選發布版本
- **正式版本**：穩定發布版本

## 7. 成功標準

### 7.1 功能標準
- [ ] 支援所有 v5 功能（巢狀 struct/union/array、匿名結構、位元欄位）
- [ ] AST 解析效能提升 50% 以上
- [ ] 展平算法正確性 100%
- [ ] GUI 響應時間 < 100ms

### 7.2 品質標準
- [ ] 測試覆蓋率 > 90%
- [ ] 程式碼品質檢查通過
- [ ] 型別檢查通過
- [ ] 文件完整性 > 95%

### 7.3 效能標準
- [ ] 大型結構（>1000 節點）解析時間 < 5 秒
- [ ] GUI 渲染時間 < 200ms
- [ ] 記憶體使用量 < 100MB
- [ ] 啟動時間 < 3 秒

## 8. 後續規劃

### 8.1 v7.1 版本
- 進階搜尋和篩選功能
- 自訂顯示主題
- 匯出功能增強

### 8.2 v7.2 版本
- 即時編輯功能
- 版本控制整合
- 協作功能

### 8.3 v8 版本
- 多語言支援
- 無障礙功能
- 雲端同步

---

> 本文件為 v7 開發的詳細實作規劃，基於 v6 GUI 架構和 v5 巢狀結構支援。
> 開發過程中將持續更新進度和調整規劃。 