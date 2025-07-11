
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import re
import sys

# --- Core Logic from struct_parser.py ---

# Based on a common 64-bit system (like GCC on x86-64)
TYPE_INFO = {
    "char":               {"size": 1, "align": 1},
    "signed char":        {"size": 1, "align": 1},
    "unsigned char":      {"size": 1, "align": 1},
    "bool":               {"size": 1, "align": 1},
    "short":              {"size": 2, "align": 2},
    "unsigned short":     {"size": 2, "align": 2},
    "int":                {"size": 4, "align": 4},
    "unsigned int":       {"size": 4, "align": 4},
    "long":               {"size": 8, "align": 8}, # Common on 64-bit Linux/macOS
    "unsigned long":      {"size": 8, "align": 8},
    "long long":          {"size": 8, "align": 8},
    "unsigned long long": {"size": 8, "align": 8},
    "float":              {"size": 4, "align": 4},
    "double":             {"size": 8, "align": 8},
    "pointer":            {"size": 8, "align": 8} # Generic for all pointer types
}

def parse_struct_definition(file_content):
    struct_match = re.search(r"struct\s+(\w+)\s*\{([^}]+)\};", file_content, re.DOTALL)
    if not struct_match:
        return None, None
    struct_name = struct_match.group(1)
    struct_content = struct_match.group(2)
    member_matches = re.findall(r"\s*([\w\s\*]+?)\s+([\w\[\]]+);", struct_content)
    members = []
    for type_str, name in member_matches:
        clean_type = " ".join(type_str.strip().split())
        if "*" in clean_type:
            members.append(("pointer", name))
        elif clean_type in TYPE_INFO:
            members.append((clean_type, name))
    return struct_name, members

def calculate_layout(members):
    if not members:
        return [], 0, 1
    layout = []
    current_offset = 0
    max_alignment = 1
    for member_type, member_name in members:
        info = TYPE_INFO[member_type]
        size, alignment = info["size"], info["align"]
        if alignment > max_alignment:
            max_alignment = alignment
        padding = (alignment - (current_offset % alignment)) % alignment
        current_offset += padding
        layout.append({"name": member_name, "type": member_type, "size": size, "offset": current_offset})
        current_offset += size
    final_padding = (max_alignment - (current_offset % max_alignment)) % max_alignment
    total_size = current_offset + final_padding
    return layout, total_size, max_alignment

# --- GUI Application ---

class StructParserApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("C++ Struct Parser")
        self.geometry("750x800")

        self.struct_layout = None
        self.total_size = 0
        self.hex_entries = []

        # --- Widgets ---
        # Frame for file selection
        file_frame = tk.Frame(self, pady=5)
        file_frame.pack(fill=tk.X, padx=10)
        self.file_label = tk.Label(file_frame, text="No file selected.", anchor="w", justify=tk.LEFT)
        self.file_label.pack(side=tk.LEFT, expand=True, fill=tk.X)
        browse_button = tk.Button(file_frame, text="Browse...", command=self.browse_file)
        browse_button.pack(side=tk.RIGHT)

        # Frame for struct layout info
        info_frame = tk.LabelFrame(self, text="Struct Layout", padx=10, pady=10)
        info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.info_text = scrolledtext.ScrolledText(info_frame, wrap=tk.WORD, height=10, state=tk.DISABLED)
        self.info_text.pack(fill=tk.BOTH, expand=True)

        # Frame for hex input
        input_frame = tk.LabelFrame(self, text="Hex Data Input", padx=10, pady=10)
        input_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Control sub-frame for unit selection and endianness
        control_frame = tk.Frame(input_frame)
        control_frame.pack(fill=tk.X, pady=(0, 5))
        tk.Label(control_frame, text="Input Unit Size:").pack(side=tk.LEFT, padx=(0, 10))
        self.unit_size_var = tk.StringVar(value="1 Byte")
        unit_options = ["1 Byte", "4 Bytes", "8 Bytes"]
        unit_menu = tk.OptionMenu(control_frame, self.unit_size_var, *unit_options, command=lambda _: self._rebuild_hex_grid())
        unit_menu.pack(side=tk.LEFT)

        tk.Label(control_frame, text="Byte Order:").pack(side=tk.LEFT, padx=(20, 10))
        self.endian_var = tk.StringVar(value="Little Endian")
        endian_options = ["Little Endian", "Big Endian"]
        endian_menu = tk.OptionMenu(control_frame, self.endian_var, *endian_options)
        endian_menu.pack(side=tk.LEFT)

        # Canvas with scrollbar for the entry grid
        canvas = tk.Canvas(input_frame, borderwidth=0, height=150)
        self.hex_grid_frame = tk.Frame(canvas)
        scrollbar = tk.Scrollbar(input_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas.create_window((4,4), window=self.hex_grid_frame, anchor="nw")
        self.hex_grid_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        # Parse Button
        self.parse_button = tk.Button(self, text="Parse Data", command=self.parse_hex_data, state=tk.DISABLED)
        self.parse_button.pack(pady=10)

        # Test Data Button
        self.test_button = tk.Button(self, text="填入測試資料", command=self.fill_test_data, state=tk.DISABLED)
        self.test_button.pack(pady=5)

        # Frame for results
        result_frame = tk.LabelFrame(self, text="Parsed Values", padx=10, pady=10)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD, height=10, state=tk.DISABLED, font=("Courier", 10))
        self.result_text.pack(fill=tk.BOTH, expand=True)

    def browse_file(self):
        file_path = filedialog.askopenfilename(
            title="Select a C++ header file",
            filetypes=(("Header files", "*.h"), ("All files", "*.*" ))
        )
        if not file_path:
            return

        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            struct_name, members = parse_struct_definition(content)
            if not struct_name or not members:
                messagebox.showerror("Parsing Error", "Could not find a valid struct definition in the file.")
                return

            self.file_label.config(text=file_path)
            self.struct_layout, self.total_size, struct_align = calculate_layout(members)
            
            info_str = f"Struct: {struct_name}\nAlignment: {struct_align} bytes\nTotal Size: {self.total_size} bytes\n\n"
            info_str += "{:<18} {:<20} {:<6} {:<8} {:<12}\n".format("Member", "Type", "Size", "Offset", "Range") + "-" * 70 + "\n"
            last_end = 0
            for item in self.struct_layout:
                start = item['offset']
                end = start + item['size']
                # 如果有 padding
                if start > last_end:
                    info_str += "{:<18} {:<20} {:<6} {:<8} {:<12}\n".format(
                        "<padding>", "-", str(start - last_end), str(last_end), f"{last_end}~{start}")
                info_str += "{:<18} {:<20} {:<6} {:<8} {:<12}\n".format(
                    item['name'], item['type'], item['size'], start, f"{start}~{end}")
                last_end = end
            # struct 結尾 padding
            if last_end < self.total_size:
                info_str += "{:<18} {:<20} {:<6} {:<8} {:<12}\n".format(
                    "<padding>", "-", str(self.total_size - last_end), str(last_end), f"{last_end}~{self.total_size}")
            
            self.info_text.config(state=tk.NORMAL); self.info_text.delete('1.0', tk.END); self.info_text.insert(tk.END, info_str); self.info_text.config(state=tk.DISABLED)
            self.parse_button.config(state=tk.NORMAL)
            self.test_button.config(state=tk.NORMAL)
            self.result_text.config(state=tk.NORMAL); self.result_text.delete('1.0', tk.END); self.result_text.config(state=tk.DISABLED)
            
            self._rebuild_hex_grid()

        except Exception as e:
            messagebox.showerror("File Error", f"An error occurred: {e}")

    def _rebuild_hex_grid(self):
        for widget in self.hex_grid_frame.winfo_children():
            widget.destroy()
        self.hex_entries.clear()

        if self.total_size == 0:
            return

        unit_str = self.unit_size_var.get()
        unit_size = int(unit_str.split()[0])
        chars_per_box = unit_size * 2
        num_boxes = (self.total_size + unit_size - 1) // unit_size
        cols = max(1, self.hex_grid_frame.winfo_width() // (chars_per_box * 8))

        for i in range(num_boxes):
            entry = tk.Entry(self.hex_grid_frame, width=chars_per_box + 2, font=("Courier", 10))
            entry.grid(row=i // cols, column=i % cols, padx=2, pady=2)
            self.hex_entries.append(entry)
            entry.bind("<KeyRelease>", lambda e, length=chars_per_box: self._auto_focus(e, length))

    def _auto_focus(self, event, length):
        widget = event.widget
        if len(widget.get()) >= length:
            next_widget = widget.tk_focusNext()
            if next_widget:
                next_widget.focus()

    def parse_hex_data(self):
        if not self.struct_layout:
            messagebox.showwarning("No Struct", "Please load a struct definition file first.")
            return

        hex_parts = [entry.get().strip() for entry in self.hex_entries]
        hex_data = "".join(hex_parts)

        if not re.match(r"^[0-9a-fA-F]*$", hex_data):
            messagebox.showerror("Invalid Input", "Input contains non-hexadecimal characters.")
            return
        if len(hex_data) > self.total_size * 2:
            messagebox.showerror("Invalid Length", f"Input data ({len(hex_data)} chars) is longer than the expected total size ({self.total_size * 2} chars).")
            return
        
        hex_data = hex_data.ljust(self.total_size * 2, '0')
        data_bytes = bytes.fromhex(hex_data)
        
        byte_order_str = self.endian_var.get()
        byte_order = 'little' if byte_order_str == "Little Endian" else 'big'

        result_str = f"Parsed Values (using {byte_order_str})\n"
        result_str += "{:<18} {:<25} {:<20} {}\n".format("Member", "Value (Decimal/Bool)", "Raw Bytes", "Hex (Raw Slice)")
        result_str += "-" * 90 + "\n"

        for item in self.struct_layout:
            offset, size, name = item['offset'], item['size'], item['name']
            member_bytes = data_bytes[offset : offset + size]
            value = int.from_bytes(member_bytes, byte_order)
            hex_value = member_bytes.hex()
            display_value = str(bool(value)) if item['type'] == 'bool' else str(value)
            result_str += "{:<18} {:<25} {:<20} 0x{}\n".format(name, display_value, str(list(member_bytes)), hex_value)

        self.result_text.config(state=tk.NORMAL); self.result_text.delete('1.0', tk.END); self.result_text.insert(tk.END, result_str); self.result_text.config(state=tk.DISABLED)

    def fill_test_data(self):
        """
        根據 struct_layout 自動填入適合測試 endian 差異的 hex 資料。
        int/short/long 會填 0x01000000...，char/bool 填 0x01。
        """
        if not self.struct_layout:
            return
        # 預設 little endian 測試值
        test_bytes = bytearray(self.total_size)
        for item in self.struct_layout:
            offset, size, typ = item['offset'], item['size'], item['type']
            if size == 1:
                test_bytes[offset] = 0x01
            else:
                # 只針對 int/short/long 這類型，填 0x01 其餘 0x00
                test_bytes[offset:offset+size] = (1).to_bytes(size, 'little')
        # 依照 hex_entries 分割填入
        unit_str = self.unit_size_var.get()
        unit_size = int(unit_str.split()[0])
        chars_per_box = unit_size * 2
        hex_str = test_bytes.hex()
        for i, entry in enumerate(self.hex_entries):
            entry.delete(0, tk.END)
            entry.insert(0, hex_str[i*chars_per_box:(i+1)*chars_per_box])

if __name__ == "__main__":
    app = StructParserApp()
    app.mainloop()
