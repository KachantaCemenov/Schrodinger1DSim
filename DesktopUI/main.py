from pathlib import Path
import sys


if not getattr(sys, "frozen", False):
    project_folder = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_folder))


from MainWindow import MainWindow


if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()