import os
import xml.etree.ElementTree as ET


def test_ui_strings_contains_required_keys():
    # Minimal completeness check for keys referenced in code
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    xml_path = os.path.join(root_dir, "src", "config", "ui_strings.xml")
    tree = ET.parse(xml_path)
    root = tree.getroot()
    keys = {elem.attrib.get("name") for elem in root.findall("string")}

    required = {
        # titles/tabs
        "window_title", "tab_load_h", "tab_manual_struct", "tab_debug",
        # control labels
        "label_unit_size", "label_endianness", "label_display_mode", "label_target_struct",
        "label_gui_version", "label_search", "label_filter", "label_struct_name", "label_total_size_bytes",
        # buttons used
        "browse_button", "parse_button", "export_csv_button",
        "btn_expand_all", "btn_collapse_all", "btn_expand_selected", "btn_collapse_selected",
        "btn_batch_delete", "btn_add_member", "btn_export_h", "btn_reset", "btn_delete", "btn_move_up",
        "btn_move_down", "btn_copy",
        # treeview headers
        "member_col_name", "member_col_value", "member_col_hex_value", "member_col_hex_raw",
        "layout_col_name", "layout_col_type", "layout_col_offset", "layout_col_size",
        "layout_col_bit_offset", "layout_col_bit_size", "layout_col_is_bitfield",
        # dialogs and messages
        "dialog_error_title", "dialog_select_file", "dialog_file_error", "dialog_parsing_error",
        "dialog_export_failed_title", "dialog_export_done_title", "dialog_export_done_body",
        "dialog_context_warning_title", "dialog_not_loaded_body", "dialog_export_h_title",
        # presenter messages
        "msg_no_file_selected", "msg_not_loaded", "msg_file_load_error", "msg_input_too_long", "msg_hex_parse_error",
    }

    missing = sorted(required - keys)
    assert not missing, f"Missing keys in ui_strings.xml: {missing}"

