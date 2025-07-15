# Examples Directory

本目錄用於存放 C/C++ struct 範例檔案，協助使用者快速測試與理解工具功能。

## 目前範例
- `example.h`：包含 bitfield、padding 等常見 struct 宣告，適合用於 GUI 的 .h 檔案載入測試。

## 範例檔案格式
- 檔案需為標準 C/C++ header 格式（副檔名 .h）
 - 支援 struct 與 union 宣告
- 支援 bitfield 宣告（如 `int a : 1;`）
- 支援多型別混合、padding、自動對齊

## 如何擴充範例
1. 新增一個 .h 檔案，內容為合法的 struct 宣告
2. 可加入不同型別、bitfield、padding 測試
3. 檔案命名建議以功能或測試重點命名（如 `bitfield_example.h`, `padding_test.h`）

## 用途
- 測試 GUI 的 .h 檔案載入功能
- 驗證 struct 解析、bitfield、padding 等機制
- 作為教學與說明範例 