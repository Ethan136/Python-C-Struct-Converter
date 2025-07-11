from tkinter import filedialog

class StructPresenter:
    def __init__(self, model, view):
        self.model = model
        self.view = view
        self.view.presenter = self # Set presenter reference in view

    def browse_file(self):
        file_path = filedialog.askopenfilename(
            title="Select a C++ header file",
            filetypes=(("Header files", "*.h"), ("All files", "*.*"))
        )
        if not file_path:
            return

        try:
            struct_name, layout, total_size, struct_align = self.model.load_struct_from_file(file_path)
            self.view.show_file_path(file_path)
            self.view.show_struct_layout(struct_name, layout, total_size, struct_align)
            self.view.enable_parse_button()
            self.view.clear_results()
            
            # Rebuild hex grid based on new struct size
            unit_size = self.view.get_selected_unit_size()
            self.view.rebuild_hex_grid(total_size, unit_size)

        except Exception as e:
            self.view.show_error("File Error", f"An error occurred: {e}")
            self.view.disable_parse_button()
            self.view.clear_results()
            self.view.rebuild_hex_grid(0, 1) # Clear hex grid

    def on_unit_size_change(self, *args):
        # This method is called when the unit size dropdown changes
        if self.model.total_size > 0: # Only rebuild if a struct is loaded
            unit_size = self.view.get_selected_unit_size()
            self.view.rebuild_hex_grid(self.model.total_size, unit_size)

    def parse_hex_data(self):
        if not self.model.layout:
            self.view.show_warning("No Struct", "Please load a struct definition file first.")
            return

        hex_parts = self.view.get_hex_input_parts()
        hex_data = "".join(hex_parts)

        if not hex_data: # Allow empty input to be parsed as all zeros
            hex_data = ""
        elif not all(re.match(r"^[0-9a-fA-F]*$", part) for part in hex_parts):
            self.view.show_error("Invalid Input", "Input contains non-hexadecimal characters.")
            return
        
        # The model will handle padding if hex_data is shorter than total_size * 2
        # We only check if it's too long here
        if len(hex_data) > self.model.total_size * 2:
            self.view.show_error("Invalid Length", f"Input data ({len(hex_data)} chars) is longer than the expected total size ({self.model.total_size * 2} chars).")
            return

        try:
            byte_order_str = self.view.get_selected_endianness()
            byte_order = 'little' if byte_order_str == "Little Endian" else 'big'
            parsed_values = self.model.parse_hex_data(hex_data, byte_order)
            self.view.show_parsed_values(parsed_values, byte_order_str)
        except Exception as e:
            self.view.show_error("Parsing Error", f"An error occurred during parsing: {e}")

