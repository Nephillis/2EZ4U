import tkinter as tk
from frontend.ui import Aplikasi2EZ4U

def main():
    # Inisialisasi root window Tkinter
    root = tk.Tk()
    
    # Memanggil class utama dari ui.py yang berada di folder frontend
    app = Aplikasi2EZ4U(root)
    
    # Menjalankan main loop aplikasi
    root.mainloop()

if __name__ == "__main__":
    main()