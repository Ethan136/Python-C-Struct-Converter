import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

class StructView(tk.Tk):
    def __init__(self, presenter):
        super().__init__()
        self.presenter = presenter
        self.title("C++ Struct Parser")
        self.geometry("750x800")

        self.hex_entries = []

        # --- Widgets ---
        # Frame for file selection
        file_frame = tk.Frame(self, pady=5)
        file_frame.pack(fill=tk.X, padx=10)
        self.file_label = tk.Label(file_frame, text="No file selected.", anchor="w", justify=tk.LEFT)
        self.file_label.pack(side=tk.LEFT, expand=True, fill=tk.X)
        browse_button = tk.Button(file_frame, text="Browse...", command=self.presenter.browse_file)
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
        unit_menu = tk.OptionMenu(control_frame, self.unit_size_var, *unit_options, command=self.presenter.on_unit_size_change)
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
        self.parse_button = tk.Button(self, text="Parse Data", command=self.presenter.parse_hex_data, state=tk.DISABLED)
        self.parse_button.pack(pady=10)

        # Frame for results
        result_frame = tk.LabelFrame(self, text="Parsed Values", padx=10, pady=10)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD, height=10, state=tk.DISABLED, font=("Courier", 10))
        self.result_text.pack(fill=tk.BOTH, expand=True)

    def show_file_path(self, path):
        self.file_label.config(text=path)

    def show_struct_layout(self, struct_name, layout, total_size, struct_align):
        info_str = f"Struct: {struct_name}\nAlignment: {struct_align} bytes\nTotal Size: {total_size} bytes\n\n"
        info_str += "{:<18} {:<20} {:<6} {:<8}\n".format("Member", "Type", "Size", "Offset") + "-" * 55 + "\n"
        for item in layout:
            info_str += "{:<18} {:<20} {:<6} {:<8}\n".format(item['name'], item['type'], item['size'], item['offset'])
        
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
        result_str = f"Parsed Values (using {byte_order_str})\n"
        result_str += "{:<18} {:<25} {}\n".format("Member", "Value (Decimal/Bool)", "Hex (Raw Slice)")
        result_str += "-" * 70 + "\n"

        for item in parsed_values:
            result_str += "{:<18} {:<25} 0x{}\n".format(item['name'], item['value'], item['hex_raw'])

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
        return [entry.get().strip() for entry in self.hex_entries]

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
            self.hex_entries.append(entry)
            entry.bind("<KeyRelease>", lambda e, length=chars_per_box: self._auto_focus(e, length))

    def _auto_focus(self, event, length):
        widget = event.widget
        if len(widget.get()) >= length:
            next_widget = widget.tk_focusNext()
            if next_widget:
                next_widget.focus()
