import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
import random
import time
from tkinter import ttk
from backend.m1_pesanan import Array
from backend.m3_laporan import merge_sort, binary_search, linear_search, insertion_sort

class Pesanan:
    def __init__(self, oid, pelanggan, menu, harga):
        self.oid = oid
        self.pelanggan = pelanggan
        self.resto = "Nasi Imoet"
        self.menu = menu
        self.harga = harga
        self.prioritas = random.randint(1, 3)
        self.masuk = "10:00:00"
        self.status = "ANTRE"

    def __eq__(self, other):
        if isinstance(other, str): return self.oid == other
        return self.oid == other.oid
        
    def __lt__(self, other):
        if isinstance(other, str): return self.oid < other
        return self.oid < other.oid
        
    def __le__(self, other):
        if isinstance(other, str): return self.oid <= other
        return self.oid <= other.oid

class Aplikasi2EZ4U:
    def __init__(self, root):
        self.root = root
        self.root.title("2EZ4U Food Delivery")
        self.root.geometry("1100x750")
        
        # --- 1. HEADER (TOP BAR) ---
        header = tk.Frame(root, bg="#2c405a", height=40)
        header.pack(side=tk.TOP, fill=tk.X)
        tk.Label(header, text="2EZ4U Food Delivery", bg="#2c405a", fg="white", 
                 font=("Arial", 12, "bold")).pack(side=tk.LEFT, padx=10, pady=5)

        # --- CONTAINER UTAMA ---
        main_frame = tk.Frame(root)
        main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # --- 2. PANEL KIRI (SIDEBAR MENU M1 - M4) ---
        left_panel = tk.Frame(main_frame, width=280, bg="#f0f0f0", relief=tk.SUNKEN, borderwidth=1)
        left_panel.pack(side=tk.LEFT, fill=tk.Y)
        
        # Setup Scrollbar untuk Panel Kiri
        canvas = tk.Canvas(left_panel, bg="#f0f0f0", width=250)
        scrollbar = ttk.Scrollbar(left_panel, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#f0f0f0")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        # Untuk Linux (Ubuntu/Debian/WSL):
        canvas.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))
        
        # Untuk Windows / macOS:
        canvas.bind("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        def _on_mousewheel(event):
            if event.num == 4:
                canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                canvas.yview_scroll(1, "units")
            else:
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        def bind_mouse_wheel(widget):
            widget.bind("<MouseWheel>", _on_mousewheel, add="+")
            widget.bind("<Button-4>", _on_mousewheel, add="+")
            widget.bind("<Button-5>", _on_mousewheel, add="+")
            for child in widget.winfo_children():
                bind_mouse_wheel(child)

        self.buat_tombol_menu(scrollable_frame)
        bind_mouse_wheel(scrollable_frame)

        # --- 3. PANEL KANAN (FORM & TABEL KONTEN) ---
        right_panel = tk.Frame(main_frame, bg="white")
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Judul & Penjelasan
        tk.Label(right_panel, text="Search: binary search, O(log n)", font=("Arial", 14, "bold"), 
                 bg="white", anchor="w").pack(fill=tk.X)
        tk.Label(right_panel, text="Membuang separuh sisa daftar pada setiap perbandingan. Menuntut daftar yang sudah terurut menurut oid.", 
                 bg="white", fg="#555555", anchor="w").pack(fill=tk.X, pady=(0, 15))

        # Area Form Input & Tombol
        form_frame = tk.Frame(right_panel, bg="white")
        form_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(form_frame, text="Nomor pesanan (oid)", bg="white", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w")
        self.entry_oid = tk.Entry(form_frame, width=25, font=("Arial", 11))
        self.entry_oid.grid(row=1, column=0, pady=2, sticky="w")
        self.entry_oid.insert(0, "O-137442") # Placeholder bawaan
        
        btn_cari = tk.Button(form_frame, text="CARI", bg="#2c405a", fg="white", width=15, font=("Arial", 10, "bold"))
        btn_cari.grid(row=1, column=1, padx=20)
        
        tk.Label(form_frame, text="format O-000001 sampai O-200000", bg="white", fg="#777777", font=("Arial", 9)).grid(row=2, column=0, sticky="w")

        # Label Statistik Performa
        teks_statistik = (
            "Daftar terurut oid dibangun sekali dengan merge sort, 317.80 ms.\n"
            "Ditemukan pada baris ke-137.442 dari 200.001 baris.\n"
            "16 perbandingan, bandingkan dengan linear search."
        )
        tk.Label(right_panel, text=teks_statistik, bg="white", justify=tk.LEFT, anchor="w").pack(fill=tk.X, pady=15)

        # Tabel / Treeview
        columns = ("kolom", "isi")
        self.tree = ttk.Treeview(right_panel, columns=columns, show="headings", height=8)
        self.tree.heading("kolom", text="kolom")
        self.tree.heading("isi", text="isi")
        self.tree.column("kolom", width=150, anchor="w")
        self.tree.column("isi", width=400, anchor="w")
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Data Dummy seperti di modul
        dummy_data = [
            ("oid", "O-137442"), ("pelanggan", "dr. Gada Irawan"), ("resto", "kantin-pusat"),
            ("menu", "roti-bakar"), ("harga", "12.000"), ("prioritas", "2"),
            ("masuk", "11:35:01"), ("selesai", "-"), ("status", "CANCEL")
        ]
        for item in dummy_data:
            self.tree.insert("", tk.END, values=item)

        # --- 4. PANEL KANAN BAWAH (COMMAND LOG & INFO) ---
        tk.Label(right_panel, text="COMMAND", bg="white", font=("Arial", 9, "bold"), anchor="w").pack(fill=tk.X, pady=(15, 2))
        
        self.log_text = tk.Text(right_panel, height=5, font=("Courier", 10), bg="#f5f5f5")
        self.log_text.pack(fill=tk.X)
        self.log_text.insert(tk.END, "binary_search    -> M3 - binary search 0.05 ms\n")
        self.log_text.insert(tk.END, "linear_search    -> M3 - linear search 26.28 ms\n")
        self.log_text.insert(tk.END, "merge_sort       -> M3 - merge sort   9.92 ms\n")
        self.log_text.insert(tk.END, "insertion_sort   -> M3 - insertion sort 80.38 ms\n")

        # Kotak Penjelasan Kuning Pucat
        info_frame = tk.Frame(right_panel, bg="#fffae6", bd=1, relief=tk.SOLID)
        info_frame.pack(fill=tk.X, pady=10)
        teks_info = (
            "Setiap perbandingan membuang separuh sisa daftar, jadi 200.001 baris habis dalam paling banyak 18 langkah.\n"
            "Syaratnya daftar harus SUDAH terurut menurut kunci yang dicari; di sini terurut menurut oid."
        )
        tk.Label(info_frame, text=teks_info, bg="#fffae6", justify=tk.LEFT, font=("Arial", 9)).pack(padx=10, pady=8, anchor="w")

        # --- 5. FOOTER (STATUS BAR) ---
        footer = tk.Frame(root, bg="#f0f0f0")
        footer.pack(side=tk.BOTTOM, fill=tk.X)
        tk.Label(footer, text=" [M3 - binary search] 0.05 ms ", bg="#2c405a", fg="white", 
                 font=("Courier", 10, "bold")).pack(side=tk.LEFT)

        self.data_pesanan = Array()
        self.is_sorted = False

    def buat_tombol_menu(self, parent):
        menus = [
            ("DATA", ["Load"]),
            ("M1 - DATA PESANAN", [
                "ARRAY - LIHAT PESANAN", "ARRAY - TAMBAH PESANAN REGULER",
                "ARRAY - TAMBAH PESANAN PRIORITAS", "ARRAY - TAMBAH PESANAN VIP",
                "ARRAY - HAPUS PESANAN", "LINKEDLIST - LIHAT PESANAN",
                "LINKEDLIST - TAMBAH PESANAN REGULER", "LINKEDLIST - TAMBAH PESANAN PRIORITAS",
                "LINKEDLIST - TAMBAH PESANAN VIP", "LINKEDLIST - HAPUS PESANAN"
            ]),
            ("M2 - STACK DAN QUEUE", [
                "STACK - POSTFIX (MESIN KASIR)", "STACK - UNDO", "STACK - REDO",
                "QUEUE - ENQUEUE", "QUEUE - DEQUEUE NAIF", "QUEUE - DEQUEUE CIRCULAR"
            ]),
            ("M3 - SORT DAN SEARCH", [
                "SORT - INSERTION SORT", "SORT - MERGE SORT",
                "SEARCH - LINEAR SEARCH", "SEARCH - BINARY SEARCH"
            ])
        ]

        for kategori, daftar_menu in menus:
            tk.Label(parent, text=kategori, bg="#f0f0f0", font=("Arial", 8, "bold"), 
                     anchor="w").pack(fill=tk.X, pady=(15, 2), padx=5)
            for menu in daftar_menu:
                # Membuat highlight biru khusus untuk "SEARCH - BINARY SEARCH"
                bg_color = "#d9e8f5" if menu == "SEARCH - BINARY SEARCH" else "white"
                btn = tk.Button(parent, text=menu, bg=bg_color, relief=tk.SOLID, bd=1, 
                                anchor="w", font=("Arial", 8), padx=10, cursor="hand2")
                if menu == "Load":
                    btn.config(command=self.proses_load)
                elif menu == "SEARCH - LINEAR SEARCH":
                    btn.config(command=self.proses_linear_search)
                elif menu == "SEARCH - BINARY SEARCH":
                    btn.config(command=self.proses_cari) # Memakai proses_cari yang sudah menampilkan ke tabel
                elif menu == "SORT - MERGE SORT":
                    btn.config(command=self.proses_merge_sort_menu)
                elif menu == "SORT - INSERTION SORT":
                    btn.config(command=self.proses_insertion_sort_menu)

                btn.pack(fill=tk.X, padx=5, pady=1)

                

    def proses_load(self):
        self.data_pesanan = Array() # Bersihkan wadah
        
        # Kita buat 1000 data dummy Nasi Imoet yang posisinya teracak
        daftar_menu = ["Nasi Bakar", "Nasi Kotak Spesial", "Nasi Kuning", "Tumpeng Mini"]
        daftar_nama = ["dr. Gada", "Ibu Siti", "Bapak Budi", "Pak RT", "Toko Andi"]
        
        # Menghasilkan 1000 angka acak tanpa duplikat dari 1 sampai 5000
        oids_acak = random.sample(range(1, 5001), 1000) 
        
        for num in oids_acak:
            oid_str = f"O-{num:06d}" # Format menjadi O-000123
            p = Pesanan(oid_str, random.choice(daftar_nama), random.choice(daftar_menu), 15000)
            self.data_pesanan.append(p)
            
        self.is_sorted = False
        
        # Cetak ke layar log (terminal UI)
        self.log_text.insert(tk.END, f"[DATA] Berhasil memuat {self.data_pesanan.size} baris data acak ke dalam Array M1.\n")
        self.log_text.see(tk.END)

    def proses_cari(self):
        # 1. Pastikan data sudah diload
        if self.data_pesanan.size == 0:
            self.log_text.insert(tk.END, "[ERROR] Load data terlebih dahulu!\n")
            self.log_text.see(tk.END)
            return

        target_oid = self.entry_oid.get().strip()
        if not target_oid:
            return

        # 2. Lakukan Sorting jika belum diurutkan (Syarat mutlak Binary Search)
        waktu_sort = 0
        if not self.is_sorted:
            start_sort = time.time()
            self.data_pesanan, comp_sort = merge_sort(self.data_pesanan)
            end_sort = time.time()
            waktu_sort = (end_sort - start_sort) * 1000 # konversi ke ms
            self.is_sorted = True
            
            self.log_text.insert(tk.END, f"merge_sort       -> M3 - merge sort {waktu_sort:.2f} ms ({comp_sort} banding)\n")

        # 3. Lakukan Binary Search
        start_search = time.time()
        idx_ketemu, comp_search = binary_search(self.data_pesanan, target_oid)
        end_search = time.time()
        waktu_search = (end_search - start_search) * 1000

        self.log_text.insert(tk.END, f"binary_search    -> M3 - binary search {waktu_search:.2f} ms ({comp_search} banding)\n")
        self.log_text.see(tk.END)

        # 4. Tampilkan ke Tabel Treeview
        # Bersihkan tabel lama
        for item in self.tree.get_children():
            self.tree.delete(item)

        if idx_ketemu != -1:
            # Ambil objek pesanan yang ditemukan
            pesanan = self.data_pesanan.get(idx_ketemu)
            
            # Masukkan detailnya ke tabel
            data_tampil = [
                ("oid", pesanan.oid),
                ("pelanggan", pesanan.pelanggan),
                ("resto", pesanan.resto),
                ("menu", pesanan.menu),
                ("harga", str(pesanan.harga)),
                ("prioritas", str(pesanan.prioritas)),
                ("masuk", pesanan.masuk),
                ("selesai", "-"),
                ("status", pesanan.status)
            ]
            for item in data_tampil:
                self.tree.insert("", tk.END, values=item)
        else:
            self.tree.insert("", tk.END, values=("Hasil", "DATA TIDAK DITEMUKAN"))

    def proses_linear_search(self):
        if self.data_pesanan.size == 0: return
        target = self.entry_oid.get().strip()
        
        start = time.time()
        idx, comp = linear_search(self.data_pesanan, target)
        waktu = (time.time() - start) * 1000
        
        self.log_text.insert(tk.END, f"linear_search    -> M3 - linear search {waktu:.2f} ms ({comp} banding)\n")
        self.log_text.see(tk.END)

    def proses_merge_sort_menu(self):
        if self.data_pesanan.size == 0: return
        
        start = time.time()
        self.data_pesanan, comp = merge_sort(self.data_pesanan)
        waktu = (time.time() - start) * 1000
        self.is_sorted = True
        
        self.log_text.insert(tk.END, f"merge_sort       -> M3 - merge sort {waktu:.2f} ms ({comp} banding)\n")
        self.log_text.see(tk.END)

    def proses_insertion_sort_menu(self):
        if self.data_pesanan.size == 0: return
        
        start = time.time()
        self.data_pesanan, comp = insertion_sort(self.data_pesanan)
        waktu = (time.time() - start) * 1000
        self.is_sorted = True
        
        self.log_text.insert(tk.END, f"insertion_sort   -> M3 - insertion sort {waktu:.2f} ms ({comp} banding)\n")
        self.log_text.see(tk.END)

    

if __name__ == "__main__":
    root = tk.Tk()
    app = Aplikasi2EZ4U(root)
    root.mainloop()