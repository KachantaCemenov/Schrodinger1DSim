import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from HelpWindowText import HELP_TOPICS

"""HELP_TOPICS = [
    (
        "Topic 1",
        "TODO: Write the first topic here.\n\n"
        "explanations, instructions, examples.",
    ),
    (
        "Topic 2",
        "TODO: Write the second topic here.",
    ),
    (
        "Topic 3",
        "TODO: Write the third topic here.",
    ),
    (
        "Topic 4",
        "TODO: Write the fourth topic here.",
    ),
]"""


class HelpWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)

        self.title("Help")
        self.geometry("800x600")
        self.minsize(500, 350)
        self.transient(parent)

        container = ttk.Frame(self, padding=10)
        container.pack(fill="both", expand=True)

        notebook = ttk.Notebook(container)
        notebook.pack(fill="both", expand=True)

        for title, content in HELP_TOPICS:
            tab = ttk.Frame(notebook, padding=8)
            notebook.add(tab, text=title)

            text = ScrolledText(tab, wrap = "word", font = ("Segoe UI", 11), padx = 12, pady = 12,
                relief="flat", borderwidth = 0, width = 60, height = 20)
            text.pack(fill="both", expand=True)

            #Configure some tags for formatting
            text.tag_configure("title", font = ("Segoe UI", 18, "bold"), spacing3 = 12)
            text.tag_configure("heading", font = ("Segoe UI", 13, "bold"), spacing1 = 10, spacing3 = 6)
            text.tag_configure("bold", font = ("Segoe UI", 11, "bold"))
            text.tag_configure("italic", font=("Segoe UI", 11, "italic"))
            text.tag_configure("bullet", lmargin1 = 15, lmargin2 = 32, spacing3 = 4)

            for paragraph, tag in content:
                if tag is None:
                    text.insert("end", paragraph)
                else:
                    text.insert("end", paragraph, (tag,))
            text.configure(state = "disabled")

        ttk.Button(container, text = "Close", command = self.destroy).pack(anchor = "e", pady = (10, 0))

        self.bind("<Escape>", lambda event: self.destroy())