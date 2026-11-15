import tkinter as tk
from tkinter import ttk


class ResultTable(ttk.Frame):

    def __init__(self, parent, page_size = None):
        super().__init__(parent)

        if page_size is not None:
            if type(page_size) is not int or page_size <= 0:
                raise ValueError("Page size must be a positive integer.")

        self.page_size = page_size
        self.page_index = 0
        self.dataframe = None

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        table_frame = ttk.Frame(self)
        table_frame.grid(row=0, column=0, sticky="nsew")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(self, show = "headings")
        self.tree.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(table_frame, orient = "vertical", command = self.tree.yview)
        scrollbar.grid(row = 0, column = 1, sticky = "ns")
        self.tree.configure(yscrollcommand = scrollbar.set)
        
        # Only create paging controls when pagination is needed
        if self.page_size is not None: 
            paging = ttk.Frame(self)
            paging.grid(row = 1, column = 0, sticky = "ew", pady = 5)
            paging.columnconfigure(1, weight = 1)

            self.previous_button = ttk.Button(paging, text = "Previous", command = lambda: self.ChangePage(-1), state = "disabled")
            self.previous_button.grid(row = 0, column = 0)

            self.page_text = tk.StringVar(master = self, value = "No results loaded")
            ttk.Label(paging, textvariable = self.page_text, anchor = "center").grid(row = 0, column = 1, sticky = "ew", padx = 8)

            self.next_button = ttk.Button(paging, text = "Next", command = lambda: self.ChangePage(1), state = "disabled")
            self.next_button.grid(row = 0, column = 2)

    def LoadDataFrame(self, dataframe):
        # Retain the full data. Slice when displaying pages

        self.dataframe = dataframe
        self.page_index = 0

        columns = list(dataframe.columns)
        self.tree.configure(columns = columns)

        for column in columns:
            self.tree.heading(column,text = column)
            self.tree.column(column,width = 110)

        self.RefreshPage() #Move the reset pages in there

    def RefreshPage():
        children = self.tree.get_children()
        if children:
            self.tree.delete(*children)

        total = 0 if self.dataframe is None else len(self.dataframe)

        if total == 0:
            self.page_index = 0

            if self.page_size is not None:
                self.page_text.set("No results loaded")
                self.previous_button.configure(state="disabled")
                self.next_button.configure(state="disabled")
            return

        if self.page_size is None:
            # One page
            start = 0
            end = total
        else:
            last_page = (total - 1) // self.page_size
            self.page_index = max(0, min(self.page_index, last_page))

            start = self.page_index * self.page_size
            end = min(start + self.page_size, total)

        page = self.dataframe.iloc[start:end]

        for values in page.itertuples(index = False, name = None):
            self.tree.insert("", "end", values = values)

        # Start new page at first row
        self.tree.yview_moveto(0)
        if self.page_size is not None:
            self.page_text.set(f"Rows {start + 1:,}–{end:,} of {total:,}")
            self.previous_button.configure(state = "normal" if start > 0 else "disabled")
            self.next_button.configure(state = "normal" if end < total else "disabled")

    def ChangePage(self, direction):
        if self.page_size is None or self.dataframe is None or self.dataframe.empty:
            return
        last_page = (len(self.dataframe) - 1) // self.page_size
        new_page = max(0, min(self.page_index + direction, last_page))

        if new_page == self.page_index:
            return

        self.page_index = new_page
        self.RefreshPage()