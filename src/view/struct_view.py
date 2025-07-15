import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
# from config import get_string
from model.struct_model import StructModel

def create_member_treeview(parent):
    tree = ttk.Treeview(
        parent,
        columns=("name", "value", "hex_value", "hex_raw"),
        show="headings",
        height=6
    )
    tree.heading("name", text="欄位名稱")
    tree.heading("value", text="值")
    tree.heading("hex_value", text="Hex Value")
    tree.heading("hex_raw", text="Hex Raw")
    tree.column("name", width=120, stretch=False)
    tree.column("value", width=100, stretch=False)
    tree.column("hex_value", width=100, stretch=False)
    tree.column("hex_raw", width=150, stretch=False)
    tree.pack(fill="x")
    return tree

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
    def __init__(self, presenter=None):
        super().__init__()
        self.presenter = presenter
        self.title("C Struct GUI")
        self.geometry("1200x800")

        self._create_tab_control()

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

    def _create_file_tab_frame(self, parent):
        _, main_frame = create_scrollable_tab_frame(parent)
        # 單位選擇與 endianness
        control_frame = tk.Frame(main_frame)
        control_frame.pack(fill="x", pady=(5, 2))
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

        # struct member value 顯示區
        member_frame = tk.LabelFrame(main_frame, text="Struct Member Value")
        member_frame.pack(fill="x", padx=2, pady=2)
        self.member_tree = create_member_treeview(member_frame)

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
        self.layout_tree = ttk.Treeview(layout_frame, columns=("name", "type", "offset", "size", "bit_offset", "bit_size", "is_bitfield"), show="headings", height=10, yscrollcommand=layout_scrollbar.set)
        self.layout_tree.heading("name", text="欄位名稱")
        self.layout_tree.heading("type", text="型別")
        self.layout_tree.heading("offset", text="Offset")
        self.layout_tree.heading("size", text="Size")
        self.layout_tree.heading("bit_offset", text="bit_offset")
        self.layout_tree.heading("bit_size", text="bit_size")
        self.layout_tree.heading("is_bitfield", text="is_bitfield")
        self.layout_tree.pack(side="left", fill="both", expand=True)
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
        self.manual_layout_tree = ttk.Treeview(layout_frame, columns=("name", "type", "offset", "size", "bit_offset", "bit_size", "is_bitfield"), show="headings", height=10, yscrollcommand=layout_scrollbar.set)
        self.manual_layout_tree.heading("name", text="欄位名稱")
        self.manual_layout_tree.heading("type", text="型別")
        self.manual_layout_tree.heading("offset", text="Offset")
        self.manual_layout_tree.heading("size", text="Size")
        self.manual_layout_tree.heading("bit_offset", text="bit_offset")
        self.manual_layout_tree.heading("bit_size", text="bit_size")
        self.manual_layout_tree.heading("is_bitfield", text="is_bitfield")
        self.manual_layout_tree.pack(side="left", fill="both", expand=True)
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
            print("[DEBUG] presenter is None")
            return {}
        member_data = [
            {
                "name": m.get("name", ""),
                "type": m.get("type", ""),
                "bit_size": m.get("bit_size", 0),
            }
            for m in self.members
        ]
        print(f"[DEBUG] member_data: {member_data}")
        try:
            layout = self.presenter.compute_member_layout(member_data, self.size_var.get())
        except Exception as e:
            print(f"[DEBUG] compute_member_layout error: {e}")
            layout = []
        print(f"[DEBUG] layout: {layout}")
        mapping = {}
        for item in layout:
            if item.get("type") != "padding":
                mapping[item["name"]] = str(item["size"])
        print(f"[DEBUG] mapping: {mapping}")
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
        tk.Entry(self.member_frame, textvariable=name_var, width=10).grid(row=row, column=1, padx=2, pady=1)

        type_var = tk.StringVar(value=member.get("type", ""))
        type_options = self._get_type_options(member.get("bit_size", 0) > 0)
        tk.OptionMenu(self.member_frame, type_var, *type_options).grid(row=row, column=2, padx=2, pady=1)

        bit_var = tk.IntVar(value=member.get("bit_size", 0))
        tk.Entry(self.member_frame, textvariable=bit_var, width=6).grid(row=row, column=3, padx=2, pady=1)

        size_val = name2size.get(member.get("name", ""), "-")
        size_label = tk.Label(self.member_frame, text=size_val)
        size_label.grid(row=row, column=4, padx=2, pady=1)
        size_label.is_size_label = True

        op_frame = tk.Frame(self.member_frame)
        op_frame.grid(row=row, column=5, padx=2, pady=1)
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

    def _render_member_table(self):
        # 清空現有表格
        for widget in self.member_frame.winfo_children():
            widget.destroy()
        # Member 編輯表格
        if self.members:
            self._build_member_header(True)
            name2size = self._compute_member_layout(True)
            for idx, m in enumerate(self.members):
                self._render_member_row(idx, m, True, name2size)
        else:
            tk.Label(self.member_frame, text="無成員資料", fg="gray").grid(row=0, column=0, columnspan=6, pady=10)
        # 更新下方標準 struct layout treeview
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
        if errors:
            self.validation_label.config(text="; ".join(errors), fg="red")
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
                self.rebuild_hex_grid(result['total_size'], 1)
            else:
                self.show_error('載入檔案錯誤', result['message'])
                self.disable_parse_button()
                self.clear_results()
                self.rebuild_hex_grid(0, 1)

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

            tree.insert("", "end", values=(item.get("name", ""), value, hex_value, hex_raw))

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

    def show_manual_debug_bytes(self, debug_lines):
        """顯示 MyStruct tab 的 debug bytes，與 file tab 的 show_debug_bytes 一致"""
        self._show_debug_text(self.manual_debug_text, debug_lines)

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
            self.layout_tree.insert("", "end", values=(
                item.get("name", ""),
                item.get("type", ""),
                item.get("offset", ""),
                item.get("size", ""),
                bit_offset_str,
                bit_size_str,
                str(item.get("is_bitfield", False))
            ))

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

    def _on_unit_size_change(self):
        if self.presenter:
            result = self.presenter.on_unit_size_change()
            unit_size = result.get("unit_size")
            if unit_size is not None and hasattr(self, "rebuild_hex_grid"):
                self.rebuild_hex_grid(self.model.total_size if hasattr(self, "model") and hasattr(self.model, "total_size") else 0, unit_size)

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
        """建立十六進位輸入格的共用函式"""
        for widget in frame.winfo_children():
            widget.destroy()
        entry_list.clear()
        if total_size == 0:
            return

        chars_per_box = unit_size * 2
        num_boxes = (total_size + unit_size - 1) // unit_size
        cols = max(1, 16 // unit_size)

        for i in range(num_boxes):
            if i == num_boxes - 1:
                remain_bytes = total_size - (unit_size * (num_boxes - 1))
                box_chars = remain_bytes * 2 if remain_bytes > 0 else chars_per_box
            else:
                box_chars = chars_per_box

            entry = tk.Entry(frame, width=box_chars + 2, font=("Courier", 10))
            entry.grid(row=i // cols, column=i % cols, padx=2, pady=2)
            entry_list.append((entry, box_chars))
            entry.bind("<KeyPress>", lambda e, length=box_chars: self._validate_input(e, length))
            entry.bind("<Key>", lambda e, length=box_chars: self._limit_input_length(e, length))

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
                self.show_manual_debug_bytes(result['debug_lines'])
            else:
                self.show_error('解析錯誤', result['message'])
        else:
            self.manual_debug_text.config(state="normal")
            self.manual_debug_text.delete("1.0", tk.END)
            self.manual_debug_text.insert("1.0", f"hex_parts: {hex_parts}\n(需由 presenter/model 實作解析)")
            self.manual_debug_text.config(state="disabled")

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
        self.refresh_debug_info()

    def refresh_debug_info(self):
        if self.presenter and hasattr(self.presenter, "get_cache_stats") and hasattr(self.presenter, "get_last_layout_time"):
            hit, miss = self.presenter.get_cache_stats()
            last_time = self.presenter.get_last_layout_time()
            text = f"Cache Hit: {hit}\nCache Miss: {miss}\nLast Layout Time: {last_time}"
            # 額外顯示 LRU cache 狀態
            if hasattr(self.presenter, "get_cache_keys") and hasattr(self.presenter, "get_lru_state"):
                keys = self.presenter.get_cache_keys()
                lru = self.presenter.get_lru_state()
                text += f"\nCache Keys: {keys}"
                text += f"\nLRU Capacity: {lru.get('capacity')}"
                text += f"\nCurrent Size: {lru.get('current_size')}"
                text += f"\nLast Hit: {lru.get('last_hit')}"
                text += f"\nLast Evict: {lru.get('last_evict')}"
        else:
            text = "No presenter stats available."
        self.debug_info_label.config(text=text)