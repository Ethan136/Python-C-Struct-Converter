# V4 Refactor 規劃（含細節任務）

## 0. 目標
- 全面優化專案結構、可維護性、可讀性
- 分析現有肥大、重複、legacy code，規劃分割、合併、刪除

## 1. 肥大模組/函式分割建議
- src/view/struct_view.py（34KB, 762行）
  - [ ] **GUI 主框架/Tab 控制邏輯**
    - 拆出 MainView 或 TabController class，專責 tab 切換、主視窗初始化
    - 需修改：StructView.__init__、_create_tab_control、main.py 的 view 初始化
  - [ ] **共用元件**
    - 將 create_member_treeview、create_scrollable_tab_frame 等 helper 移到 src/view/widgets.py
    - 需修改：struct_view.py 內所有呼叫這些 helper 的地方
    - 將 Treeview/Frame/Button group 等重複元件封裝 class
  - [ ] **事件處理/回呼**
    - 拆出 event_handlers.py，集中管理所有 callback、事件綁定
    - 需修改：所有 _on_xxx_change、_add_member、_delete_member、_update_member_xxx、_move_member_xxx、_copy_member 等方法
  - [ ] **檔案結構調整**
    - main_view.py（主框架/Tab 控制）、widgets.py（Treeview、scrollable frame、共用元件）、event_handlers.py（事件/回呼）、struct_view.py 僅保留高階組裝

- src/model/struct_model.py（21KB, 523行）
  - [ ] **結構體解析/對齊邏輯**
    - 拆出 align.py，專責 C/C++ 對齊、padding 計算
    - 需修改：calculate_layout、LayoutCalculator class 相關邏輯
  - [ ] **型別推斷/驗證**
    - 拆出 type_infer.py，專責型別推斷、驗證、合法性檢查
    - 需修改：_convert_to_cpp_members、_convert_legacy_member、validate_manual_struct
  - [ ] **匯出/序列化**
    - 拆出 exporter.py，專責 .h 檔匯出、序列化
    - 需修改：export_manual_struct_to_h
  - [ ] **檔案結構調整**
    - struct_model.py（高階 API）、align.py、type_infer.py、exporter.py、utils.py

- tests/test_struct_view.py（45KB, 928行）
  - [ ] **依功能分檔**
    - 拆分為 test_struct_view_basic.py, test_struct_view_hex.py, test_struct_view_scroll.py, test_struct_view_member_table.py, test_struct_view_debug.py
    - 需修改：將現有測試依功能分類搬移

- tests/test_struct_model.py（40KB, 989行）
  - [ ] **依功能分檔**
    - 拆分為 test_struct_model_basic.py, test_struct_model_align.py, test_struct_model_type.py, test_struct_model_export.py
    - 需修改：將現有測試依功能分類搬移

## 2. 可合併模組/函式建議
- src/model/input_field_processor.py（179行）
  - [ ] 若僅被 struct_model.py 使用，直接合併進 struct_model.py，或重構為 model/utils.py
  - [ ] 若有多處使用，統一 API 並加型別註解
  - 需修改：import input_field_processor 的所有地方
- src/presenter/struct_presenter.py（231行）
  - [ ] 檢查是否有多個 presenter（如 future tab），可合併為 BasePresenter
  - [ ] 統一 interface，減少重複 callback
  - 需修改：main.py、struct_view.py、所有 presenter 相關呼叫
- config 目錄
  - [ ] ui_strings.py/xml 只保留一種格式，建議用 json/yaml 統一
  - [ ] 未被 import 的設定檔直接刪除
  - 需修改：main.py、presenter、view 相關 get_string/load_ui_strings 呼叫

## 3. 可刪除 legacy code
- [ ] 檢查 src/view/struct_view.py、src/model/struct_model.py 內部註解掉的舊邏輯、未使用 helper，搜尋 # old、# legacy、註解掉的 function，確認無用後刪除
- [ ] 移除未被呼叫的 helper function
- [ ] tests/ 目錄下 v2/v3 已棄用的測試檔案（如 test_struct_view_v3.py, test_struct_model_v3.py）若已無人維護且無新功能覆蓋，直接刪除
- [ ] config/ 目錄下未被 import 的設定檔，用 grep 檢查 import，未被 import 的設定檔刪除
- [ ] 其他 __pycache__、未被 import 的 .py，全專案清理 __pycache__，用 flake8/vulture 等工具找出未被 import 的 .py 檔

## 4. 其他優化建議
- [ ] 增加型別註解/type hint：逐步為所有 public function、class method 增加 type hint
- [ ] 增加 docstring、模組說明：每個 class、function、module 增加 docstring，說明用途、參數、回傳值
- [ ] 測試覆蓋率報告與 dead code 檢查：使用 pytest-cov 產生覆蓋率報告，使用 vulture、flake8 檢查 dead code、未使用變數
- [ ] 建立 widgets/、utils/ 共用模組：建立 src/view/widgets.py、src/model/utils.py，集中共用元件與工具函式，未來新功能優先考慮共用元件設計

---

> 本文件為 v4 架構優化前的初步規劃與細節分解，後續可依實際重構進度細化每一項目。 