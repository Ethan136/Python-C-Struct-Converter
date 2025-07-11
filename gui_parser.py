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
        self.geometry("700x750")

        self.struct_layout = None
        self.total_size = 0

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
        self.hex_entry = tk.Entry(input_frame, font=("Courier", 10))
        self.hex_entry.pack(fill=tk.X, ipady=4)
        self.hex_status_label = tk.Label(input_frame, text="Expected characters: 0", anchor="w", justify=tk.LEFT)
        self.hex_status_label.pack(fill=tk.X)

        # Parse Button
        self.parse_button = tk.Button(self, text="Parse Data", command=self.parse_hex_data, state=tk.DISABLED)
        self.parse_button.pack(pady=10)

        # Frame for results
        result_frame = tk.LabelFrame(self, text="Parsed Values", padx=10, pady=10)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD, height=10, state=tk.DISABLED, font=("Courier", 10))
        self.result_text.pack(fill=tk.BOTH, expand=True)

    def browse_file(self):
        file_path = filedialog.askopenfilename(
            title="Select a C++ header file",
            filetypes=(("Header files", "*.h"), ("All files", "*.*"))
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
            
            # Display layout info
            info_str = f"Struct: {struct_name}\n"
            info_str += f"Alignment: {struct_align} bytes\n"
            info_str += f"Total Size: {self.total_size} bytes\n\n"
            info_str += "{:<18} {:<20} {:<6} {:<8}\n".format("Member", "Type", "Size", "Offset")
            info_str += "-" * 55 + "\n"
            for item in self.struct_layout:
                info_str += "{:<18} {:<20} {:<6} {:<8}\n".format(item['name'], item['type'], item['size'], item['offset'])
            
            self.info_text.config(state=tk.NORMAL)
            self.info_text.delete('1.0', tk.END)
            self.info_text.insert(tk.END, info_str)
            self.info_text.config(state=tk.DISABLED)

            # Update hex input status
            self.hex_status_label.config(text=f"Expected characters: {self.total_size * 2}")
            self.parse_button.config(state=tk.NORMAL)
            self.result_text.config(state=tk.NORMAL)
            self.result_text.delete('1.0', tk.END)
            self.result_text.config(state=tk.DISABLED)

        except Exception as e:
            messagebox.showerror("File Error", f"An error occurred: {e}")

    def parse_hex_data(self):
        hex_data = self.hex_entry.get().strip()

        if not self.struct_layout:
            messagebox.showwarning("No Struct", "Please load a struct definition file first.")
            return

        # Validate hex data
        if not re.match(r"^[0-9a-fA-F]*$", hex_data):
            messagebox.showerror("Invalid Input", "Input contains non-hexadecimal characters.")
            return
        if len(hex_data) != self.total_size * 2:
            messagebox.showerror("Invalid Length", f"Expected {self.total_size * 2} hex characters, but got {len(hex_data)}.")
            return

        data_bytes = bytes.fromhex(hex_data)
        
        # Prepare result string
        result_str = "{:<18} {:<25} {}\n".format("Member", "Value (Decimal/Bool)", "Hex (Little Endian)")
        result_str += "-" * 70 + "\n"

        for item in self.struct_layout:
            offset, size, name = item['offset'], item['size'], item['name']
            member_bytes = data_bytes[offset : offset + size]
            value = int.from_bytes(member_bytes, 'little')
            hex_value = member_bytes.hex()

            display_value = str(bool(value)) if item['type'] == 'bool' else str(value)
            result_str += "{:<18} {:<25} 0x{}\n".format(name, display_value, hex_value)

        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete('1.0', tk.END)
        self.result_text.insert(tk.END, result_str)
        self.result_text.config(state=tk.DISABLED)

if __name__ == "__main__":
    app = StructParserApp()
    app.mainloop()
