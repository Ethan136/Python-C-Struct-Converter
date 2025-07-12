import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from config import get_string

class StructView(tk.Tk):
    def __init__(self, presenter=None):
        super().__init__()
        self.presenter = presenter
        self.title(get_string("app_title"))
        self.geometry("1200x800")

        self.hex_entries = []

        # --- Widgets ---
        # Frame for file selection
        file_frame = tk.Frame(self, pady=5)
        file_frame.pack(fill=tk.X, padx=10)
        self.file_label = tk.Label(file_frame,
                                    text=get_string("no_file_selected"),
                                    anchor="w", justify=tk.LEFT)
        self.file_label.pack(side=tk.LEFT, expand=True, fill=tk.X)
        self.browse_button = tk.Button(file_frame,
                                  text=get_string("browse_button"),
                                  command=self.presenter.browse_file if self.presenter else None)
        self.browse_button.pack(side=tk.RIGHT)

        # Frame for struct layout info
        info_frame = tk.LabelFrame(self,
                                  text=get_string("layout_frame_title"),
                                  padx=10, pady=10)
        info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        # --- 新增：左右分割 ---
        info_split_frame = tk.Frame(info_frame)
        info_split_frame.pack(fill=tk.BOTH, expand=True)
        info_split_frame.columnconfigure(0, weight=1)
        info_split_frame.columnconfigure(1, weight=1)
        # 左：struct layout
        self.info_text = scrolledtext.ScrolledText(info_split_frame, wrap=tk.WORD, height=10, state=tk.DISABLED)
        self.info_text.grid(row=0, column=0, sticky="nsew", padx=(0,5))
        # 右：debug struct 原始內容
        self.struct_debug_text = scrolledtext.ScrolledText(info_split_frame, wrap=tk.WORD, height=10, state=tk.DISABLED, font=("Courier", 10))
        self.struct_debug_text.grid(row=0, column=1, sticky="nsew", padx=(5,0))

        # Frame for hex input
        input_frame = tk.LabelFrame(self,
                                   text=get_string("hex_input_title"),
                                   padx=10, pady=10)
        input_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Control sub-frame for unit selection and endianness
        control_frame = tk.Frame(input_frame)
        control_frame.pack(fill=tk.X, pady=(0, 5))
        tk.Label(control_frame,
                 text=get_string("input_unit_size")).pack(side=tk.LEFT, padx=(0, 10))
        self.unit_size_var = tk.StringVar(value="1 Byte")
        unit_options = ["1 Byte", "4 Bytes", "8 Bytes"]
        self.unit_menu = tk.OptionMenu(control_frame, self.unit_size_var, *unit_options, command=self._dispatch_on_unit_size_change)
        self.unit_menu.pack(side=tk.LEFT)

        tk.Label(control_frame,
                 text=get_string("byte_order")).pack(side=tk.LEFT, padx=(20, 10))
        self.endian_var = tk.StringVar(value="Little Endian")
        endian_options = ["Little Endian", "Big Endian"]
        # Add command to trigger re-parsing when endianness changes
        self.endian_menu = tk.OptionMenu(control_frame, self.endian_var, *endian_options, command=self._dispatch_on_endianness_change)
        self.endian_menu.pack(side=tk.LEFT)

        # --- 水平排列：左邊 hex input，右邊 debug ---
        input_debug_frame = tk.Frame(input_frame)
        input_debug_frame.pack(fill=tk.BOTH, expand=True)
        input_debug_frame.columnconfigure(0, weight=1)
        input_debug_frame.columnconfigure(1, weight=1)

        # 左邊：Canvas with scrollbar for the entry grid
        left_frame = tk.Frame(input_debug_frame)
        left_frame.grid(row=0, column=0, sticky="nsew")
        
        canvas = tk.Canvas(left_frame, borderwidth=0, height=150)
        self.hex_grid_frame = tk.Frame(canvas)
        scrollbar = tk.Scrollbar(left_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas.create_window((4,4), window=self.hex_grid_frame, anchor="nw")
        self.hex_grid_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        # 右邊：Debug Bytes Frame
        right_frame = tk.Frame(input_debug_frame)
        right_frame.grid(row=0, column=1, sticky="nsew")
        
        debug_label = tk.Label(right_frame, text="Debug: Raw Bytes", font=("Arial", 10, "bold"))
        debug_label.pack(anchor="w")
        
        self.debug_text = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD, width=40, height=8, state=tk.DISABLED, font=("Courier", 10))
        self.debug_text.pack(fill=tk.BOTH, expand=True)

        # Parse Button
        self.parse_button = tk.Button(self,
                                      text=get_string("parse_button"),
                                      command=self.presenter.parse_hex_data if self.presenter else None,
                                      state=tk.DISABLED)
        self.parse_button.pack(pady=10)

        # Frame for results
        result_frame = tk.LabelFrame(self,
                                     text=get_string("parsed_values_title"),
                                     padx=10, pady=10)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # --- 水平排列：左邊 parse result，右邊 struct member debug ---
        result_debug_frame = tk.Frame(result_frame)
        result_debug_frame.pack(fill=tk.BOTH, expand=True)
        result_debug_frame.columnconfigure(0, weight=1)
        result_debug_frame.columnconfigure(1, weight=1)

        # 左邊：Parse Results
        left_result_frame = tk.Frame(result_debug_frame)
        left_result_frame.grid(row=0, column=0, sticky="nsew")

        self.result_text = scrolledtext.ScrolledText(left_result_frame, wrap=tk.WORD, height=10, state=tk.DISABLED, font=("Courier", 10))
        self.result_text.pack(fill=tk.BOTH, expand=True)

        # 右邊：Struct Member Debug
        right_result_frame = tk.Frame(result_debug_frame)
        right_result_frame.grid(row=0, column=1, sticky="nsew")

        debug_result_label = tk.Label(right_result_frame, text="Debug: Struct Member Bytes", font=("Arial", 10, "bold"))
        debug_result_label.pack(anchor="w")

        self.debug_result_text = scrolledtext.ScrolledText(right_result_frame, wrap=tk.WORD, width=80, height=10, state=tk.DISABLED, font=("Courier", 10))
        self.debug_result_text.pack(fill=tk.BOTH, expand=True)

    def _dispatch_on_unit_size_change(self, *args):
        if self.presenter:
            self.presenter.on_unit_size_change(*args)

    def _dispatch_on_endianness_change(self, *args):
        if self.presenter:
            self.presenter.on_endianness_change(*args)

    def set_presenter(self, presenter):
        self.presenter = presenter
        self.browse_button.config(command=self.presenter.browse_file)
        self.parse_button.config(command=self.presenter.parse_hex_data)

    def show_file_path(self, path):
        self.file_label.config(text=path)

    def show_struct_layout(self, struct_name, layout, total_size, struct_align):
        info_str = f"Struct: {struct_name}\nAlignment: {struct_align} bytes\nTotal Size: {total_size} bytes\n\n"
        # 新增 bit 欄位資訊欄位
        info_str += "{:<18} {:<20} {:<6} {:<8} {:<10} {:<10} {:<10}\n".format(
            "Member", "Type", "Size", "Offset", "is_bitfield", "bit_offset", "bit_size") + "-" * 85 + "\n"
        for item in layout:
            # Display padding differently
            if item['type'] == "padding":
                info_str += "{:<18} {:<20} {:<6} {:<8} {:<10} {:<10} {:<10}\n".format(
                    item['name'], "-", item['size'], item['offset'], "-", "-", "-")
            else:
                is_bf = str(item.get("is_bitfield", False))
                bit_off = str(item.get("bit_offset", "-"))
                bit_sz = str(item.get("bit_size", "-"))
                info_str += "{:<18} {:<20} {:<6} {:<8} {:<10} {:<10} {:<10}\n".format(
                    item['name'], item['type'], item['size'], item['offset'], is_bf, bit_off, bit_sz)
        self.info_text.config(state=tk.NORMAL); self.info_text.delete('1.0', tk.END); self.info_text.insert(tk.END, info_str); self.info_text.config(state=tk.DISABLED)

    def update_hex_input_status(self, expected_chars):
        # This label is removed in the new grid approach, but keeping for now if needed elsewhere
        pass

    def enable_parse_button(self):
        self.parse_button.config(state=tk.NORMAL)

    def disable_parse_button(self):
        self.parse_button.config(state=tk.DISABLED)

    def clear_results(self):
        self.result_text.config(state=tk.NORMAL); self.result_text.delete('1.0', tk.END); self.result_text.config(state=tk.DISABLED)

    def show_parsed_values(self, parsed_values, byte_order_str):
        # 嘗試取得 layout 以便標示 bitfield
        layout_map = {}
        if hasattr(self, 'model') and hasattr(self.model, 'layout'):
            for item in getattr(self.model, 'layout', []):
                layout_map[item['name']] = item
        result_str = f"Parsed Values (using {byte_order_str})\n"
        result_str += "{:<18} {:<25} {}\n".format("Member", "Value (Decimal/Bool)", "Hex (Value)")
        result_str += "-" * 70 + "\n"

        for item in parsed_values:
            name = item['name']
            value = item['value']
            # 找到對應的 size
            size = None
            for p in parsed_values:
                if p['name'] == name:
                    size = len(item['hex_raw']) // 2 if item['hex_raw'] else 0
                    break
            # bitfield 標示
            bf_tag = ""
            if name in layout_map and layout_map[name].get("is_bitfield", False):
                bf_tag = f" [bitfield bit_offset={layout_map[name]['bit_offset']} bit_size={layout_map[name]['bit_size']}]"
            # padding 顯示 -
            if value == "-":
                hex_value = "-"
            else:
                try:
                    int_value = int(value) if not isinstance(value, bool) else int(value)
                    hex_value = hex(int_value)[2:].zfill(size * 2) if size else hex(int_value)[2:]
                    hex_value = "0x" + hex_value
                except Exception:
                    hex_value = str(value)
            result_str += "{:<18} {:<25} {}{}\n".format(name, value, hex_value, bf_tag)

        self.result_text.config(state=tk.NORMAL); self.result_text.delete('1.0', tk.END); self.result_text.insert(tk.END, result_str); self.result_text.config(state=tk.DISABLED)

    def show_error(self, title, message):
        messagebox.showerror(title, message)

    def show_warning(self, title, message):
        messagebox.showwarning(title, message)

    def get_selected_unit_size(self):
        return int(self.unit_size_var.get().split()[0])

    def get_selected_endianness(self):
        return self.endian_var.get()

    def get_hex_input_parts(self):
        # Returns a list of (raw_input_string, expected_chars_for_this_box)
        return [(entry.get().strip(), expected_len) for entry, expected_len in self.hex_entries]

    def rebuild_hex_grid(self, total_size, unit_size):
        for widget in self.hex_grid_frame.winfo_children():
            widget.destroy()
        self.hex_entries.clear()

        if total_size == 0:
            return

        chars_per_box = unit_size * 2
        num_boxes = (total_size + unit_size - 1) // unit_size
        
        # Calculate columns based on a reasonable entry width, or default to 4 columns
        # This is a heuristic, actual width depends on font and system
        entry_approx_width = chars_per_box * 8 + 20 # rough pixel width
        frame_width = self.hex_grid_frame.winfo_width()
        if frame_width == 1: # Initial call, frame not yet rendered, use a default
            cols = 4 
        else:
            cols = max(1, frame_width // entry_approx_width)
        
        for i in range(num_boxes):
            entry = tk.Entry(self.hex_grid_frame, width=chars_per_box + 2, font=("Courier", 10))
            entry.grid(row=i // cols, column=i % cols, padx=2, pady=2)
            # Store the entry widget along with its expected character length
            self.hex_entries.append((entry, chars_per_box))
            entry.bind("<KeyRelease>", lambda e, length=chars_per_box: self._auto_focus(e, length))

    def _auto_focus(self, event, length):
        widget = event.widget
        if len(widget.get()) >= length:
            next_widget = widget.tk_focusNext()
            if next_widget:
                next_widget.focus()

    def show_debug_bytes(self, debug_lines):
        """
        Show the debug byte content for each input box.
        debug_lines: list of str, each line is one row of bytes (already formatted)
        """
        self.debug_text.config(state=tk.NORMAL)
        self.debug_text.delete('1.0', tk.END)
        for line in debug_lines:
            self.debug_text.insert(tk.END, line + '\n')
        self.debug_text.config(state=tk.DISABLED)

    def show_struct_member_debug(self, parsed_values, layout):
        """
        Show debug information for each struct member including byte values and offset.
        parsed_values: list of dict with parsed member data
        layout: list of dict with struct layout information
        """
        debug_str = "Struct Member Debug Info\n"
        debug_str += "{:<18} {:<8} {:<8} {:<20} {:<30} {}\n".format(
            "Member", "Offset", "Size", "Bytes (Raw)", "BitField Info", "Bytes (Formatted)")
        debug_str += "-" * 120 + "\n"
        for item in parsed_values:
            member_name = item['name']
            hex_raw = item['hex_raw']
            # Find corresponding layout info
            layout_info = None
            for layout_item in layout:
                if layout_item['name'] == member_name:
                    layout_info = layout_item
                    break
            if layout_info:
                offset = layout_info['offset']
                size = layout_info['size']
                # Bitfield info
                bf_info = ""
                if layout_info.get("is_bitfield", False):
                    bf_info = f"is_bitfield=True bit_offset={layout_info['bit_offset']} bit_size={layout_info['bit_size']}"
                # Format bytes for display
                if hex_raw:
                    raw_bytes = hex_raw
                    formatted_bytes = ' '.join([hex_raw[i:i+2] for i in range(0, len(hex_raw), 2)])
                else:
                    raw_bytes = "00" * size
                    formatted_bytes = "00 " * size
                debug_str += "{:<18} {:<8} {:<8} {:<20} {:<30} {}\n".format(
                    member_name, offset, size, raw_bytes, bf_info, formatted_bytes
                )
        self.debug_result_text.config(state=tk.NORMAL)
        self.debug_result_text.delete('1.0', tk.END)
        self.debug_result_text.insert(tk.END, debug_str)
        self.debug_result_text.config(state=tk.DISABLED)

    def show_struct_debug(self, struct_content):
        self.struct_debug_text.config(state=tk.NORMAL)
        self.struct_debug_text.delete('1.0', tk.END)
        self.struct_debug_text.insert(tk.END, struct_content)
        self.struct_debug_text.config(state=tk.DISABLED)