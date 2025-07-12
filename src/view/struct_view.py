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

        # 在手動設定Tab建立UI
        self._create_manual_struct_frame(self.tab_manual)

    def _create_manual_struct_frame(self, parent):
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
            tk.Button(self.bitfield_frame, text="刪除", command=lambda i=idx: self._delete_bitfield(i)).grid(row=idx+1, column=3)
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