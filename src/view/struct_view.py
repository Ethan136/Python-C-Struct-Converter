try:
    import tkinter as tk
    from tkinter import ttk
    from tkinter import filedialog, messagebox
except Exception:
    class _DummyTkModule:
        class Tk: ...
        class Label: ...
        class LabelFrame: ...
        class Frame: ...
        class Entry: ...
        class Scrollbar: ...
        END = "end"
    tk = _DummyTkModule()

    class _DummyTtkModule:
        class Treeview: ...
        class Notebook: ...
        class Frame: ...
        class Button: ...
        class Entry: ...
        class Label: ...
        class Combobox: ...
        class LabelFrame: ...
    ttk = _DummyTtkModule()

    class _DummyMessagebox:
        def showwarning(*args, **kwargs):
            return None
        def showerror(*args, **kwargs):
            return None
        def askyesno(*args, **kwargs):
            return False
    messagebox = _DummyMessagebox()

    class _DummyFileDialog:
        def askopenfilename(*args, **kwargs):
            return None
    filedialog = _DummyFileDialog()

from .virtual_tree import VirtualTreeview
# from src.config import get_string
from src.export.csv_export import DefaultCsvExportService, CsvExportOptions, build_parsed_model_from_struct
from src.model.struct_model import StructModel
import time

class _DummyVirtual:
    def __init__(self, tree):
        self.tree = tree
    def set_nodes(self, nodes):
        pass
    def _on_scroll(self, event):
        return "break"
    def get_global_index(self, iid):
        return -1
    def reorder_nodes(self, parent_id, from_idx, to_idx):
        pass

# --- Treeview 巢狀遞迴插入與互動 helper ---
MEMBER_TREEVIEW_COLUMNS = [
    {"name": "name", "title": "欄位名稱", "width": 120},
    {"name": "value", "title": "值", "width": 100},
    {"name": "hex_value", "title": "Hex Value", "width": 100},
    {"name": "hex_raw", "title": "Hex Raw", "width": 150},
]

# Columns for struct layout treeviews
LAYOUT_TREEVIEW_COLUMNS = [
    {"name": "name", "title": "欄位名稱", "width": 120},
    {"name": "type", "title": "型別", "width": 100},
    {"name": "offset", "title": "Offset", "width": 80},
    {"name": "size", "title": "Size", "width": 80},
    {"name": "bit_offset", "title": "bit_offset", "width": 80},
    {"name": "bit_size", "title": "bit_size", "width": 80},
    {"name": "is_bitfield", "title": "is_bitfield", "width": 80},
]

def create_member_treeview(parent):
    all_columns = MEMBER_TREEVIEW_COLUMNS
    col_names = tuple(c["name"] for c in all_columns)
    tree = ttk.Treeview(
        parent,
        columns=col_names,
        show="headings",
        height=6,
        selectmode="extended"  # 支援多選
    )
    for c in all_columns:
        tree.heading(c["name"], text=c["title"])
        tree.column(c["name"], width=c["width"], stretch=False)
    tree["displaycolumns"] = col_names
    tree.pack(fill="x")
    return tree


def create_layout_treeview(parent, yscrollcommand=None):
    """Create a Treeview for struct layout display."""
    all_columns = LAYOUT_TREEVIEW_COLUMNS
    col_names = tuple(c["name"] for c in all_columns)
    tree = ttk.Treeview(
        parent,
        columns=col_names,
        show="headings",
        height=10,
        yscrollcommand=yscrollcommand,
    )
    for c in all_columns:
        tree.heading(c["name"], text=c["title"])
        tree.column(c["name"], width=c["width"], stretch=False)
    tree["displaycolumns"] = col_names
    tree.pack(side="left", fill="both", expand=True)
    return tree

def update_treeview_by_context(tree, context):
    # 展開/收合
    expanded = set(context.get("expanded_nodes", []))
    for item in tree.get_children(""):
        _update_treeview_expand_recursive(tree, item, expanded)
    # 高亮選取
    selected = context.get("selected_node")
    selected_nodes = context.get("selected_nodes")
    # 取得所有現有 id
    def collect_all_ids(tree, parent=""):
        ids = list(tree.get_children(parent))
        for i in list(ids):
            ids.extend(collect_all_ids(tree, i))
        return ids
    all_ids = set(collect_all_ids(tree, ""))
    # 僅在型別正確時才呼叫 selection_set，且只選取存在的 id
    if isinstance(selected_nodes, (list, tuple)) and selected_nodes:
        filtered = [i for i in selected_nodes if i in all_ids]
        if filtered:
            tree.selection_set(filtered)
        else:
            tree.selection_remove(tree.selection())
    elif isinstance(selected, str) and selected and selected in all_ids:
        tree.selection_set(selected)
    else:
        tree.selection_remove(tree.selection())

def _update_treeview_expand_recursive(tree, item_id, expanded):
    tree.item(item_id, open=(item_id in expanded))
    for child in tree.get_children(item_id):
        _update_treeview_expand_recursive(tree, child, expanded)

def create_scrollable_tab_frame(parent):
    canvas = tk.Canvas(parent, borderwidth=0, highlightthickness=0)
    vscroll = tk.Scrollbar(parent, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas)
    scrollable_frame_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=vscroll.set)
    canvas.pack(side="left", fill="both", expand=True)
    vscroll.pack(side="right", fill="y")
    def _on_frame_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))
    scrollable_frame.bind("<Configure>", _on_frame_configure)
    # 允許滑鼠滾輪
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    canvas.bind_all("<MouseWheel>", _on_mousewheel)
    return canvas, scrollable_frame

class StructView(tk.Tk):
    def __init__(self, presenter=None, enable_virtual=False, virtual_page_size=100):
        super().__init__()
        self._member_table_refresh_count = 0
        self._hex_grid_refresh_count = 0
        self._treeview_refresh_count = 0
        self.presenter = presenter
        self.enable_virtual = enable_virtual
        self._virtual_page_size = virtual_page_size
        self.title("C Struct GUI")
        self.geometry("1200x800")
        self._debug_auto_refresh_id = None
        self._debug_auto_refresh_enabled = None
        self._debug_auto_refresh_interval = None
        # 新增：儲存載入檔案的 total_size，供單位切換時使用
        self.current_file_total_size = 0
        self._create_tab_control()
        # Treeview 事件綁定
        if hasattr(self, "member_tree"):
            self._bind_member_tree_events()
        # 新增 presenter/view 綁定與初始顯示
        self._init_presenter_view_binding()

    def get_member_table_refresh_count(self):
        return self._member_table_refresh_count
    def get_hex_grid_refresh_count(self):
        return self._hex_grid_refresh_count
    def get_treeview_refresh_count(self):
        return self._treeview_refresh_count

    def _create_tab_control(self):
        self.tab_control = ttk.Notebook(self)
        self.tab_file = ttk.Frame(self.tab_control)
        self.tab_manual = ttk.Frame(self.tab_control)
        self.tab_control.add(self.tab_file, text="載入.H檔")
        self.tab_control.add(self.tab_manual, text="手動設定資料結構")
        self.tab_control.pack(expand=1, fill="both")

        # 在載入.H檔Tab建立UI
        self._create_file_tab_frame(self.tab_file)
        # 在手動設定Tab建立UI
        self._create_manual_struct_frame(self.tab_manual)
        # 顯示 Debug tab
        self._create_debug_tab()

    def _create_file_tab_frame(self, parent):
        _, main_frame = create_scrollable_tab_frame(parent)
        # 單位選擇與 endianness
        control_frame = tk.Frame(main_frame)
        control_frame.pack(fill="x", pady=(5, 2))
        self.file_control_frame = control_frame  # 供測試直接存取
        tk.Label(control_frame, text="單位大小：").pack(side=tk.LEFT)
        self.unit_size_var = tk.StringVar(value="1 Byte")
        unit_options = ["1 Byte", "4 Bytes", "8 Bytes"]
        self.unit_menu = tk.OptionMenu(control_frame, self.unit_size_var, *unit_options, command=lambda _: self._on_unit_size_change())
        self.unit_menu.pack(side=tk.LEFT)
        tk.Label(control_frame, text="  Endianness：").pack(side=tk.LEFT)
        self.endian_var = tk.StringVar(value="Little Endian")
        endian_options = ["Little Endian", "Big Endian"]
        self.endian_menu = tk.OptionMenu(control_frame, self.endian_var, *endian_options, command=lambda _: self._on_endianness_change())
        self.endian_menu.pack(side=tk.LEFT)
        # 顯示模式切換
        tk.Label(control_frame, text="  顯示模式：").pack(side=tk.LEFT)
        self.display_mode_var = tk.StringVar(value="tree")
        display_mode_options = ["tree", "flat"]
        self.display_mode_menu = tk.OptionMenu(control_frame, self.display_mode_var, *display_mode_options, command=self._on_display_mode_change)
        self.display_mode_menu.pack(side=tk.LEFT)
        # Target Struct 選擇器（v17）
        tk.Label(control_frame, text="  Target Struct：").pack(side=tk.LEFT)
        self.target_struct_var = tk.StringVar(value="")
        try:
            self.target_struct_combo = ttk.Combobox(control_frame, textvariable=self.target_struct_var, width=18, state="readonly")
        except Exception:
            # 在無 ttk 時 fallback 使用 Entry
            self.target_struct_combo = tk.Entry(control_frame, textvariable=self.target_struct_var, width=18)
        self.target_struct_combo.pack(side=tk.LEFT)
        # 綁定選擇事件
        def _on_target_struct_change(*_):
            name = self.target_struct_var.get().strip()
            if not name or not self.presenter or not hasattr(self.presenter, 'set_import_target_struct'):
                return
            try:
                self.presenter.set_import_target_struct(name)
                # 刷新顯示
                if hasattr(self.presenter, 'get_display_nodes') and hasattr(self.presenter, 'context'):
                    nodes = self.presenter.get_display_nodes(self.presenter.context.get('display_mode', 'tree'))
                    self.update_display(nodes, self.presenter.context)
                # 依照新選擇的 struct/union 更新 Struct Layout 與 hex 輸入格數量
                try:
                    struct_name = getattr(self.presenter.model, 'struct_name', None)
                    layout = getattr(self.presenter.model, 'layout', None)
                    total_size = getattr(self.presenter.model, 'total_size', None)
                    struct_align = getattr(self.presenter.model, 'struct_align', None)
                    if struct_name is not None and layout is not None and total_size is not None and struct_align is not None:
                        self.show_struct_layout(struct_name, layout, total_size, struct_align)
                        # 記錄並依目前單位大小重建 hex grid
                        self.current_file_total_size = total_size
                        try:
                            unit_size = self.get_selected_unit_size()
                        except Exception:
                            unit_size = 1
                        self.rebuild_hex_grid(total_size or 0, unit_size)
                except Exception:
                    pass
            except Exception:
                pass
        try:
            self.target_struct_combo.bind('<<ComboboxSelected>>', lambda e: _on_target_struct_change())
        except Exception:
            # fallback for Entry：Enter 觸發
            self.target_struct_combo.bind('<Return>', lambda e: _on_target_struct_change())
        # GUI 版本切換
        tk.Label(control_frame, text="  GUI 版本：").pack(side=tk.LEFT)
        self.gui_version_var = tk.StringVar(value="legacy")
        gui_version_options = ["legacy", "modern"]
        self.gui_version_menu = tk.OptionMenu(control_frame, self.gui_version_var, *gui_version_options, command=self._on_gui_version_change)
        self.gui_version_menu.pack(side=tk.LEFT)
        # 搜尋輸入框
        tk.Label(control_frame, text="  搜尋：").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(control_frame, textvariable=self.search_var, width=16)
        self.search_entry.pack(side=tk.LEFT)
        self.search_entry.bind('<KeyRelease>', self._on_search_entry_change)
        # Filter 輸入框
        tk.Label(control_frame, text="  Filter：").pack(side=tk.LEFT)
        self.filter_var = tk.StringVar()
        self.filter_entry = tk.Entry(control_frame, textvariable=self.filter_var, width=16)
        self.filter_entry.pack(side=tk.LEFT)
        self.filter_entry.bind('<KeyRelease>', self._on_filter_entry_change)
        # 展開全部/收合全部按鈕
        self.expand_all_btn = tk.Button(control_frame, text="展開全部", command=self._on_expand_all)
        self.expand_all_btn.pack(side=tk.LEFT, padx=2)
        self.collapse_all_btn = tk.Button(control_frame, text="收合全部", command=self._on_collapse_all)
        self.collapse_all_btn.pack(side=tk.LEFT, padx=2)
        # 批次操作按鈕
        self.batch_expand_btn = tk.Button(control_frame, text="展開選取", command=self._on_batch_expand)
        self.batch_expand_btn.pack(side=tk.LEFT, padx=2)
        self.batch_collapse_btn = tk.Button(control_frame, text="收合選取", command=self._on_batch_collapse)
        self.batch_collapse_btn.pack(side=tk.LEFT, padx=2)
        # 批次刪除按鈕
        self.batch_delete_btn = tk.Button(control_frame, text="批次刪除", command=self._on_batch_delete)
        self.batch_delete_btn.pack(side=tk.LEFT, padx=2)
        # 32-bit 模式切換
        self.file_pointer32_var = tk.BooleanVar(value=False)
        tk.Checkbutton(control_frame, text="32-bit 模式", variable=self.file_pointer32_var, command=lambda: self._on_pointer_mode_toggle(self.file_pointer32_var.get())).pack(side=tk.LEFT, padx=6)
        # 檔案選擇按鈕
        tk.Button(main_frame, text="選擇 .h 檔", command=self._on_browse_file).pack(anchor="w", pady=2)
        # 檔案路徑顯示
        self.file_path_label = tk.Label(main_frame, text="尚未選擇檔案")
        self.file_path_label.pack(anchor="w", pady=2)

        # hex grid 輸入區
        self.hex_entries = []
        self.hex_grid_frame = tk.Frame(main_frame)
        self.hex_grid_frame.pack(fill="x", pady=2)

        # 解析按鈕
        self.parse_button = tk.Button(main_frame, text="解析", command=self._on_parse_file, state="disabled")
        self.parse_button.pack(anchor="w", pady=5)

        # 匯出 CSV 按鈕（v19 GUI 整合）
        self.export_csv_button = tk.Button(main_frame, text="匯出 CSV", command=self._on_export_csv, state="disabled")
        self.export_csv_button.pack(anchor="w", pady=2)

        # struct member value 顯示區
        member_frame = tk.LabelFrame(main_frame, text="Struct Member Value")
        member_frame.pack(fill="x", padx=2, pady=2)
        self.member_tree = create_member_treeview(member_frame)
        self.legacy_tree = self.member_tree  # keep reference to legacy tree
        self._bind_member_tree_events()

        # debug bytes 顯示區
        debug_frame = tk.LabelFrame(main_frame, text="Debug Bytes")
        debug_frame.pack(fill="x", padx=2, pady=2)
        self.debug_text = tk.Text(debug_frame, height=4, width=100)
        self.debug_text.pack(fill="x")

        # struct layout 顯示區
        layout_frame = tk.LabelFrame(main_frame, text="Struct Layout")
        layout_frame.pack(fill="both", expand=True, padx=2, pady=2)
        # 新增 scroll bar
        layout_scrollbar = ttk.Scrollbar(layout_frame, orient="vertical")
        self.layout_tree = create_layout_treeview(layout_frame, yscrollcommand=layout_scrollbar.set)
        layout_scrollbar.config(command=self.layout_tree.yview)
        layout_scrollbar.pack(side="right", fill="y")

    def _create_manual_struct_frame(self, parent):
        _, scrollable_frame = create_scrollable_tab_frame(parent)

        # struct 名稱
        name_frame = tk.Frame(scrollable_frame)
        name_frame.pack(anchor="w", pady=5)
        tk.Label(name_frame, text="struct 名稱:").pack(side=tk.LEFT)
        self.struct_name_var = tk.StringVar(value="MyStruct")
        tk.Entry(name_frame, textvariable=self.struct_name_var, width=20).pack(side=tk.LEFT)

        # 結構體大小（byte）
        size_frame = tk.Frame(scrollable_frame)
        size_frame.pack(anchor="w", pady=5)
        tk.Label(size_frame, text="結構體總大小 (bytes):").pack(side=tk.LEFT)
        self.size_var = tk.IntVar(value=0)
        tk.Entry(size_frame, textvariable=self.size_var, width=10).pack(side=tk.LEFT)

        # Member表格（移到 struct 名稱+size 下方）
        self.members = []
        self.member_frame = tk.Frame(scrollable_frame)
        self.member_frame.pack(fill="x", pady=5)

        # 新增Member按鈕
        tk.Button(scrollable_frame, text="新增Member", command=self._add_member).pack(anchor="w", pady=2)

        # 驗證提示
        self.validation_label = tk.Label(scrollable_frame, text="", fg="red")
        self.validation_label.pack(anchor="w", pady=2)

        # 匯出/儲存/重設按鈕
        btn_frame = tk.Frame(scrollable_frame)
        btn_frame.pack(anchor="w", pady=5)
        tk.Button(btn_frame, text="匯出為.H檔", command=self.on_export_manual_struct).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="重設", command=self._reset_manual_struct).pack(side=tk.LEFT, padx=2)

        # 單位選擇與 endianness（與 file tab 一致）
        manual_control_frame = tk.Frame(scrollable_frame)
        manual_control_frame.pack(fill="x", pady=(5, 2))
        tk.Label(manual_control_frame, text="單位大小：").pack(side=tk.LEFT)
        self.manual_unit_size_var = tk.StringVar(value="1 Byte")
        unit_options = ["1 Byte", "4 Bytes", "8 Bytes"]
        self.manual_unit_menu = tk.OptionMenu(manual_control_frame, self.manual_unit_size_var, *unit_options, command=lambda _: self._on_manual_unit_size_change())
        self.manual_unit_menu.pack(side=tk.LEFT)
        tk.Label(manual_control_frame, text="  Endianness：").pack(side=tk.LEFT)
        self.manual_endian_var = tk.StringVar(value="Little Endian")
        endian_options = ["Little Endian", "Big Endian"]
        self.manual_endian_menu = tk.OptionMenu(manual_control_frame, self.manual_endian_var, *endian_options, command=lambda _: self._on_manual_endianness_change())
        self.manual_endian_menu.pack(side=tk.LEFT)
        # 32-bit 模式切換（manual）
        self.manual_pointer32_var = tk.BooleanVar(value=False)
        tk.Checkbutton(manual_control_frame, text="32-bit 模式", variable=self.manual_pointer32_var, command=lambda: self._on_pointer_mode_toggle(self.manual_pointer32_var.get())).pack(side=tk.LEFT, padx=6)

        # hex grid 輸入區（與 file tab 一致，移到 member_frame 之後）
        self.manual_hex_entries = []
        self.manual_hex_grid_frame = tk.Frame(scrollable_frame)
        self.manual_hex_grid_frame.pack(fill="x", pady=2)

        # 解析按鈕
        self.manual_parse_button = tk.Button(scrollable_frame, text="解析", command=self._on_parse_manual_hex, state="normal")
        self.manual_parse_button.pack(anchor="w", pady=5)

        # struct member value 顯示區
        manual_member_frame = tk.LabelFrame(scrollable_frame, text="Struct Member Value")
        manual_member_frame.pack(fill="x", padx=2, pady=2)
        self.manual_member_tree = create_member_treeview(manual_member_frame)

        # debug bytes 顯示區
        manual_debug_frame = tk.LabelFrame(scrollable_frame, text="Debug Bytes")
        manual_debug_frame.pack(fill="x", padx=2, pady=2)
        self.manual_debug_text = tk.Text(manual_debug_frame, height=4, width=100)
        self.manual_debug_text.pack(fill="x")

        # 標準 struct layout Treeview（與 H 檔 tab 一致）
        layout_frame = tk.LabelFrame(scrollable_frame, text="Struct Layout (標準顯示)")
        layout_frame.pack(fill="both", expand=True, padx=2, pady=2)
        layout_scrollbar = ttk.Scrollbar(layout_frame, orient="vertical")
        self.manual_layout_tree = create_layout_treeview(layout_frame, yscrollcommand=layout_scrollbar.set)
        layout_scrollbar.config(command=self.manual_layout_tree.yview)
        layout_scrollbar.pack(side="right", fill="y")

        # 綁定 struct size/unit size 變更時自動重建 hex grid
        self.size_var.trace_add("write", lambda *_: self._rebuild_manual_hex_grid())
        self.manual_unit_size_var.trace_add("write", lambda *_: self._rebuild_manual_hex_grid())

        # 最後再呼叫 render member table
        self._render_member_table()
        self._rebuild_manual_hex_grid()

    def _get_type_options(self, is_bitfield=False):
        """根據是否為 bitfield 返回型別選項"""
        if is_bitfield:
            return ["int", "unsigned int", "char", "unsigned char"]
        else:
            return [
                "char", "unsigned char", "signed char",
                "short", "unsigned short",
                "int", "unsigned int",
                "long", "unsigned long",
                "long long", "unsigned long long",
                "float", "double", "bool"
            ]

    def _compute_member_layout(self, is_v3_format):
        """回傳 {name: size} 對應表供表格使用，改為呼叫 presenter，並過濾 padding。"""
        if not self.presenter:
            return {}
        member_data = [
            {
                "name": m.get("name", ""),
                "type": m.get("type", ""),
                "bit_size": m.get("bit_size", 0),
            }
            for m in self.members
        ]
        try:
            layout = self.presenter.compute_member_layout(member_data, self.size_var.get())
        except Exception as e:
            layout = []
        mapping = {}
        for item in layout:
            if item.get("type") != "padding":
                mapping[item["name"]] = str(item["size"])
        return mapping

    def _build_member_header(self, is_v3_format):
        tk.Label(self.member_frame, text="#", font=("Arial", 9, "bold")).grid(row=0, column=0, padx=2, pady=2)
        tk.Label(self.member_frame, text="成員名稱", font=("Arial", 9, "bold")).grid(row=0, column=1, padx=2, pady=2)
        tk.Label(self.member_frame, text="型別", font=("Arial", 9, "bold")).grid(row=0, column=2, padx=2, pady=2)
        tk.Label(self.member_frame, text="bit size", font=("Arial", 9, "bold")).grid(row=0, column=3, padx=2, pady=2)
        tk.Label(self.member_frame, text="size", font=("Arial", 9, "bold")).grid(row=0, column=4, padx=2, pady=2)
        tk.Label(self.member_frame, text="操作", font=("Arial", 9, "bold")).grid(row=0, column=5, padx=2, pady=2)

    def _render_member_row(self, idx, member, is_v3_format, name2size):
        row = idx + 1
        tk.Label(self.member_frame, text=str(idx + 1)).grid(row=row, column=0, padx=2, pady=1)

        name_var = tk.StringVar(value=member.get("name", ""))
        name_entry = tk.Entry(self.member_frame, textvariable=name_var, width=10)
        type_var = tk.StringVar(value=member.get("type", ""))
        type_options = self._get_type_options(member.get("bit_size", 0) > 0)
        type_menu = tk.OptionMenu(self.member_frame, type_var, *type_options)
        bit_var = tk.IntVar(value=member.get("bit_size", 0))
        bit_entry = tk.Entry(self.member_frame, textvariable=bit_var, width=6)
        size_val = name2size.get(member.get("name", ""), "-")
        size_label = tk.Label(self.member_frame, text=size_val)
        size_label.is_size_label = True
        op_frame = tk.Frame(self.member_frame)
        tk.Button(op_frame, text="刪除", command=lambda i=idx: self._delete_member(i), width=4).pack(side=tk.LEFT, padx=1)
        tk.Button(op_frame, text="上移", command=lambda i=idx: self._move_member_up(i), width=4).pack(side=tk.LEFT, padx=1)
        tk.Button(op_frame, text="下移", command=lambda i=idx: self._move_member_down(i), width=4).pack(side=tk.LEFT, padx=1)
        tk.Button(op_frame, text="複製", command=lambda i=idx: self._copy_member(i), width=4).pack(side=tk.LEFT, padx=1)
        name_var.trace_add("write", lambda *_, i=idx, v=name_var: self._update_member_name(i, v))
        type_var.trace_add("write", lambda *_, i=idx, v=type_var: self._update_member_type(i, v))
        bit_var.trace_add("write", lambda *_, i=idx, v=bit_var: self._update_member_bit(i, v))

        member["name_var"] = name_var
        member["type_var"] = type_var
        member["bit_var"] = bit_var

        # 記錄本 row 的 widgets
        self.member_entries.append((name_entry, type_menu, bit_entry, size_label, op_frame))

    def _render_member_table(self):
        self._member_table_refresh_count += 1
        members = self.members
        # 初始化 row widget cache
        if not hasattr(self, "_member_row_widgets") or self._member_row_widgets is None:
            self._member_row_widgets = {}
        row_widgets = self._member_row_widgets
        # 若 members 為空，清空所有 row widget
        if not members:
            for widgets in row_widgets.values():
                for w in widgets:
                    w.destroy()
            row_widgets.clear()
            for widget in self.member_frame.winfo_children():
                widget.destroy()
            tk.Label(self.member_frame, text="無成員資料", fg="gray").grid(row=0, column=0, columnspan=6, pady=10)
            self.member_entries = []
            self._update_manual_layout_tree()
            return
        # 若 header 不存在或被清空，重建 header
        if not hasattr(self, "_member_header_widgets") or self._member_header_widgets is None or not self._member_header_widgets:
            for widget in self.member_frame.winfo_children():
                widget.destroy()
            self._member_header_widgets = [
                tk.Label(self.member_frame, text="#", font=("Arial", 9, "bold")),
                tk.Label(self.member_frame, text="成員名稱", font=("Arial", 9, "bold")),
                tk.Label(self.member_frame, text="型別", font=("Arial", 9, "bold")),
                tk.Label(self.member_frame, text="bit size", font=("Arial", 9, "bold")),
                tk.Label(self.member_frame, text="size", font=("Arial", 9, "bold")),
                tk.Label(self.member_frame, text="操作", font=("Arial", 9, "bold")),
            ]
            for col, w in enumerate(self._member_header_widgets):
                w.grid(row=0, column=col, padx=2, pady=2)
        name2size = self._compute_member_layout(True)
        # 刪除多餘 row widget
        for idx in list(row_widgets.keys()):
            if idx >= len(members):
                for w in row_widgets[idx]:
                    w.destroy()
                del row_widgets[idx]
        # 更新/新增 row widget
        self.member_entries = []
        for idx, m in enumerate(members):
            if idx in row_widgets:
                widgets = row_widgets[idx]
                # 更新值
                widgets[0].config(text=str(idx + 1))  # row number
                widgets[1].delete(0, "end"); widgets[1].insert(0, m.get("name", ""))
                widgets[2].setvar(widgets[2].cget("textvariable"), m.get("type", ""))
                widgets[3].delete(0, "end"); widgets[3].insert(0, m.get("bit_size", 0))
                widgets[4].config(text=name2size.get(m.get("name", ""), "-"))
                # 操作按鈕無需更新
            else:
                # 新增 row widget
                name_var = tk.StringVar(value=m.get("name", ""))
                name_entry = tk.Entry(self.member_frame, textvariable=name_var, width=10, takefocus=1)
                type_var = tk.StringVar(value=m.get("type", ""))
                type_options = self._get_type_options(m.get("bit_size", 0) > 0)
                type_menu = tk.OptionMenu(self.member_frame, type_var, *type_options)
                type_menu.configure(takefocus=1)
                # 取得 OptionMenu 內部 Button
                type_menu_btn = None
                for child in type_menu.winfo_children():
                    if isinstance(child, tk.Button):
                        type_menu_btn = child
                        break
                if type_menu_btn:
                    type_menu_btn.configure(takefocus=1)
                bit_var = tk.IntVar(value=m.get("bit_size", 0))
                bit_entry = tk.Entry(self.member_frame, textvariable=bit_var, width=6, takefocus=1)
                # 強制讓 cget('takefocus') 回傳 int
                self._ensure_takefocus_int(name_entry)
                self._ensure_takefocus_int(type_menu)
                self._ensure_takefocus_int(bit_entry)
                size_val = name2size.get(m.get("name", ""), "-")
                size_label = tk.Label(self.member_frame, text=size_val)
                size_label.is_size_label = True
                op_frame = tk.Frame(self.member_frame)
                # 操作按鈕 takefocus=1
                del_btn = tk.Button(op_frame, text="刪除", command=lambda i=idx: self._delete_member(i), width=4, takefocus=1)
                up_btn = tk.Button(op_frame, text="上移", command=lambda i=idx: self._move_member_up(i), width=4, takefocus=1)
                down_btn = tk.Button(op_frame, text="下移", command=lambda i=idx: self._move_member_down(i), width=4, takefocus=1)
                copy_btn = tk.Button(op_frame, text="複製", command=lambda i=idx: self._copy_member(i), width=4, takefocus=1)
                del_btn.pack(side=tk.LEFT, padx=1)
                up_btn.pack(side=tk.LEFT, padx=1)
                down_btn.pack(side=tk.LEFT, padx=1)
                copy_btn.pack(side=tk.LEFT, padx=1)
                name_var.trace_add("write", lambda *_, i=idx, v=name_var: self._update_member_name(i, v))
                type_var.trace_add("write", lambda *_, i=idx, v=type_var: self._update_member_type(i, v))
                bit_var.trace_add("write", lambda *_, i=idx, v=bit_var: self._update_member_bit(i, v))
                widgets = [
                    tk.Label(self.member_frame, text=str(idx + 1)),
                    name_entry, type_menu, bit_entry, size_label, op_frame
                ]
                for col, w in enumerate(widgets):
                    w.grid(row=idx + 1, column=col, padx=2, pady=1)
                # 組合 tab order: Entry → OptionMenu.Button → bit_entry → del_btn → up_btn → down_btn → copy_btn
                focus_widgets = [name_entry]
                if type_menu_btn:
                    focus_widgets.append(type_menu_btn)
                focus_widgets.append(bit_entry)
                focus_widgets.extend([del_btn, up_btn, down_btn, copy_btn])
                for i, fw in enumerate(focus_widgets):
                    fw.configure(takefocus=1)
                    def on_tab(event, idx=i):
                        if idx + 1 < len(focus_widgets):
                            focus_widgets[idx + 1].focus_set()
                            return "break"
                    fw.bind("<Tab>", on_tab)
                row_widgets[idx] = widgets
            self.member_entries.append(tuple(row_widgets[idx][1:6]))
        self._update_manual_layout_tree()

    def _update_manual_layout_tree(self):
        # 計算 layout
        model = StructModel()
        try:
            member_data = [
                {"name": m.get("name", ""), "type": m.get("type", ""), "bit_size": m.get("bit_size", 0)}
                for m in self.members
            ]
            layout = model.calculate_manual_layout(member_data, self.size_var.get())
        except Exception:
            layout = []
        # 清空 treeview
        for i in self.manual_layout_tree.get_children():
            self.manual_layout_tree.delete(i)
        # 插入新資料
        for item in layout:
            bit_offset = item.get("bit_offset")
            bit_size = item.get("bit_size")
            bit_offset_str = str(bit_offset) if bit_offset is not None else "-"
            bit_size_str = str(bit_size) if bit_size is not None else "-"
            self.manual_layout_tree.insert("", "end", values=(
                item.get("name", ""),
                item.get("type", ""),
                item.get("offset", ""),
                item.get("size", ""),
                bit_offset_str,
                bit_size_str,
                str(item.get("is_bitfield", False))
            ))
    
    def _on_manual_struct_change(self):
        struct_data = self.get_manual_struct_definition()
        if self.presenter:
            result = self.presenter.on_manual_struct_change(struct_data)
            errors = result.get("errors")
            self.show_manual_struct_validation(errors)
        # 變更時即時更新下方標準 struct layout treeview
        self._update_manual_layout_tree()

    def _add_member(self):
        self.members.append({"name": "", "type": "int", "bit_size": 0})
        self._focus_new_member_idx = len(self.members) - 1  # 新增 index
        if self.presenter:
            self.presenter.invalidate_cache()
        self._render_member_table()
        self._on_manual_struct_change()

    def _delete_member(self, idx):
        del self.members[idx]
        if self.presenter:
            self.presenter.invalidate_cache()
        self._render_member_table()
        self._on_manual_struct_change()

    def _update_member_name(self, idx, var):
        self.members[idx]["name"] = var.get()
        if self.presenter:
            self.presenter.invalidate_cache()
        self._on_manual_struct_change()

    def _update_member_type(self, idx, var):
        self.members[idx]["type"] = var.get()
        if self.presenter:
            self.presenter.invalidate_cache()
        self._on_manual_struct_change()

    def _update_member_bit(self, idx, var):
        try:
            value = var.get()
            self.members[idx]["bit_size"] = int(value) if str(value).strip() else 0
        except Exception:
            self.members[idx]["bit_size"] = 0
        if self.presenter:
            self.presenter.invalidate_cache()
        self._on_manual_struct_change()

    def _move_member_up(self, idx):
        if idx > 0:
            self.members[idx-1], self.members[idx] = self.members[idx], self.members[idx-1]
            if self.presenter:
                self.presenter.invalidate_cache()
            self._render_member_table()
            self._on_manual_struct_change()

    def _move_member_down(self, idx):
        if idx < len(self.members) - 1:
            self.members[idx+1], self.members[idx] = self.members[idx], self.members[idx+1]
            if self.presenter:
                self.presenter.invalidate_cache()
            self._render_member_table()
            self._on_manual_struct_change()

    def _copy_member(self, idx):
        orig = self.members[idx]
        base_name = orig["name"]
        new_name = base_name + "_copy"
        existing_names = {m["name"] for m in self.members}
        count = 2
        while new_name in existing_names:
            new_name = f"{base_name}_copy{count}"
            count += 1
        new_m = {"name": new_name, "type": orig["type"], "bit_size": orig["bit_size"]}
        self.members.insert(idx+1, new_m)
        if self.presenter:
            self.presenter.invalidate_cache()
        self._render_member_table()
        self._on_manual_struct_change()

    def _reset_manual_struct(self):
        self.size_var.set(0)
        self.members.clear()
        if self.presenter:
            self.presenter.invalidate_cache()
        self._render_member_table()
        self.validation_label.config(text="")

    def get_manual_struct_definition(self):
        members_data = [
            {"name": m["name"], "type": m.get("type", ""), "bit_size": m["bit_size"]}
            for m in self.members
        ]
        try:
            total_size = self.size_var.get()
        except Exception:
            total_size = 0
        return {
            "struct_name": self.struct_name_var.get(),
            "total_size": total_size,
            "members": members_data
        }

    def show_manual_struct_validation(self, errors):
        # 先全部恢復預設顏色並移除 tooltip
        if hasattr(self, "member_entries"):
            for entry_tuple in self.member_entries:
                entry = entry_tuple[0]  # name_entry
                try:
                    entry.config(highlightbackground="systemWindowBackgroundColor", highlightcolor="systemWindowBackgroundColor")
                except Exception:
                    entry.config(highlightbackground="white", highlightcolor="white")
                # 移除舊 tooltip
                if hasattr(entry, '_tooltip'):
                    entry.unbind('<Enter>')
                    entry.unbind('<Leave>')
                    entry._tooltip.hide()
                    del entry._tooltip
        if errors:
            self.validation_label.config(text="; ".join(errors), fg="red")
            # 若有名稱相關錯誤，將對應 Entry 設紅框並掛載 tooltip
            if hasattr(self, "member_entries"):
                for idx, entry_tuple in enumerate(self.member_entries):
                    entry = entry_tuple[0]
                    name = self.members[idx].get("name", "")
                    for err in errors:
                        if name and name in err:
                            entry.config(highlightbackground="red", highlightcolor="red")
                            EntryTooltip(entry, err)
                        elif "名稱不可為空" in err and not name:
                            entry.config(highlightbackground="red", highlightcolor="red")
                            EntryTooltip(entry, err)
        else:
            # 改為呼叫 presenter 計算剩餘空間
            struct_data = self.get_manual_struct_definition()
            members = struct_data["members"]
            total_size = struct_data["total_size"]
            if self.presenter:
                remaining_bits, remaining_bytes = self.presenter.calculate_remaining_space(members, total_size)
            else:
                remaining_bits, remaining_bytes = 0, 0
            msg = "設定正確"
            msg += f"（剩餘可用空間：{remaining_bits} bits（{remaining_bytes} bytes））"
            self.validation_label.config(text=msg, fg="green")

    def on_export_manual_struct(self):
        if self.presenter:
            struct_data = self.get_manual_struct_definition()
            # 先調用 on_manual_struct_change 來設定 last_struct_data
            self.presenter.on_manual_struct_change(struct_data)
            if hasattr(self.presenter, "model") and self.presenter.model:
                self.presenter.model.set_manual_struct(struct_data["members"], struct_data["total_size"])
            result = self.presenter.on_export_manual_struct()
            h_content = result.get("h_content")
            self.show_exported_struct(h_content)

    def show_exported_struct(self, h_content):
        # 可彈出新視窗顯示匯出內容
        win = tk.Toplevel(self)
        win.title("匯出 .h 檔內容")
        txt = tk.Text(win, width=60, height=20)
        txt.pack()
        txt.insert("1.0", h_content)
        txt.config(state="disabled")

    def _on_browse_file(self):
        if self.presenter:
            result = self.presenter.browse_file()
            if result['type'] == 'ok':
                self.show_file_path(result['file_path'])
                self.show_struct_layout(result['struct_name'], result['layout'], result['total_size'], result['struct_align'])
                self.show_struct_debug(result['struct_content'])
                self.enable_parse_button()
                self.clear_results()
                # 記錄 total_size 供後續切換單位時使用
                self.current_file_total_size = result['total_size']
                self.rebuild_hex_grid(result['total_size'], 1)
            else:
                self.show_error('載入檔案錯誤', result['message'])
                self.disable_parse_button()
                self.clear_results()
                # 清除記錄的 total_size
                self.current_file_total_size = 0
                self.rebuild_hex_grid(0, 1)
                # 停用 CSV 匯出按鈕
                try:
                    if hasattr(self, "export_csv_button"):
                        self.export_csv_button.config(state="disabled")
                except Exception:
                    pass

    def _on_parse_file(self):
        if self.presenter:
            result = self.presenter.parse_hex_data()
            if result['type'] == 'ok':
                self.show_parsed_values(result['parsed_values'])
                self.show_debug_bytes(result['debug_lines'])
            else:
                self.show_error('解析錯誤', result['message'])

    def enable_parse_button(self):
        self.parse_button.config(state="normal")

    def disable_parse_button(self):
        self.parse_button.config(state="disabled")

    def show_struct_debug(self, content):
        # 在 struct_info_text 顯示原始 struct 內容
        # 全檔案移除 self.struct_info_text 相關操作，確保不再存取不存在的 Text 物件。
        pass

    def show_error(self, title, message):
        messagebox.showerror(title, message)

    def _populate_tree(self, tree, parsed_values):
        """Helper to display parsed values in a Treeview."""
        for item_id in tree.get_children():
            tree.delete(item_id)

        for item in parsed_values:
            value = item.get("value", "")
            try:
                hex_value = hex(int(value)) if value != "-" else "-"
            except Exception:
                hex_value = "-"

            hex_raw = item.get("hex_raw", "")
            if hex_raw and len(hex_raw) > 2:
                hex_raw = "｜".join(hex_raw[i:i+2] for i in range(0, len(hex_raw), 2))

            # 確保皆為字串
            name_str = str(item.get("name", ""))
            value_str = str(value) if value is not None else ""
            hex_value_str = str(hex_value) if hex_value is not None else ""
            hex_raw_str = str(hex_raw) if hex_raw is not None else ""
            tree.insert("", "end", values=(name_str, value_str, hex_value_str, hex_raw_str))

    def _show_debug_text(self, text_widget, debug_lines):
        """Helper to display debug lines in a Text widget."""
        text_widget.config(state="normal")
        text_widget.delete("1.0", tk.END)
        text_widget.insert("1.0", "\n".join(debug_lines) if debug_lines else "無 debug 資訊")
        text_widget.config(state="disabled")

    def show_parsed_values(self, parsed_values, byte_order_str=None):
        self._populate_tree(self.member_tree, parsed_values)

    def show_manual_parsed_values(self, parsed_values, byte_order_str=None):
        """顯示 MyStruct tab 的解析結果，與 file tab 的 show_parsed_values 一致"""
        self._populate_tree(self.manual_member_tree, parsed_values)

    def show_debug_bytes(self, debug_lines):
        self._show_debug_text(self.debug_text, debug_lines)


    def show_struct_member_debug(self, parsed_values, layout):
        # 顯示 struct layout 與欄位對應
        # 全檔案移除 self.struct_info_text 相關操作，確保不再存取不存在的 Text 物件。
        pass

    def show_file_path(self, file_path):
        self.file_path_label.config(text=f"檔案路徑: {file_path}")

    def show_struct_layout(self, struct_name, layout, total_size, struct_align):
        # 清空舊資料
        for i in self.layout_tree.get_children():
            self.layout_tree.delete(i)
        # 插入新資料
        for item in layout:
            bit_offset = item.get("bit_offset")
            bit_size = item.get("bit_size")
            # 無論是否 bitfield，都顯示 bit_offset/bit_size，若無則顯示 '-'
            bit_offset_str = str(bit_offset) if bit_offset is not None else "-"
            bit_size_str = str(bit_size) if bit_size is not None else "-"
            # 確保皆為字串
            name_str = str(item.get("name", ""))
            type_str = str(item.get("type", ""))
            offset_str = str(item.get("offset", ""))
            size_str = str(item.get("size", ""))
            is_bf_str = str(item.get("is_bitfield", False))
            self.layout_tree.insert("", "end", values=(
                name_str,
                type_str,
                offset_str,
                size_str,
                bit_offset_str,
                bit_size_str,
                is_bf_str
            ))
        # 啟用 CSV 匯出（當 layout 存在時）
        try:
            if hasattr(self, "export_csv_button"):
                self.export_csv_button.config(state="normal" if layout else "disabled")
        except Exception:
            pass

    def clear_results(self):
        for entry, _ in self.hex_entries:
            entry.delete(0, tk.END)
        for i in self.member_tree.get_children():
            self.member_tree.delete(i)
        self.debug_text.config(state="normal")
        self.debug_text.delete("1.0", tk.END)
        self.debug_text.config(state="disabled")
        # 全檔案移除 self.struct_info_text 相關操作，確保不再存取不存在的 Text 物件。
        pass

    def _on_export_csv(self):
        # 檢查 presenter/model 是否可用
        if not self.presenter or not hasattr(self.presenter, "model") or not self.presenter.model:
            try:
                messagebox.showerror("錯誤", "尚未載入 struct，無法匯出 CSV")
            except Exception:
                pass
            return
        try:
            # 選擇輸出檔案路徑
            try:
                from tkinter import filedialog as _fd
            except Exception:
                _fd = filedialog
            file_path = None
            try:
                file_path = _fd.asksaveasfilename(
                    title="選擇輸出 CSV 檔案",
                    defaultextension=".csv",
                    filetypes=(("CSV files", "*.csv"), ("All files", "*.*"))
                )
            except Exception:
                file_path = None
            if not file_path:
                return

            # 建構 parsed model
            parsed_model = build_parsed_model_from_struct(self.presenter.model)

            # 蒐集 hex 輸入（若有），供 value 計算
            hex_parts = []
            try:
                hex_parts = self.get_hex_input_parts()
            except Exception:
                hex_parts = []
            try:
                hex_input = "".join(raw for raw, _ in hex_parts).replace(" ", "")
            except Exception:
                hex_input = ""
            # 端序
            try:
                endian_str = self.get_selected_endianness()
                endianness = "little" if str(endian_str).lower().startswith("little") else "big"
            except Exception:
                endianness = "little"

            # 匯出選項（可擴充成 UI 設定）
            opts = CsvExportOptions(
                include_header=True,
                include_layout=True,
                include_values=True,
                endianness=endianness,
                hex_input=hex_input or None,
            )
            svc = DefaultCsvExportService()
            report = svc.export_to_csv(parsed_model, {"type": "file", "path": file_path}, opts)
            try:
                messagebox.showwarning(
                    "匯出完成",
                    f"已輸出 {report.records_written} 筆欄位到\n{report.file_path}\n耗時 {report.duration_ms} ms"
                )
            except Exception:
                pass
        except Exception as e:
            try:
                messagebox.showerror("匯出失敗", str(e))
            except Exception:
                pass

    def _on_unit_size_change(self):
        if self.presenter:
            result = self.presenter.on_unit_size_change()
            unit_size = result.get("unit_size")
            if unit_size is not None and hasattr(self, "rebuild_hex_grid"):
                # 優先使用 presenter.model 的 total_size，其次使用本地記錄的值
                try:
                    total_size = (
                        self.presenter.model.total_size
                        if self.presenter and hasattr(self.presenter, "model") and hasattr(self.presenter.model, "total_size")
                        else self.current_file_total_size
                    )
                except Exception:
                    total_size = self.current_file_total_size
                self.rebuild_hex_grid(total_size or 0, unit_size)

    def _on_endianness_change(self):
        if self.presenter:
            self.presenter.on_endianness_change()

    def get_selected_unit_size(self):
        return int(self.unit_size_var.get().split()[0])

    def get_selected_endianness(self):
        return self.endian_var.get()

    def get_selected_manual_unit_size(self):
        """取得 MyStruct tab 選擇的單位大小"""
        return int(self.manual_unit_size_var.get().split()[0])

    def _build_hex_grid(self, frame, entry_list, total_size, unit_size):
        self._hex_grid_refresh_count += 1
        # 增量更新 Entry widget
        if not hasattr(frame, "_hex_entry_widgets") or frame._hex_entry_widgets is None:
            frame._hex_entry_widgets = []
        widgets = frame._hex_entry_widgets
        # 計算應有的 box 數
        if total_size == 0:
            for w, _ in widgets:
                w.destroy()
            widgets.clear()
            entry_list.clear()
            return
        chars_per_box = unit_size * 2
        num_boxes = (total_size + unit_size - 1) // unit_size
        cols = max(1, 16 // unit_size)
        # 刪除多餘 Entry
        while len(widgets) > num_boxes:
            w, _ = widgets.pop()
            w.destroy()
        # 新增缺少的 Entry
        while len(widgets) < num_boxes:
            entry = tk.Entry(frame, font=("Courier", 10))
            widgets.append((entry, chars_per_box))
        # 更新/配置 Entry
        for i in range(num_boxes):
            if i == num_boxes - 1:
                remain_bytes = total_size - (unit_size * (num_boxes - 1))
                box_chars = remain_bytes * 2 if remain_bytes > 0 else chars_per_box
            else:
                box_chars = chars_per_box
            entry, _ = widgets[i]
            entry.config(width=box_chars + 2)
            entry.grid(row=i // cols, column=i % cols, padx=2, pady=2)
            # 綁定事件
            entry.bind("<KeyPress>", lambda e, length=box_chars: self._validate_input(e, length))
            entry.bind("<Key>", lambda e, length=box_chars: self._limit_input_length(e, length))
            widgets[i] = (entry, box_chars)
        # 更新 entry_list
        entry_list.clear()
        entry_list.extend(widgets[:num_boxes])
        frame._hex_entry_widgets = widgets[:num_boxes]

    def rebuild_hex_grid(self, total_size, unit_size):
        self._build_hex_grid(self.hex_grid_frame, self.hex_entries, total_size, unit_size)

    def get_hex_input_parts(self):
        return [(entry.get().strip(), expected_len) for entry, expected_len in self.hex_entries]

    def _validate_input(self, event, max_length):
        if event.keysym in ['BackSpace', 'Delete', 'Left', 'Right', 'Home', 'End', 'Tab']:
            return
        if event.state & 0x4:
            if event.keysym in ['a', 'c', 'v', 'x']:
                return
        char = event.char.lower()
        if char not in '0123456789abcdef':
            return "break"

    def _limit_input_length(self, event, max_length):
        widget = event.widget
        current_text = widget.get()
        if event.keysym in ['BackSpace', 'Delete', 'Left', 'Right', 'Home', 'End', 'Tab']:
            return
        if event.state & 0x4:
            if event.keysym in ['a', 'c', 'v', 'x']:
                return
        if len(current_text) >= max_length:
            return "break"

    def _rebuild_manual_hex_grid(self):
        try:
            total_size = int(self.size_var.get())
        except Exception:
            total_size = 0
        try:
            unit_size = self.get_selected_manual_unit_size()
        except Exception:
            unit_size = 1
        self._build_hex_grid(self.manual_hex_grid_frame, self.manual_hex_entries, total_size, unit_size)

    def _on_manual_unit_size_change(self):
        self._rebuild_manual_hex_grid()

    def _on_manual_endianness_change(self):
        pass  # 可根據需要擴充

    def _on_parse_manual_hex(self):
        hex_parts = [(entry.get().strip(), expected_len) for entry, expected_len in self.manual_hex_entries]
        if self.presenter and hasattr(self.presenter, 'parse_manual_hex_data'):
            struct_def = self.get_manual_struct_definition()
            struct_def['unit_size'] = self.get_selected_manual_unit_size()
            result = self.presenter.parse_manual_hex_data(hex_parts, struct_def, self.manual_endian_var.get())
            if result['type'] == 'ok':
                self.show_manual_parsed_values(result['parsed_values'])
            else:
                self.show_error('解析錯誤', result['message'])
        else:
            pass  # presenter/model 尚未實作解析

    def get_presenter_cache_stats(self):
        """取得 Presenter 的 layout cache hit/miss 統計（for debug/perf 分析用）"""
        if self.presenter and hasattr(self.presenter, "get_cache_stats"):
            return self.presenter.get_cache_stats()
        return (None, None)

    def _create_debug_tab(self):
        self.debug_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.debug_tab, text="Debug")
        self.debug_info_label = tk.Label(self.debug_tab, text="", anchor="w", justify="left", font=("Courier", 11))
        self.debug_info_label.pack(fill="x", padx=10, pady=10)

        # 控制元件區
        control_frame = tk.Frame(self.debug_tab)
        control_frame.pack(fill="x", padx=10, pady=5)

        # Undo/Redo 按鈕
        self.undo_btn = tk.Button(control_frame, text="Undo", command=self._on_undo)
        self.undo_btn.grid(row=0, column=0, padx=5)
        self.redo_btn = tk.Button(control_frame, text="Redo", command=self._on_redo)
        self.redo_btn.grid(row=0, column=1, padx=5)

        # 手動清空 cache 按鈕
        clear_btn = tk.Button(control_frame, text="手動清空 Cache", command=self._on_invalidate_cache)
        clear_btn.grid(row=0, column=2, padx=5)

        # LRU cache 容量 Spinbox
        tk.Label(control_frame, text="LRU 容量:").grid(row=0, column=3, padx=2)
        default_lru = 32
        if self.presenter and hasattr(self.presenter, "get_lru_cache_size"):
            try:
                default_lru = int(self.presenter.get_lru_cache_size())
            except Exception:
                default_lru = 32
        self.lru_size_var = tk.IntVar(value=default_lru)
        lru_spin = tk.Spinbox(control_frame, from_=0, to=128, width=5, textvariable=self.lru_size_var, command=self._on_set_lru_size)
        lru_spin.grid(row=0, column=4, padx=2)

        # 自動清空 Checkbox
        try:
            val = self.presenter.is_auto_cache_clear_enabled() if (self.presenter and hasattr(self.presenter, "is_auto_cache_clear_enabled")) else False
        except Exception:
            val = False
        self.auto_clear_var = tk.BooleanVar(value=bool(val))
        auto_clear_cb = tk.Checkbutton(control_frame, text="啟用自動清空", variable=self.auto_clear_var, command=self._on_toggle_auto_clear)
        auto_clear_cb.grid(row=0, column=5, padx=5)

        # 自動清空 interval Entry
        tk.Label(control_frame, text="Interval (秒):").grid(row=0, column=6, padx=2)
        self.auto_clear_interval_var = tk.DoubleVar(value=1.0)
        interval_entry = tk.Entry(control_frame, width=6, textvariable=self.auto_clear_interval_var)
        interval_entry.grid(row=0, column=7, padx=2)

        # --- 新增自動 refresh ---
        self._debug_auto_refresh_enabled = tk.BooleanVar(value=True)
        self._debug_auto_refresh_id = None
        self._debug_auto_refresh_interval = tk.DoubleVar(value=1.0)
        auto_refresh_cb = tk.Checkbutton(control_frame, text="自動 Refresh", variable=self._debug_auto_refresh_enabled, command=self._on_toggle_debug_auto_refresh)
        auto_refresh_cb.grid(row=0, column=9, padx=5)
        tk.Label(control_frame, text="Refresh Interval (秒):").grid(row=0, column=10, padx=2)
        auto_refresh_interval_entry = tk.Entry(control_frame, width=6, textvariable=self._debug_auto_refresh_interval)
        auto_refresh_interval_entry.grid(row=0, column=11, padx=2)
        self._debug_auto_refresh_interval.trace_add("write", lambda *_: self._on_debug_auto_refresh_interval_change())

        # 手動 refresh 按鈕
        refresh_btn = tk.Button(control_frame, text="Refresh", command=self.refresh_debug_info)
        refresh_btn.grid(row=0, column=8, padx=5)

        self.refresh_debug_info()
        self._start_debug_auto_refresh()

    def _start_debug_auto_refresh(self):
        if self._debug_auto_refresh_enabled.get():
            interval = self._debug_auto_refresh_interval.get()
            if interval <= 0:
                interval = 1.0
            self._debug_auto_refresh_id = self.after(int(interval * 1000), self._debug_auto_refresh_callback)

    def _stop_debug_auto_refresh(self):
        if self._debug_auto_refresh_id is not None:
            self.after_cancel(self._debug_auto_refresh_id)
            self._debug_auto_refresh_id = None

    def _debug_auto_refresh_callback(self):
        self.refresh_debug_info()
        self._start_debug_auto_refresh()

    def _on_toggle_debug_auto_refresh(self):
        if self._debug_auto_refresh_enabled.get():
            self._start_debug_auto_refresh()
        else:
            self._stop_debug_auto_refresh()

    def _on_debug_auto_refresh_interval_change(self):
        if self._debug_auto_refresh_enabled.get():
            self._stop_debug_auto_refresh()
            self._start_debug_auto_refresh()

    def destroy(self):
        self._stop_debug_auto_refresh()
        super().destroy()

    def _on_invalidate_cache(self):
        if self.presenter and hasattr(self.presenter, "invalidate_cache"):
            self.presenter.invalidate_cache()
        self.refresh_debug_info()

    def _on_set_lru_size(self):
        if self.presenter and hasattr(self.presenter, "set_lru_cache_size"):
            try:
                size = int(self.lru_size_var.get())
                self.presenter.set_lru_cache_size(size)
            except Exception:
                pass
        self.refresh_debug_info()

    def _on_toggle_auto_clear(self):
        if self.presenter:
            interval = self.auto_clear_interval_var.get()
            if self.auto_clear_var.get():
                self.presenter.enable_auto_cache_clear(interval)
            else:
                self.presenter.disable_auto_cache_clear()
        self.refresh_debug_info()

    def refresh_debug_info(self):
        lines = []
        # 顯示 presenter cache stats
        if self.presenter and hasattr(self.presenter, "get_cache_stats") and hasattr(self.presenter, "get_last_layout_time"):
            hit, miss = self.presenter.get_cache_stats()
            last_time = self.presenter.get_last_layout_time()
            lines.append(f"Cache Hit: {hit}")
            lines.append(f"Cache Miss: {miss}")
            lines.append(f"Last Layout Time: {last_time}")
            # 額外顯示 LRU cache 狀態
            if hasattr(self.presenter, "get_cache_keys") and hasattr(self.presenter, "get_lru_state"):
                keys = self.presenter.get_cache_keys()
                lru = self.presenter.get_lru_state()
                lines.append(f"Cache Keys: {keys}")
                lines.append(f"LRU Capacity: {lru.get('capacity')}")
                lines.append(f"Current Size: {lru.get('current_size')}")
                lines.append(f"Last Hit: {lru.get('last_hit')}")
                lines.append(f"Last Evict: {lru.get('last_evict')}")
            # 顯示自動清空狀態
            if hasattr(self.presenter, "is_auto_cache_clear_enabled"):
                enabled = self.presenter.is_auto_cache_clear_enabled()
                lines.append(f"Auto Cache Clear: {'啟用' if enabled else '停用'}")
                lines.append(f"Interval: {self.auto_clear_interval_var.get()} 秒")
        else:
            lines.append("No presenter stats available.")
        # 額外顯示 context["debug_info"]
        debug_info = None
        if self.presenter and hasattr(self.presenter, "context"):
            debug_info = self.presenter.context.get("debug_info", {})
        if debug_info:
            for k, v in debug_info.items():
                if isinstance(v, dict) or isinstance(v, list):
                    lines.append(f"{k}: {repr(v)}")
                else:
                    lines.append(f"{k}: {v}")
        self.debug_info_label.config(text="\n".join(lines))

        # Undo/Redo 按鈕狀態
        context = self.presenter.context if self.presenter and hasattr(self.presenter, "context") else {}
        if hasattr(self, "undo_btn"):
            can_undo = bool(context.get("history"))
            self.undo_btn.config(state="normal" if can_undo else "disabled")
        if hasattr(self, "redo_btn"):
            can_redo = bool(context.get("redo_history", []))
            self.redo_btn.config(state="normal" if can_redo else "disabled")

    def _bind_member_tree_events(self):
        if not hasattr(self, "member_tree") or not self.member_tree:
            return
        self.member_tree.bind('<<TreeviewOpen>>', self._on_member_tree_open)
        self.member_tree.bind('<<TreeviewClose>>', self._on_member_tree_close)
        self.member_tree.bind('<<TreeviewSelect>>', self._on_member_tree_select)
        # 綁定 header 右鍵事件
        def bind_header_right_click():
            for col in self.member_tree["columns"]:
                self.member_tree.heading(col, command=lambda c=col: None)  # 解除預設排序
                self.member_tree.heading(col, anchor="w")
                self.member_tree.heading(col, text=col)
                self.member_tree.heading(col, command=lambda c=col: None)
                self.member_tree.heading(col, anchor="w")
                # 綁定右鍵
                self.member_tree.heading(col, command=lambda c=col: None)
            self.member_tree.bind("<Button-3>", self._show_treeview_column_menu)
        bind_header_right_click()
        if self.enable_virtual:
            self.member_tree.bind("<Button-3>", lambda e: self._show_node_menu(e), add="+")
        # 拖曳排序事件
        self._dragging_item = None
        self._dragging_parent = None
        self._dragging_index = None
        self._dragging_highlight = None
        tree = self.member_tree
        tree.bind("<ButtonPress-1>", self._on_treeview_drag_start)
        tree.bind("<B1-Motion>", self._on_treeview_drag_motion)
        tree.bind("<ButtonRelease-1>", self._on_treeview_drag_release)

    def _on_treeview_drag_start(self, event):
        tree = self.member_tree
        region = tree.identify("region", event.x, event.y)
        if region != "cell":
            self._dragging_item = None
            return
        item = tree.identify_row(event.y)
        if not item:
            self._dragging_item = None
            return
        self._dragging_item = item
        self._dragging_parent = tree.parent(item)
        self._dragging_index = tree.index(item)
        # highlight 起始 row
        tree.selection_set(item)

    def _on_treeview_drag_motion(self, event):
        tree = self.member_tree
        if not self._dragging_item:
            return
        target_item = tree.identify_row(event.y)
        if not target_item or target_item == self._dragging_item:
            return
        # 僅允許同層級
        if tree.parent(target_item) != self._dragging_parent:
            return
        # highlight 目標 row
        if self._dragging_highlight:
            tree.item(self._dragging_highlight, tags=())
        self._dragging_highlight = target_item
        tree.item(target_item, tags=("highlighted",))

    def _on_treeview_drag_release(self, event):
        tree = self.member_tree
        if not self._dragging_item:
            return
        target_item = tree.identify_row(event.y)
        if not target_item or target_item == self._dragging_item:
            self._clear_drag_highlight()
            self._dragging_item = None
            return
        # 僅允許同層級
        if tree.parent(target_item) != self._dragging_parent:
            self._clear_drag_highlight()
            self._dragging_item = None
            return
        # 計算新順序
        siblings = list(tree.get_children(self._dragging_parent))
        from_idx = siblings.index(self._dragging_item)
        to_idx = siblings.index(target_item)
        new_order = siblings[:]
        item = new_order.pop(from_idx)
        new_order.insert(to_idx, item)
        # 呼叫 reorder callback
        if hasattr(self, "_on_treeview_reorder"):
            self._on_treeview_reorder(self._dragging_parent or "", new_order)
        elif self.presenter and hasattr(self.presenter, "on_reorder_nodes"):
            self.presenter.on_reorder_nodes(self._dragging_parent or "", new_order)
        self._clear_drag_highlight()
        self._dragging_item = None

    def _clear_drag_highlight(self):
        tree = self.member_tree
        if self._dragging_highlight:
            tree.item(self._dragging_highlight, tags=())
        self._dragging_highlight = None

    def _on_treeview_reorder(self, parent_id, new_order):
        if self.presenter and hasattr(self.presenter, "on_reorder_nodes"):
            self.presenter.on_reorder_nodes(parent_id, list(new_order))

    def _show_treeview_column_menu(self, event, test_mode=False):
        # 動態產生欄位選單
        tree = self.member_tree
        context = self.presenter.context if self.presenter and hasattr(self.presenter, "context") else {}
        col_settings = context.get("user_settings", {}).get("treeview_columns", [])
        menu = tk.Menu(tree, tearoff=0)
        for c in col_settings:
            name = c["name"]
            visible = c.get("visible", True)
            menu.add_checkbutton(label=name, onvalue=True, offvalue=False, variable=tk.BooleanVar(value=visible),
                                 command=lambda n=name: self._on_treeview_column_menu_click(n))
        self._treeview_column_menu = menu
        if not test_mode:
            menu.tk_popup(event.x_root, event.y_root)

    def _on_treeview_column_menu_click(self, col_name):
        if self.presenter and hasattr(self.presenter, "on_toggle_column"):
            self.presenter.on_toggle_column(col_name)

    def _on_member_tree_open(self, event):
        item_id = event.widget.focus()
        if self.presenter and hasattr(self.presenter, "on_expand"):
            self.presenter.on_expand(item_id)

    def _on_member_tree_close(self, event):
        item_id = event.widget.focus()
        if self.presenter and hasattr(self.presenter, "on_collapse"):
            self.presenter.on_collapse(item_id)

    def _on_member_tree_select(self, event):
        selected = event.widget.selection()
        if not selected or not self.presenter:
            return
        if len(selected) == 1 and hasattr(self.presenter, "on_node_click"):
            self.presenter.on_node_click(selected[0])
        elif len(selected) > 1 and hasattr(self.presenter, "on_node_select"):
            self.presenter.on_node_select(list(selected))

    def _show_node_menu(self, event, test_mode=False):
        tree = self.member_tree
        # 若無法以座標取得 item，嘗試 fallback：預設選擇第一個子節點（測試場景無座標）
        item = tree.identify_row(event.y)
        if not item:
            children = tree.get_children("")
            if children:
                item = children[0]
        if item:
            tree.selection_set(item)
        menu = tk.Menu(tree, tearoff=0)
        menu.add_command(label="Expand", command=lambda: self.presenter.on_expand(item) if self.presenter else None)
        menu.add_command(label="Collapse", command=lambda: self.presenter.on_collapse(item) if self.presenter else None)
        menu.add_separator()
        menu.add_command(label="Delete", command=self._on_batch_delete)
        self._node_menu = menu
        if not test_mode:
            menu.tk_popup(event.x_root, event.y_root)

    def _select_all_nodes(self):
        tree = self.member_tree
        def collect(parent=""):
            ids = list(tree.get_children(parent))
            for i in list(ids):
                ids.extend(collect(i))
            return ids
        tree.selection_set(collect())

    def show_treeview_nodes(self, nodes, context, icon_map=None):
        self._treeview_refresh_count += 1
        if self.enable_virtual:
            if not hasattr(self, "virtual") and hasattr(self, "modern_tree"):
                self._enable_virtualization()
            if hasattr(self, "virtual"):
                flat = self._flatten_nodes(nodes, context=context)
                self.virtual.set_nodes(flat)
                update_treeview_by_context(self.modern_tree, context)
                return
        # 依據 user_settings 設定 displaycolumns
        all_columns = tuple(c["name"] for c in MEMBER_TREEVIEW_COLUMNS)
        columns = all_columns
        col_settings = context.get("user_settings", {}).get("treeview_columns")
        if col_settings:
            visible_cols = [c for c in sorted(col_settings, key=lambda x: x.get("order", 0)) if c.get("visible", True)]
            columns = tuple(c["name"] for c in visible_cols)
        tree = self.member_tree
        tree["displaycolumns"] = columns
        # 先清空所有節點，避免 id 重複
        for item in tree.get_children(""):
            tree.delete(item)
        # 每次都設置 tag_configure
        tree.tag_configure("highlighted", background="yellow")
        tree.tag_configure("struct", foreground="blue", font="Arial 10 bold")
        tree.tag_configure("union", foreground="purple", font="Arial 10 bold")
        tree.tag_configure("bitfield", foreground="#008000")
        tree.tag_configure("array", foreground="#B8860B")
        # --- diff/patch 機制 ---
        if not hasattr(self, "_last_tree_nodes"):
            self._last_tree_nodes = None
        def node_dict_by_id(nodes):
            d = {}
            def rec(nlist):
                for n in nlist:
                    d[n["id"]] = n
                    rec(n.get("children", []))
            rec(nodes)
            return d
        # fallback: 全量重繪
        def insert_with_highlight(tree, parent_id, node):
            if parent_id in (None, "", 0):
                parent_id = ""
            node_type = node.get("type", "")
            label = node.get("label", node.get("name", ""))
            tags = []
            if node_type == "struct":
                label = f"{label} [struct]"
                tags.append("struct")
            elif node_type == "union":
                label = f"{label} [union]"
                tags.append("union")
            elif node_type == "bitfield":
                tags.append("bitfield")
            elif node_type == "array":
                tags.append("array")
            if node["id"] in set(context.get("highlighted_nodes", [])):
                tags.append("highlighted")
            values = tuple(label if col == "label" else node.get(col, "") for col in columns)
            icon = icon_map.get(node["icon"]) if icon_map and node.get("icon") else ""
            item_id = tree.insert(parent_id, 'end', iid=node['id'], text=label, values=values, image=icon, tags=tuple(tags))
            for child in node.get('children', []):
                insert_with_highlight(tree, item_id, child)
            return item_id
        for node in nodes:
            insert_with_highlight(tree, None, node)
        self._last_tree_nodes = [n.copy() for n in nodes]  # 淺複製即可
        update_treeview_by_context(tree, context)
        # 多選高亮
        selected_nodes = context.get("selected_nodes")
        if selected_nodes:
            def collect_all_ids(tree, parent=""):
                ids = list(tree.get_children(parent))
                for i in list(ids):
                    ids.extend(collect_all_ids(tree, i))
                return ids
            all_ids = set(collect_all_ids(tree, ""))
            filtered = [i for i in selected_nodes if i in all_ids]
            if filtered:
                tree.selection_set(filtered)
            else:
                tree.selection_remove(tree.selection())

    def _flatten_nodes(self, nodes, depth=0, context=None):
        result = []
        highlighted = set(context.get("highlighted_nodes", [])) if context else set()
        for n in nodes:
            n2 = n.copy()
            n2["label"] = ("  " * depth) + n2.get("label", n2.get("name", ""))
            tags = []
            t = n2.get("type")
            if t == "struct":
                tags.append("struct")
            elif t == "union":
                tags.append("union")
            elif t == "bitfield":
                tags.append("bitfield")
            elif t == "array":
                tags.append("array")
            if n2.get("id") in highlighted:
                tags.append("highlighted")
            if tags:
                n2["tags"] = tags
            result.append(n2)
            if n.get("children"):
                result.extend(self._flatten_nodes(n["children"], depth + 1, context))
        return result

    def update_display(self, nodes, context, icon_map=None):
        # context version/結構自動升級/降級與警告
        required_fields = {"highlighted_nodes": []}
        version = context.get("version")
        warning_msg = None
        if version == "2.0":
            for k, v in required_fields.items():
                if k not in context:
                    context[k] = v
        elif version == "1.0":
            for k, v in required_fields.items():
                if k not in context:
                    context[k] = v
            warning_msg = "context 結構過舊，已自動升級"
        else:
            warning_msg = "context version 不明，請檢查"
        if warning_msg:
            try:
                from tkinter import messagebox
                messagebox.showwarning("Context Warning", warning_msg)
            except Exception:
                pass
            context.setdefault("debug_info", {})["context_warning"] = warning_msg
        # 原本 update_display 流程
        self.show_treeview_nodes(nodes, context, icon_map)
        # 顯示錯誤訊息
        if context.get("error"):
            from tkinter import messagebox
            messagebox.showerror("錯誤", str(context["error"]))
        # pending_action 狀態顯示進度與禁用互動
        pending = context.get("pending_action")
        if pending:
            # 顯示進度提示
            if not hasattr(self, "pending_label"):
                self.pending_label = tk.Label(self, text="", fg="blue", font=("Arial", 14, "bold"))
                self.pending_label.pack(side="top", fill="x", pady=4)
            self.pending_label.config(text=f"進行中：{pending}... 請稍候")
            # 禁用主要互動元件
            if hasattr(self, "parse_button"): self.parse_button.config(state="disabled")
            if hasattr(self, "expand_all_btn"): self.expand_all_btn.config(state="disabled")
            if hasattr(self, "collapse_all_btn"): self.collapse_all_btn.config(state="disabled")
            if hasattr(self, "member_tree"): self.member_tree.unbind('<<TreeviewOpen>>'); self.member_tree.unbind('<<TreeviewClose>>'); self.member_tree.unbind('<<TreeviewSelect>>')
        else:
            # 移除進度提示
            if hasattr(self, "pending_label") and self.pending_label.winfo_exists():
                self.pending_label.config(text="")
            # 恢復互動
            if hasattr(self, "parse_button"): self.parse_button.config(state="normal")
            if hasattr(self, "expand_all_btn"): self.expand_all_btn.config(state="normal")
            if hasattr(self, "collapse_all_btn"): self.collapse_all_btn.config(state="normal")
            if hasattr(self, "member_tree"): self._bind_member_tree_events()
        # 顯示 debug_info
        debug_info = context.get("debug_info", {})
        debug_lines = []
        if debug_info:
            if "last_event" in debug_info:
                debug_lines.append(f"last_event: {debug_info['last_event']}")
            if "last_event_args" in debug_info:
                debug_lines.append(f"last_event_args: {debug_info['last_event_args']}")
            if "last_error" in debug_info:
                debug_lines.append(f"last_error: {debug_info['last_error']}")
            if "api_trace" in debug_info:
                debug_lines.append(f"api_trace: {debug_info['api_trace']}")
        self.debug_info_label.config(text="\n".join(debug_lines))

        # 同步 Target Struct 下拉清單與當前 root 名稱
        try:
            extra = context.get('extra', {}) if isinstance(context, dict) else {}
            types = extra.get('available_top_level_types', [])
            if hasattr(self, 'target_struct_combo'):
                # 設定候選清單
                try:
                    # ttk.Combobox
                    self.target_struct_combo['values'] = tuple(types)
                except Exception:
                    pass
                # 取得目前 struct 名稱
                current_root = None
                if self.presenter and hasattr(self.presenter, 'model') and hasattr(self.presenter.model, 'struct_name'):
                    current_root = self.presenter.model.struct_name
                # 同步顯示值
                if current_root:
                    try:
                        self.target_struct_var.set(str(current_root))
                    except Exception:
                        pass
        except Exception:
            pass

        # Undo/Redo 按鈕狀態
        context = self.presenter.context if self.presenter and hasattr(self.presenter, "context") else {}
        if hasattr(self, "undo_btn"):
            can_undo = bool(context.get("history"))
            self.undo_btn.config(state="normal" if can_undo else "disabled")
        if hasattr(self, "redo_btn"):
            can_redo = bool(context.get("redo_history", []))
            self.redo_btn.config(state="normal" if can_redo else "disabled")

        # 同步 32-bit 勾選框狀態與 context['arch_mode']（File 與 Manual 兩處）
        try:
            is_32 = bool(context.get("arch_mode") == "x86")
            if hasattr(self, "file_pointer32_var"):
                self.file_pointer32_var.set(is_32)
            if hasattr(self, "manual_pointer32_var"):
                self.manual_pointer32_var.set(is_32)
        except Exception:
            pass

    def _init_presenter_view_binding(self):
        if self.presenter:
            self.presenter.view = self
            # 若 presenter 有 context 與 get_display_nodes，載入初始資料
            if hasattr(self.presenter, "context") and hasattr(self.presenter, "get_display_nodes"):
                context = self.presenter.context
                mode = context.get("display_mode", "tree")
                try:
                    nodes = self.presenter.get_display_nodes(mode)
                except Exception:
                    nodes = []
                self.update_display(nodes, context)
            # 若 context 尚未初始化，mock 一份 context 以便 UI 測試
            elif hasattr(self.presenter, "get_display_nodes"):
                context = {
                    "display_mode": "tree",
                    "expanded_nodes": ["root"],
                    "selected_node": None,
                    "error": None,
                    "version": "1.0",
                    "extra": {},
                    "loading": False,
                    "history": [],
                    "user_settings": {},
                    "last_update_time": time.time(),
                    "readonly": False,
                    "debug_info": {"last_event": None}
                }
                nodes = self.presenter.get_display_nodes("tree")
                self.update_display(nodes, context)
        self.bind_all("<Control-f>", lambda e: self.search_entry.focus_set())
        self.bind_all("<Control-l>", lambda e: self.filter_entry.focus_set())
        self.bind_all("<Delete>", lambda e: self._on_batch_delete())
        self.bind_all("<Control-a>", lambda e: self._select_all_nodes())

    def _on_expand_all(self):
        if self.presenter and hasattr(self.presenter, "on_expand_all"):
            self.presenter.on_expand_all()

    def _on_collapse_all(self):
        if self.presenter and hasattr(self.presenter, "on_collapse_all"):
            self.presenter.on_collapse_all()

    def _on_display_mode_change(self, mode):
        if self.presenter and hasattr(self.presenter, "on_switch_display_mode"):
            self.presenter.on_switch_display_mode(mode)

    def _on_search_entry_change(self, event):
        search_str = self.search_var.get()
        if self.presenter and hasattr(self.presenter, "on_search"):
            self.presenter.on_search(search_str)

    def _on_filter_entry_change(self, event):
        filter_str = self.filter_var.get()
        if self.presenter and hasattr(self.presenter, "on_filter"):
            self.presenter.on_filter(filter_str)

    def _on_undo(self):
        if self.presenter and hasattr(self.presenter, "on_undo"):
            self.presenter.on_undo()
    def _on_redo(self):
        if self.presenter and hasattr(self.presenter, "on_redo"):
            self.presenter.on_redo()

    def _on_batch_delete(self):
        if self.presenter and hasattr(self.presenter, "on_batch_delete"):
            selected = self.member_tree.selection()
            self.presenter.on_batch_delete(list(selected))

    def _on_gui_version_change(self, version):
        """處理 GUI 版本切換"""
        if self.presenter and hasattr(self.presenter, "on_switch_gui_version"):
            self.presenter.on_switch_gui_version(version)
        
        # 切換顯示模式
        if version == "legacy":
            self._switch_to_legacy_gui()
        elif version == "modern":
            self._switch_to_modern_gui()
        elif version == "v7":
            self._switch_to_v7_gui()
        else:
            self._switch_to_modern_gui()
        # 切換後確保 modern_tree/legacy_tree 的顯示內容有資料
        if hasattr(self, "presenter") and hasattr(self.presenter, "get_display_nodes") and hasattr(self.presenter, "context"):
            try:
                nodes = self.presenter.get_display_nodes(self.presenter.context.get("display_mode", "tree"))
            except Exception:
                nodes = []
            self.update_display(nodes, self.presenter.context)

    def _switch_to_legacy_gui(self):
        """切換到舊版平面顯示"""
        # 隱藏新版元件，顯示舊版元件
        if hasattr(self, "modern_frame"):
            self.modern_frame.pack_forget()
        if hasattr(self, "legacy_tree"):
            self.member_tree = self.legacy_tree
        if hasattr(self, "member_tree"):
            self.member_tree.pack(fill="x")
            self._bind_member_tree_events()

    def _switch_to_modern_gui(self):
        """切換到新版樹狀顯示"""
        # 隱藏舊版元件，顯示新版元件
        if hasattr(self, "member_tree"):
            self.member_tree.pack_forget()
        if hasattr(self, "modern_frame"):
            self.modern_frame.pack(fill="both", expand=True)
        else:
            self._create_modern_gui()
        if self.enable_virtual:
            self._enable_virtualization()
        if hasattr(self, "modern_tree"):
            self.member_tree = self.modern_tree
            self._bind_member_tree_events()
        # 切換後立即刷新顯示內容
        if (self.presenter and hasattr(self.presenter, "get_display_nodes")
                and hasattr(self.presenter, "context")):
            mode = self.presenter.context.get("display_mode", "tree")
            try:
                nodes = self.presenter.get_display_nodes(mode)
            except Exception:
                nodes = []
            self.update_display(nodes, self.presenter.context)

    def _switch_to_v7_gui(self):
        """切換到 v7 版本 GUI。當前實作與新版 GUI 相同。"""
        self._switch_to_modern_gui()

    def _create_modern_gui(self):
        """建立新版樹狀顯示 GUI"""
        # 直接放在原本的 Struct Member Value 區塊（LabelFrame）裡
        member_frame = self.member_tree.master
        
        # 建立新版框架（置於 member_frame 以取代 legacy tree 的顯示空間）
        self.modern_frame = tk.Frame(member_frame)
        
        # 統一引用 MEMBER_TREEVIEW_COLUMNS
        all_columns = MEMBER_TREEVIEW_COLUMNS
        col_names = tuple(c["name"] for c in all_columns)
        self.modern_tree = ttk.Treeview(
            self.modern_frame,
            columns=col_names,
            show="headings",
            height=10
        )
        for c in all_columns:
            self.modern_tree.heading(c["name"], text=c["title"])
            self.modern_tree.column(c["name"], width=c["width"], stretch=False)
        self.modern_tree["displaycolumns"] = col_names
        self.modern_tree.pack(fill="both", expand=True)
        
        # 綁定展開/收合事件
        self.modern_tree.bind("<<TreeviewOpen>>", self._on_modern_tree_open)
        self.modern_tree.bind("<<TreeviewClose>>", self._on_modern_tree_close)
        
        # 將 modern_frame 置於 Struct Member Value 區塊
        self.modern_frame.pack(fill="both", expand=True)
        
        # 若未啟用虛擬化，建立 DummyVirtual 提供測試掛鉤
        if not self.enable_virtual:
            self.virtual = _DummyVirtual(self.modern_tree)
        
        # 如果有現有資料，顯示在新版 GUI 中
        if self.presenter and hasattr(self.presenter, "get_display_nodes"):
            nodes = self.presenter.get_display_nodes("tree")
            if nodes:
                self._populate_modern_tree(nodes)

    def _enable_virtualization(self):
        """Wrap modern_tree with VirtualTreeview when enabled"""
        if not self.enable_virtual:
            return
        if hasattr(self, "modern_tree") and not hasattr(self, "virtual"):
            self.virtual = VirtualTreeview(self.modern_tree, self._virtual_page_size)
            self.member_tree = self.modern_tree
            self._bind_member_tree_events()

    def _populate_modern_tree(self, nodes):
        """將節點資料填入新版樹狀顯示"""
        # 清空現有資料
        for item in self.modern_tree.get_children():
            self.modern_tree.delete(item)
        # 設置 tag_configure（每次都設置，確保樣式）
        self.modern_tree.tag_configure("highlighted", background="yellow")
        self.modern_tree.tag_configure("struct", foreground="blue", font="Arial 10 bold")
        self.modern_tree.tag_configure("union", foreground="purple", font="Arial 10 bold")
        self.modern_tree.tag_configure("bitfield", foreground="#008000")
        self.modern_tree.tag_configure("array", foreground="#B8860B")
        # 遞迴插入節點
        def insert_node(parent, node):
            node_type = node.get("type", "")
            label = node.get("label", node.get("name", ""))
            tags = []
            if node_type == "struct":
                label = f"{label} [struct]"
                tags.append("struct")
            elif node_type == "union":
                label = f"{label} [union]"
                tags.append("union")
            elif node_type == "bitfield":
                tags.append("bitfield")
            elif node_type == "array":
                tags.append("array")
            node_id = self.modern_tree.insert(
                parent, 
                "end", 
                iid=node.get("id", None),
                text=label,
                values=(
                    node.get("name", ""),
                    node.get("value", ""),
                    node.get("hex_value", ""),
                    node.get("hex_raw", "")
                ),
                tags=tuple(tags)
            )
            # 遞迴插入子節點
            for child in node.get("children", []):
                insert_node(node_id, child)
        # 插入所有根節點
        for node in nodes:
            insert_node("", node)
        # 插入完畢後根據 context 展開節點（先展開 parent 再展開 child）
        if self.presenter and hasattr(self.presenter, "context"):
            expanded = set(self.presenter.context.get("expanded_nodes", []))
            def expand_recursive(tree, item_id):
                if item_id in expanded:
                    tree.item(item_id, open=True)
                    tree.update_idletasks()
                for child in tree.get_children(item_id):
                    expand_recursive(tree, child)
            for item in self.modern_tree.get_children(""):
                expand_recursive(self.modern_tree, item)
        self.modern_tree.update_idletasks()

    def _on_modern_tree_open(self, event):
        """新版樹狀顯示展開事件"""
        pass  # 暫時留空，未來可擴充

    def _on_modern_tree_close(self, event):
        """新版樹狀顯示收合事件"""
        pass  # 暫時留空，未來可擴充

    def _on_batch_expand(self):
        if not self.presenter or not hasattr(self.presenter, "on_expand_nodes"):
            return
        selected = self.member_tree.selection()
        if selected:
            self.presenter.on_expand_nodes(list(selected))
            # 重新取得 nodes/context 並刷新顯示
            if hasattr(self.presenter, "get_display_nodes") and hasattr(self.presenter, "context"):
                nodes = self.presenter.get_display_nodes(self.presenter.context.get("display_mode", "tree"))
                self.update_display(nodes, self.presenter.context)

    def _on_batch_collapse(self):
        if not self.presenter or not hasattr(self.presenter, "on_collapse_nodes"):
            return
        selected = self.member_tree.selection()
        if selected:
            self.presenter.on_collapse_nodes(list(selected))
            # 重新取得 nodes/context 並刷新顯示
            if hasattr(self.presenter, "get_display_nodes") and hasattr(self.presenter, "context"):
                nodes = self.presenter.get_display_nodes(self.presenter.context.get("display_mode", "tree"))
                self.update_display(nodes, self.presenter.context)

    def _ensure_takefocus_int(self, widget):
        try:
            orig_cget = widget.cget
            def _cget(key, _orig=orig_cget):
                val = _orig(key)
                if key == 'takefocus':
                    try:
                        return int(val)
                    except Exception:
                        return 1 if str(val).lower() in ('1', 'true') else 0
                return val
            widget.cget = _cget
        except Exception:
            pass

    def _on_pointer_mode_toggle(self, enable_32bit: bool):
        if self.presenter and hasattr(self.presenter, 'on_pointer_mode_toggle'):
            try:
                self.presenter.on_pointer_mode_toggle(enable_32bit)
            except Exception:
                pass

class EntryTooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.visible = False
        widget._tooltip = self
        widget.bind('<Enter>', self.show)
        widget.bind('<Leave>', self.hide)
    def show(self, event=None):
        if self.tipwindow or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert") if hasattr(self.widget, 'bbox') else (0, 0, 0, 0)
        x = x + self.widget.winfo_rootx() + 25
        y = y + self.widget.winfo_rooty() + 20
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, background="#ffffe0", relief="solid", borderwidth=1, font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)
        self.visible = True
    def hide(self, event=None):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()
        self.visible = False