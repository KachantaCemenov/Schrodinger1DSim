import tkinter as tk
from tkinter import ttk
"""
Script exist to give the config area in Simulation tab a scrollable frame
"""

class ScrollableFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(self, highlightthickness = 0, borderwidth = 0,
                                width = 350, height = 300, yscrollincrement = 20)
        self.canvas.grid(row = 0, column = 0, sticky = "nsew")

        scrollbar = ttk.Scrollbar(self, orient = "vertical", command = self.canvas.yview)
        scrollbar.grid(row = 0, column = 1, sticky = "ns")

        self.canvas.configure(yscrollcommand = scrollbar.set)

        self.content = ttk.Frame(self.canvas)
        self.content_window = self.canvas.create_window((0, 0), window = self.content,anchor = "nw")

        self.content.bind("<Configure>", self.UpdateScrollRegion)
        self.canvas.bind("<Configure>", self.UpdateContentWidth)

        # scroll only when the mouse is over this scrollable area
        self.root_window = self.winfo_toplevel()
        self.wheel_binding = self.root_window.bind("<MouseWheel>", self.OnMouseWheel, add = "+")

        self.bind("<Destroy>", self.OnDestroy, add="+")

    def UpdateScrollRegion(self, event=None):
        self.canvas.configure(
            scrollregion=self.canvas.bbox("all")
        )

    def UpdateContentWidth(self, event):
        self.canvas.itemconfigure(self.content_window, width = event.width)

    def OnMouseWheel(self, event):
        hovered = self.winfo_containing(event.x_root, event.y_root)

        # Preserve the dropdown's own mouse-wheel behavior.
        if isinstance(hovered, ttk.Combobox):
            return

        widget = hovered
        while widget is not None and widget is not self:
            widget = widget.master

        if widget is not self:
            return

        first, last = self.canvas.yview()
        if first <= 0 and last >= 1:
            return

        if event.delta:
            direction = -1 if event.delta > 0 else 1
            steps = max(1, abs(int(event.delta / 120)))
            self.canvas.yview_scroll(direction * steps, "units")
            return "break"

    def OnDestroy(self, event):
        if event.widget is self and self.wheel_binding:
            self.root_window.unbind("<MouseWheel>", self.wheel_binding)
            self.wheel_binding = None