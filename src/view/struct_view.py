import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox, scrolledtext
# from config import get_string

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
        # 單位選擇與 endianness
        control_frame = tk.Frame(parent)
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
        tk.Button(parent, text="選擇 .h 檔", command=self._on_browse_file).pack(anchor="w", pady=2)
        # 檔案路徑顯示
        self.file_path_label = tk.Label(parent, text="尚未選擇檔案")
        self.file_path_label.pack(anchor="w", pady=2)

        # hex grid 輸入區
        self.hex_entries = []
        self.hex_grid_frame = tk.Frame(parent)
        self.hex_grid_frame.pack(fill="x", pady=2)

        # 解析按鈕
        self.parse_button = tk.Button(parent, text="解析", command=self._on_parse_file, state="disabled")
        self.parse_button.pack(anchor="w", pady=5)

        # struct member value 顯示區
        member_frame = tk.LabelFrame(parent, text="Struct Member Value")
        member_frame.pack(fill="x", padx=2, pady=2)
        self.member_tree = ttk.Treeview(member_frame, columns=("name", "value", "hex_value", "hex_raw"), show="headings", height=6)
        self.member_tree.heading("name", text="欄位名稱")
        self.member_tree.heading("value", text="值")
        self.member_tree.heading("hex_value", text="Hex Value")
        self.member_tree.heading("hex_raw", text="Hex Raw")
        self.member_tree.pack(fill="x")

        # debug bytes 顯示區
        debug_frame = tk.LabelFrame(parent, text="Debug Bytes")
        debug_frame.pack(fill="x", padx=2, pady=2)
        self.debug_text = tk.Text(debug_frame, height=4, width=100)
        self.debug_text.pack(fill="x")

        # struct layout 顯示區
        layout_frame = tk.LabelFrame(parent, text="Struct Layout")
        layout_frame.pack(fill="both", expand=True, padx=2, pady=2)
        self.layout_tree = ttk.Treeview(layout_frame, columns=("name", "type", "offset", "size", "bit_offset", "bit_size", "is_bitfield"), show="headings", height=10)
        self.layout_tree.heading("name", text="欄位名稱")
        self.layout_tree.heading("type", text="型別")
        self.layout_tree.heading("offset", text="Offset")
        self.layout_tree.heading("size", text="Size")
        self.layout_tree.heading("bit_offset", text="bit_offset")
        self.layout_tree.heading("bit_size", text="bit_size")
        self.layout_tree.heading("is_bitfield", text="is_bitfield")
        self.layout_tree.pack(fill="both", expand=True)

    def _create_manual_struct_frame(self, parent):
        # 結構體名稱
        name_frame = tk.Frame(parent)
        name_frame.pack(anchor="w", pady=5)
        tk.Label(name_frame, text="struct 名稱:").pack(side=tk.LEFT)
        self.struct_name_var = tk.StringVar(value="MyStruct")
        tk.Entry(name_frame, textvariable=self.struct_name_var, width=20).pack(side=tk.LEFT)

        # 結構體大小
        size_frame = tk.Frame(parent)
        size_frame.pack(anchor="w", pady=5)
        tk.Label(size_frame, text="結構體總大小 (bits):").pack(side=tk.LEFT)
        self.size_var = tk.IntVar(value=0)
        tk.Entry(size_frame, textvariable=self.size_var, width=10).pack(side=tk.LEFT)

        # Bitfield表格
        self.bitfields = []
        self.bitfield_frame = tk.Frame(parent)
        self.bitfield_frame.pack(fill="x", pady=5)
        self._render_bitfield_table()

        # 新增Bitfield按鈕
        tk.Button(parent, text="新增Bitfield", command=self._add_bitfield).pack(anchor="w", pady=2)

        # 驗證提示
        self.validation_label = tk.Label(parent, text="", fg="red")
        self.validation_label.pack(anchor="w", pady=2)

        # 匯出/儲存/重設按鈕
        btn_frame = tk.Frame(parent)
        btn_frame.pack(anchor="w", pady=5)
        tk.Button(btn_frame, text="匯出為.H檔", command=self.on_export_manual_struct).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="重設", command=self._reset_manual_struct).pack(side=tk.LEFT, padx=2)

    def _render_bitfield_table(self):
        # 清空現有表格
        for widget in self.bitfield_frame.winfo_children():
            widget.destroy()
        # 標題
        tk.Label(self.bitfield_frame, text="#").grid(row=0, column=0)
        tk.Label(self.bitfield_frame, text="成員名稱").grid(row=0, column=1)
        tk.Label(self.bitfield_frame, text="長度(bit)").grid(row=0, column=2)
        tk.Label(self.bitfield_frame, text="操作").grid(row=0, column=3)
        # 每一列
        for idx, bf in enumerate(self.bitfields):
            tk.Label(self.bitfield_frame, text=str(idx+1)).grid(row=idx+1, column=0)
            name_var = tk.StringVar(value=bf.get("name", ""))
            length_var = tk.IntVar(value=bf.get("length", 1))
            tk.Entry(self.bitfield_frame, textvariable=name_var, width=10).grid(row=idx+1, column=1)
            tk.Entry(self.bitfield_frame, textvariable=length_var, width=6).grid(row=idx+1, column=2)
            op_frame = tk.Frame(self.bitfield_frame)
            op_frame.grid(row=idx+1, column=3)
            tk.Button(op_frame, text="刪除", command=lambda i=idx: self._delete_bitfield(i)).pack(side=tk.LEFT)
            tk.Button(op_frame, text="上移", command=lambda i=idx: self._move_bitfield_up(i)).pack(side=tk.LEFT)
            tk.Button(op_frame, text="下移", command=lambda i=idx: self._move_bitfield_down(i)).pack(side=tk.LEFT)
            tk.Button(op_frame, text="複製", command=lambda i=idx: self._copy_bitfield(i)).pack(side=tk.LEFT)
            # 綁定變更
            name_var.trace_add("write", lambda *_, i=idx, v=name_var: self._update_bitfield_name(i, v))
            length_var.trace_add("write", lambda *_, i=idx, v=length_var: self._update_bitfield_length(i, v))
            bf["name_var"] = name_var
            bf["length_var"] = length_var

    def _add_bitfield(self):
        self.bitfields.append({"name": "", "length": 1})
        self._render_bitfield_table()
        self._on_manual_struct_change()

    def _delete_bitfield(self, idx):
        del self.bitfields[idx]
        self._render_bitfield_table()
        self._on_manual_struct_change()

    def _update_bitfield_name(self, idx, var):
        self.bitfields[idx]["name"] = var.get()
        self._on_manual_struct_change()

    def _update_bitfield_length(self, idx, var):
        try:
            self.bitfields[idx]["length"] = int(var.get())
        except ValueError:
            self.bitfields[idx]["length"] = 0
        self._on_manual_struct_change()

    def _move_bitfield_up(self, idx):
        if idx > 0:
            self.bitfields[idx-1], self.bitfields[idx] = self.bitfields[idx], self.bitfields[idx-1]
            self._render_bitfield_table()
            self._on_manual_struct_change()

    def _move_bitfield_down(self, idx):
        if idx < len(self.bitfields) - 1:
            self.bitfields[idx+1], self.bitfields[idx] = self.bitfields[idx], self.bitfields[idx+1]
            self._render_bitfield_table()
            self._on_manual_struct_change()

    def _copy_bitfield(self, idx):
        orig = self.bitfields[idx]
        base_name = orig["name"]
        # 自動命名：a_copy, a_copy2, a_copy3...
        new_name = base_name + "_copy"
        existing_names = {bf["name"] for bf in self.bitfields}
        count = 2
        while new_name in existing_names:
            new_name = f"{base_name}_copy{count}"
            count += 1
        new_bf = {"name": new_name, "length": orig["length"]}
        self.bitfields.insert(idx+1, new_bf)
        self._render_bitfield_table()
        self._on_manual_struct_change()

    def _reset_manual_struct(self):
        self.size_var.set(0)
        self.bitfields.clear()
        self._render_bitfield_table()
        self.validation_label.config(text="")

    def _on_manual_struct_change(self):
        struct_data = self.get_manual_struct_definition()
        if self.presenter:
            self.presenter.on_manual_struct_change(struct_data)

    def get_manual_struct_definition(self):
        return {
            "struct_name": self.struct_name_var.get(),
            "total_size": self.size_var.get(),
            "members": [{"name": bf["name"], "length": bf["length"]} for bf in self.bitfields]
        }

    def show_manual_struct_validation(self, errors):
        if errors:
            self.validation_label.config(text="; ".join(errors), fg="red")
        else:
            self.validation_label.config(text="設定正確", fg="green")

    def on_export_manual_struct(self):
        if self.presenter:
            self.presenter.on_export_manual_struct()

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
            self.presenter.browse_file()

    def _on_parse_file(self):
        if self.presenter:
            self.presenter.parse_hex_data()

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

    def show_parsed_values(self, parsed_values, byte_order_str=None):
        # 清空舊資料
        for i in self.member_tree.get_children():
            self.member_tree.delete(i)
        # 插入新資料
        for item in parsed_values:
            value = item.get("value", "")
            hex_value = ""
            try:
                if value != "-":
                    int_value = int(value)
                    hex_value = hex(int_value)
                else:
                    hex_value = "-"
            except Exception:
                hex_value = "-"
            self.member_tree.insert("", "end", values=(item.get("name", ""), value, hex_value, item.get("hex_raw", "")))

    def show_debug_bytes(self, debug_lines):
        self.debug_text.config(state="normal")
        self.debug_text.delete("1.0", tk.END)
        if debug_lines:
            self.debug_text.insert("1.0", "\n".join(debug_lines))
        else:
            self.debug_text.insert("1.0", "無 debug 資訊")
        self.debug_text.config(state="disabled")

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
            self.presenter.on_unit_size_change()

    def _on_endianness_change(self):
        if self.presenter:
            self.presenter.on_endianness_change()

    def get_selected_unit_size(self):
        return int(self.unit_size_var.get().split()[0])

    def get_selected_endianness(self):
        return self.endian_var.get()

    def rebuild_hex_grid(self, total_size, unit_size):
        for widget in self.hex_grid_frame.winfo_children():
            widget.destroy()
        self.hex_entries.clear()
        if total_size == 0:
            return
        chars_per_box = unit_size * 2
        num_boxes = (total_size + unit_size - 1) // unit_size
        cols = 4
        for i in range(num_boxes):
            entry = tk.Entry(self.hex_grid_frame, width=chars_per_box + 2, font=("Courier", 10))
            entry.grid(row=i // cols, column=i % cols, padx=2, pady=2)
            self.hex_entries.append((entry, chars_per_box))
            entry.bind("<KeyPress>", lambda e, length=chars_per_box: self._validate_input(e, length))
            entry.bind("<Key>", lambda e, length=chars_per_box: self._limit_input_length(e, length))

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