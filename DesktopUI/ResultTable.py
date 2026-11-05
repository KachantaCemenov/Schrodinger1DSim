from tkinter import ttk


class ResultTable(ttk.Frame):

    def __init__(self, parent):
        super().__init__(parent)

        self.tree = ttk.Treeview(self, show="headings")

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)

        self.tree.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")

        self.tree.pack(
            side="left",
            fill="both",
            expand=True
        )



    def LoadDataFrame(self, dataframe):

        # Clear previous contents
        self.tree.delete(*self.tree.get_children())

        columns = list(dataframe.columns)

        self.tree["columns"] = columns

        for column in columns:

            self.tree.heading(
                column,
                text=column
            )

            self.tree.column(
                column,
                width=110
            )

        for _, row in dataframe.iterrows():

            self.tree.insert(
                "",
                "end",
                values=list(row)
            )