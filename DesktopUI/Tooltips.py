import tkinter as tk

class Tooltip:
    def __init__(self, widget, text, delay = 500, wraplength = 480):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.wraplength = wraplength

        self.after_id = None
        self.window = None

        widget.bind("<Enter>", self.Schedule, add="+")
        widget.bind("<Leave>", self.Hide, add="+")
        widget.bind("<ButtonPress>", self.Hide, add="+")
        widget.bind("<KeyPress>", self.Hide, add="+")
        widget.bind("<Unmap>", self.Hide, add="+")
        widget.bind("<Destroy>", self.OnDestroy, add="+")

    def Schedule(self, event = None):
        self.Hide()
        self.after_id = self.widget.after(self.delay, self.Show)

    def Show(self):
        self.after_id = None
        if not self.widget.winfo_exists() or not self.widget.winfo_viewable():
            return

        self.window = tk.Toplevel(self.widget)
        self.window.withdraw()
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)

        label = tk.Label(self.window, text=self.text, justify="left",
            anchor="w", background="#fff8d6", foreground="#202020",
            relief="solid", borderwidth=1, padx=10, pady=8,
            wraplength=self.wraplength)
        label.pack()

        self.window.update_idletasks()

        width = self.window.winfo_reqwidth()
        height = self.window.winfo_reqheight()

        pointer_x = self.widget.winfo_pointerx()
        pointer_y = self.widget.winfo_pointery()

        left = self.widget.winfo_vrootx()
        top = self.widget.winfo_vrooty()
        right = left + self.widget.winfo_vrootwidth()
        bottom = top + self.widget.winfo_vrootheight()

        x = pointer_x + 16
        y = pointer_y + 20

        if y + height > bottom - 8:
            y = pointer_y - height - 12

        x = max(left + 8, min(x, right - width - 8))
        y = max(top + 8, min(y, bottom - height - 8))

        self.window.geometry(f"+{x}+{y}")
        self.window.deiconify()

    def Hide(self, event = None):
        if self.after_id is not None:
            try:
                self.widget.after_cancel(self.after_id)
            except tk.TclError:
                pass
            self.after_id = None

        if self.window is not None:
            try:
                self.window.destroy()
            except tk.TclError:
                pass
            self.window = None
    
    def OnDestroy(self, event):
        if event.widget is self.widget:
            self.Hide()

def AddToolTip(widget, text):
    tooltip = Tooltip(widget, text)
    return tooltip


