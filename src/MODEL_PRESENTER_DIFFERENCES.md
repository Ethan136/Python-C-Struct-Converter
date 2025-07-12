# StructModel vs StructPresenter: 功能差異與職責分工

## 概述

在 MVP (Model-View-Presenter) 架構中，`StructModel` 和 `StructPresenter` 扮演不同的角色，各自負責特定的功能領域。本文檔詳細說明兩者的功能差異、職責分工和協作方式。

## 架構層級

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│    View     │◄──►│  Presenter   │◄──►│   Model     │
│  (GUI)      │    │ (Logic)      │    │ (Business)  │
└─────────────┘    └──────────────┘    └─────────────┘
```

## StructModel (模型層)

### 🎯 **核心職責**
- **純業務邏輯**：處理 C++ struct 的解析和記憶體佈局計算
- **資料處理**：解析十六進制資料並轉換為結構化資料
- **無 UI 依賴**：完全獨立於使用者介面

### 📋 **主要功能**

#### 1. **Struct 定義解析**
```python
def parse_struct_definition(file_content):
    """解析 C++ struct 定義"""
    # 使用正則表達式提取 struct 名稱和成員
    # 返回 struct_name 和 members 列表
```

#### 2. **記憶體佈局計算**
```python
def calculate_layout(members):
    """計算 struct 的記憶體佈局，包含對齊填充"""
    # 計算每個成員的偏移量
    # 處理記憶體對齊和填充
    # 返回 layout, total_size, max_alignment
```

#### 3. **十六進制資料解析**
```python
def parse_hex_data(self, hex_data, byte_order):
    """解析十六進制資料為結構化資料"""
    # 將 hex 字串轉換為 bytes
    # 根據佈局解析每個成員
    # 返回解析後的數值列表
```

### 🔧 **技術特點**
- **純函數式設計**：大部分方法都是純函數
- **資料驅動**：基於 `TYPE_INFO` 字典進行類型處理
- **錯誤處理**：拋出異常讓上層處理
- **無狀態操作**：不保存 UI 相關狀態

## StructPresenter (展示層)

### 🎯 **核心職責**
- **應用邏輯**：協調 Model 和 View 之間的互動
- **使用者事件處理**：處理來自 View 的使用者操作
- **資料轉換**：將使用者輸入轉換為 Model 可處理的格式
- **錯誤處理**：處理並顯示錯誤訊息給使用者

### 📋 **主要功能**

#### 1. **檔案瀏覽與載入**
```python
def browse_file(self):
    """處理檔案瀏覽和載入邏輯"""
    # 顯示檔案對話框
    # 呼叫 model.load_struct_from_file()
    # 更新 view 顯示
    # 重建 hex 輸入網格
```

#### 2. **輸入驗證與轉換**
```python
def parse_hex_data(self):
    """處理十六進制輸入的驗證和轉換"""
    # 驗證輸入格式
    # 轉換使用者輸入為記憶體格式
    # 處理位元組順序
    # 呼叫 model.parse_hex_data()
```

#### 3. **UI 狀態管理**
```python
def on_unit_size_change(self, *args):
    """處理單位大小變更"""
    # 重建 hex 輸入網格
    # 更新 UI 狀態
```

### 🔧 **技術特點**
- **事件驅動**：響應 View 的使用者事件
- **狀態管理**：管理 UI 狀態和資料流
- **錯誤處理**：捕獲異常並顯示使用者友好的錯誤訊息
- **資料轉換**：在 Model 和 View 之間轉換資料格式

## 功能對比表

| 功能領域 | StructModel | StructPresenter |
|---------|-------------|-----------------|
| **檔案解析** | ✅ 解析 C++ struct 語法 | ❌ 不直接解析檔案 |
| **記憶體計算** | ✅ 計算佈局、對齊、填充 | ❌ 不進行計算 |
| **資料解析** | ✅ 解析 hex 為結構化資料 | ❌ 不直接解析資料 |
| **輸入驗證** | ❌ 不驗證使用者輸入 | ✅ 驗證 hex 格式、範圍 |
| **UI 互動** | ❌ 無 UI 依賴 | ✅ 處理檔案對話框、錯誤顯示 |
| **狀態管理** | ❌ 無 UI 狀態 | ✅ 管理按鈕狀態、網格重建 |
| **錯誤處理** | ❌ 拋出異常 | ✅ 顯示使用者友好錯誤訊息 |
| **資料轉換** | ❌ 純資料處理 | ✅ 輸入格式轉換、位元組順序處理 |

## 協作流程

### 1. **檔案載入流程**
```
View (Browse Button) 
    ↓
Presenter.browse_file()
    ↓
Model.load_struct_from_file()
    ↓
Presenter 更新 View 顯示
```

### 2. **資料解析流程**
```
View (Parse Button)
    ↓
Presenter.parse_hex_data()
    ↓ (輸入驗證與轉換)
Model.parse_hex_data()
    ↓
Presenter 更新 View 結果
```

## 設計原則

### StructModel 原則
- **單一職責**：只負責 struct 解析和資料處理
- **純粹性**：不依賴外部狀態或 UI
- **可測試性**：每個方法都可以獨立測試
- **可重用性**：可以在不同的 UI 框架中重用

### StructPresenter 原則
- **協調者**：協調 Model 和 View 的互動
- **轉換器**：轉換資料格式和處理使用者輸入
- **錯誤處理者**：提供使用者友好的錯誤處理
- **狀態管理者**：管理 UI 狀態和資料流

## 擴展性考量

### 新增功能時的職責分配

#### 新增 struct 類型支援
- **Model**: 擴展 `TYPE_INFO` 字典，新增解析邏輯
- **Presenter**: 無需修改（除非需要特殊 UI 處理）

#### 新增輸入格式支援
- **Model**: 新增解析方法
- **Presenter**: 新增輸入驗證和轉換邏輯

#### 新增輸出格式支援
- **Model**: 新增格式化方法
- **Presenter**: 新增輸出處理邏輯

## 總結

`StructModel` 和 `StructPresenter` 在 MVP 架構中扮演截然不同的角色：

- **StructModel** 是純業務邏輯層，專注於資料處理和計算
- **StructPresenter** 是應用邏輯層，專注於使用者互動和狀態管理

這種分離確保了程式碼的可維護性、可測試性和可重用性，符合 SOLID 原則中的單一職責原則。 