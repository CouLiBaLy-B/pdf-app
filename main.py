#!/usr/bin/env python3
"""
Point d'entrée principal de l'éditeur PDF
"""
import tkinter as tk
from ui.main_window import PDFEditorMainWindow


def main():
    root = tk.Tk()
    app = PDFEditorMainWindow(root)

    def on_closing():
        app.cleanup()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
