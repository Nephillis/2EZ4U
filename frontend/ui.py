import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import tkinter as tk
from tkinter import ttk

import backend.m2_antrean as m2
from backend.m1_pesanan import Array, LinkedList
from backend.m2_antrean import Stack, splitToken, cek_prioritas, postfix, hitung
from backend.m3_laporan import insertion_sort, merge_sort, linear_search, binary_search

# Aturan proyek: tanpa dict, set, sorted(), .sort(), heapq, bisect, collections, literal {}.
# Semua struktur di berkas ini memakai list/tuple biasa dan struktur buatan sendiri (backend/).

BATAS_INSERTION = 20000       # insertion sort menolak data lebih besar dari ini (tidak membeku)
SELESAI_KOSONG = 10 ** 9      # pesanan tanpa waktu selesai diurutkan paling belakang
BARIS_TAMPIL = 20             # jumlah baris hasil sort yang ditampilkan di tabel
WARNA_NAVY = "#2c405a"
WARNA_MENU_AKTIF = "#d9e8f5"


# =====================================================================
# Fungsi bantu format tampilan
# =====================================================================
def fmt_int(n):
    """19850 -> '19.850' (pemisah ribuan titik, seperti di PDF)."""
    return f"{n:,}".replace(",", ".")


def fmt_waktu(ms):
    if ms >= 1000:
        return f"{ms / 1000:.2f} s"
    return f"{ms:.2f} ms"


def fmt_jam(detik):
    """detik sejak 00:00 -> 'HH:MM:SS'. None -> '-'."""
    if detik is None:
        return "-"
    j = detik // 3600
    m = (detik % 3600) // 60
    s = detik % 60
    return f"{j:02d}:{m:02d}:{s:02d}"


def fmt_angka(x):
    """Angka hasil hitung: 36000.0 tampil sebagai 36000."""
    if isinstance(x, float) and x == int(x):
        return str(int(x))
    if isinstance(x, float):
        return f"{x:.2f}"
    return str(x)


def fmt_rupiah(x):
    if isinstance(x, float) and x != int(x):
        return "Rp " + f"{x:,.2f}".replace(",", "#").replace(".", ",").replace("#", ".")
    n = int(x)
    if n < 0:
        return "-Rp " + fmt_int(-n)
    return "Rp " + fmt_int(n)


def pecah_csv(baris):
    """Memecah satu baris CSV TANPA library csv.
    Nama seperti "Oskar Puspita, S.Sos" memuat koma di dalam tanda kutip,
    jadi koma di dalam kutip tidak boleh dianggap pemisah kolom."""
    if '"' not in baris:
        return baris.split(",")

    hasil = []
    sekarang = ""
    dalam_kutip = False
    i = 0
    n = len(baris)
    while i < n:
        c = baris[i]
        if dalam_kutip:
            if c == '"':
                if i + 1 < n and baris[i + 1] == '"':   # "" di dalam kutip = satu tanda kutip
                    sekarang += '"'
                    i += 1
                else:
                    dalam_kutip = False
            else:
                sekarang += c
        else:
            if c == '"':
                dalam_kutip = True
            elif c == ",":
                hasil.append(sekarang)
                sekarang = ""
            else:
                sekarang += c
        i += 1
    hasil.append(sekarang)
    return hasil


# =====================================================================
# Model data
# =====================================================================
class Pesanan:
    """Satu baris pesanan.csv. Dibandingkan menurut oid (default untuk
    merge_sort / binary_search / linear_search di backend M3)."""
    __slots__ = ("oid", "pelanggan", "resto", "menu", "harga",
                 "prioritas", "masuk", "selesai", "status")

    def __init__(self, oid, pelanggan, resto, menu, harga,
                 prioritas, masuk, selesai, status):
        self.oid = oid
        self.pelanggan = pelanggan
        self.resto = resto
        self.menu = menu
        self.harga = harga            # int (rupiah)
        self.prioritas = prioritas    # 1 VIP, 2 Prioritas, 3 Reguler
        self.masuk = masuk            # int detik sejak 00:00
        self.selesai = selesai        # int detik atau None
        self.status = status          # DONE / CANCEL / ANTRE

    def __eq__(self, other):
        if isinstance(other, str):
            return self.oid == other
        return self.oid == other.oid

    def __lt__(self, other):
        if isinstance(other, str):
            return self.oid < other
        return self.oid < other.oid

    def __le__(self, other):
        if isinstance(other, str):
            return self.oid <= other
        return self.oid <= other.oid

    def __gt__(self, other):
        if isinstance(other, str):
            return self.oid > other
        return self.oid > other.oid

    def __ge__(self, other):
        if isinstance(other, str):
            return self.oid >= other
        return self.oid >= other.oid


class KunciUrut:
    """Pembungkus supaya insertion_sort / merge_sort di backend (yang membandingkan
    elemen dengan > dan <=) bisa mengurutkan menurut kunci apa pun (oid / harga / selesai).
    Operator > memakai 'lebih besar' (bukan >=) dan <= memakai 'lebih kecil sama dengan',
    jadi kestabilan sort di backend tetap terjaga untuk kunci yang sama.
    `geseran` menghitung berapa kali insertion sort benar-benar menggeser elemen."""
    __slots__ = ("pesanan", "kunci")
    geseran = 0

    def __init__(self, pesanan, kunci):
        self.pesanan = pesanan
        self.kunci = kunci

    def __gt__(self, other):
        hasil = self.kunci > other.kunci
        if hasil:
            KunciUrut.geseran += 1
        return hasil

    def __le__(self, other):
        return self.kunci <= other.kunci

    def __lt__(self, other):
        return self.kunci < other.kunci

    def __ge__(self, other):
        return self.kunci >= other.kunci

    def __eq__(self, other):
        return self.kunci == other.kunci


def ambil_kunci(p, nama_kunci):
    if nama_kunci == "harga":
        return p.harga
    if nama_kunci == "selesai":
        if p.selesai is None:
            return SELESAI_KOSONG
        return p.selesai
    return p.oid


def hitung_pemindahan_merge(n):
    """Jumlah elemen yang ditulis ke larik hasil selama merge sort n elemen
    (n + pemindahan separuh kiri + pemindahan separuh kanan)."""
    if n <= 1:
        return 0
    kiri = n // 2
    return n + hitung_pemindahan_merge(kiri) + hitung_pemindahan_merge(n - kiri)


# =====================================================================
# Mesin kasir (M2): validasi + jejak langkah infix -> postfix -> total
# =====================================================================
def validasi_infix(teks):
    """Mengembalikan pesan galat (str) bila ekspresi tidak valid, None bila valid.
    Perlu karena postfix() di backend akan berputar tanpa henti bila ada ')' berlebih."""
    if teks.strip() == "":
        return "Struk kosong. Contoh: ( 3 * 12000 ) + ( 2 * 8500 ) - 5000"
    for ch in teks:
        if ch not in "0123456789+-*/() ":
            return "Karakter '" + ch + "' tidak dikenali. Gunakan angka, + - * / dan tanda kurung."

    token = splitToken(teks)
    kedalaman = 0
    harap_operand = True
    for i in range(token.size):
        t = token.get(i)
        if t.isdigit():
            if not harap_operand:
                return "Ada dua angka berurutan tanpa operator di antaranya."
            harap_operand = False
        elif t == "(":
            if not harap_operand:
                return "Tanda ( muncul tepat setelah angka; operatornya hilang?"
            kedalaman += 1
        elif t == ")":
            if harap_operand:
                return "Tanda ) muncul sebelum operand selesai (ada operand yang hilang)."
            kedalaman -= 1
            if kedalaman < 0:
                return "Tanda ) berlebih: tidak ada ( pasangannya."
        else:
            if harap_operand:
                return "Operator '" + t + "' tidak punya operand di sebelah kirinya."
            harap_operand = True
    if kedalaman != 0:
        return "Tanda kurung tidak seimbang: ada ( yang belum ditutup."
    if harap_operand:
        return "Struk berakhir tanpa operand."
    return None


def isi_larik_teks(arr):
    """Larik/stack -> teks 'a b c'. Kosong -> 'kosong'."""
    if arr.size == 0:
        return "kosong"
    teks = ""
    for i in range(arr.size):
        if i > 0:
            teks += " "
        teks += fmt_angka(arr.get(i))
    return teks


def jejak_kasir(ekspresi):
    """Menjalankan konversi infix->postfix lalu evaluasi, dan merekam tiap langkah.
    Memakai Stack dan Array buatan sendiri (backend M1/M2), tidak ada struktur bawaan.
    Mengembalikan list of tuple (langkah, token, tindakan, stack, output)."""
    baris = []
    token = splitToken(ekspresi)
    st = Stack()
    keluar = Array()

    # ---- Tahap 1: infix -> postfix ----
    for i in range(token.size):
        t = token.get(i)
        no = "1." + str(i + 1)
        if t.isdigit():
            keluar.append(t)
            tindakan = "operand, langsung ke output"
        elif t == "(":
            st.push(t)
            tindakan = "push ( ke stack"
        elif t == ")":
            dibuang = ""
            while st.peek() != "(":
                x = st.pop()
                keluar.append(x)
                dibuang += x + " "
            st.pop()
            if dibuang == "":
                dibuang = "(kosong) "
            tindakan = "pop sampai ( : " + dibuang.strip() + ", lalu buang ("
        else:
            dibuang = ""
            while not st.is_empty() and cek_prioritas(st.peek()) >= cek_prioritas(t):
                x = st.pop()
                keluar.append(x)
                dibuang += x + " "
            st.push(t)
            if dibuang == "":
                tindakan = "push " + t
            else:
                tindakan = "pop " + dibuang.strip() + ", lalu push " + t
        baris.append((no, t, tindakan, isi_larik_teks(st.data), isi_larik_teks(keluar)))

    sisa = ""
    while not st.is_empty():
        x = st.pop()
        keluar.append(x)
        sisa += x + " "
    if sisa == "":
        sisa = "(kosong)"
    baris.append(("1.akhir", "-", "pop sisa stack: " + sisa.strip(),
                  isi_larik_teks(st.data), isi_larik_teks(keluar)))

    # ---- Tahap 2: evaluasi postfix ----
    sv = Stack()
    for i in range(keluar.size):
        t = keluar.get(i)
        no = "2." + str(i + 1)
        if t.isdigit():
            sv.push(int(t))
            tindakan = "operand, push " + t
            nilai = t
        else:
            b = sv.pop()          # operand KANAN keluar lebih dulu
            a = sv.pop()
            if t == "+":
                r = a + b
            elif t == "-":
                r = a - b
            elif t == "*":
                r = a * b
            else:
                r = a / b         # b == 0 -> ZeroDivisionError, ditangkap pemanggil
            sv.push(r)
            tindakan = ("pop " + fmt_angka(b) + " dan " + fmt_angka(a) + " -> " +
                        fmt_angka(a) + t + fmt_angka(b) + " = " + fmt_angka(r))
            nilai = fmt_angka(r)
        baris.append((no, t, tindakan, isi_larik_teks(sv.data), nilai))
    return baris


# =====================================================================
# Aplikasi
# =====================================================================
class Aplikasi2EZ4U:
    def __init__(self, root):
        self.root = root
        self.root.title("2EZ4U Food Delivery")
        self.root.geometry("1180x780")
        self.root.minsize(900, 600)

        # ---- state aplikasi ----
        self.arr = Array()            # M1: Array  (juga dipakai M3 sebagai data laporan)
        self.ll = LinkedList()        # M1: LinkedList (data yang sama)
        self.termuat = False
        self.indeks_oid = None        # M3: daftar terurut oid untuk binary search (dibangun sekali)
        self.oid_berikut = 1          # nomor oid untuk pesanan baru
        self.input_widgets = []       # widget input pada form yang sedang tampil
        self.tombol_menu = []         # (nama_menu, widget tombol) untuk highlight menu aktif

        self.bangun_ui()
        self.halaman_awal()

    # -----------------------------------------------------------------
    # Pembangunan antarmuka
    # -----------------------------------------------------------------
    def bangun_ui(self):
        style = ttk.Style()
        style.configure("Treeview", rowheight=22)

        # 1. HEADER
        header = tk.Frame(self.root, bg=WARNA_NAVY, height=40)
        header.pack(side=tk.TOP, fill=tk.X)
        tk.Label(header, text="2EZ4U Food Delivery", bg=WARNA_NAVY, fg="white",
                 font=("Arial", 12, "bold")).pack(side=tk.LEFT, padx=10, pady=8)

        # 5. FOOTER / STATUS BAR (dipack dulu supaya tidak terdorong keluar jendela)
        footer = tk.Frame(self.root, bg="#f0f0f0")
        footer.pack(side=tk.BOTTOM, fill=tk.X)
        self.lbl_status = tk.Label(footer, text=" [ siap ] ", bg=WARNA_NAVY, fg="white",
                                   font=("Courier", 10, "bold"))
        self.lbl_status.pack(side=tk.LEFT, padx=4, pady=3)

        main_frame = tk.Frame(self.root)
        main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # 2. PANEL KIRI: daftar menu
        left_panel = tk.Frame(main_frame, width=280, bg="#f0f0f0", relief=tk.SUNKEN, borderwidth=1)
        left_panel.pack(side=tk.LEFT, fill=tk.Y)

        canvas = tk.Canvas(left_panel, bg="#f0f0f0", width=262, highlightthickness=0)
        scrollbar = ttk.Scrollbar(left_panel, orient="vertical", command=canvas.yview)
        frame_menu = tk.Frame(canvas, bg="#f0f0f0")
        id_jendela = canvas.create_window((0, 0), window=frame_menu, anchor="nw")
        frame_menu.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(id_jendela, width=e.width))
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        def gulir(event):
            if event.num == 4:
                arah = -1
            elif event.num == 5:
                arah = 1
            elif event.delta > 0:
                arah = -1
            else:
                arah = 1
            canvas.yview_scroll(arah, "units")

        def pasang_gulir(widget):
            widget.bind("<MouseWheel>", gulir, add="+")
            widget.bind("<Button-4>", gulir, add="+")
            widget.bind("<Button-5>", gulir, add="+")
            for anak in widget.winfo_children():
                pasang_gulir(anak)

        self.buat_tombol_menu(frame_menu)
        pasang_gulir(canvas)
        pasang_gulir(frame_menu)

        # 3. PANEL KANAN: judul, form, hasil, tabel, COMMAND, penjelasan
        right = tk.Frame(main_frame, bg="white")
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=15, pady=10)

        # -- bagian bawah dipack lebih dulu (side=BOTTOM) agar selalu terlihat --
        self.info_frame = tk.Frame(right, bg="#fffae6", bd=1, relief=tk.SOLID)
        self.info_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(8, 0))
        self.lbl_hint = tk.Label(self.info_frame, text="", bg="#fffae6", justify=tk.LEFT,
                                 anchor="w", font=("Arial", 9), wraplength=700)
        self.lbl_hint.pack(fill=tk.X, padx=10, pady=6)
        self.info_frame.bind("<Configure>",
                             lambda e: self.lbl_hint.config(wraplength=max(200, e.width - 30)))

        log_frame = tk.Frame(right, bg="white")
        log_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.log_text = tk.Text(log_frame, height=5, font=("Courier", 10), bg="#f5f5f5",
                                state=tk.DISABLED, wrap=tk.NONE)
        log_sb = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_sb.set)
        log_sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Label(right, text="COMMAND", bg="white", font=("Arial", 9, "bold"),
                 anchor="w").pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 2))

        # -- bagian atas --
        self.lbl_judul = tk.Label(right, text="", font=("Arial", 14, "bold"), bg="white", anchor="w")
        self.lbl_judul.pack(fill=tk.X)
        self.lbl_deskripsi = tk.Label(right, text="", bg="white", fg="#555555", anchor="w",
                                      justify=tk.LEFT, font=("Arial", 9))
        self.lbl_deskripsi.pack(fill=tk.X, pady=(0, 8))

        self.form_frame = tk.Frame(right, bg="white")
        self.form_frame.pack(fill=tk.X, pady=2)

        self.lbl_hasil = tk.Label(right, text="", bg="white", justify=tk.LEFT, anchor="w",
                                  font=("Arial", 10), wraplength=700)
        self.lbl_hasil.pack(fill=tk.X, pady=(10, 6))
        right.bind("<Configure>", lambda e: self.atur_wrap(e.width))

        frame_tabel = tk.Frame(right, bg="white")
        frame_tabel.pack(fill=tk.BOTH, expand=True)
        self.tree = ttk.Treeview(frame_tabel, show="headings", height=8, selectmode="browse")
        sb_tree = ttk.Scrollbar(frame_tabel, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb_tree.set)
        sb_tree.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def atur_wrap(self, lebar):
        w = max(300, lebar - 20)
        self.lbl_hasil.config(wraplength=w)
        self.lbl_deskripsi.config(wraplength=w)

    def buat_tombol_menu(self, parent):
        menus = [
            ("DATA", ["Load"]),
            ("M1 - DATA PESANAN", [
                "ARRAY - LIHAT PESANAN", "ARRAY - TAMBAH PESANAN REGULER",
                "ARRAY - TAMBAH PESANAN PRIORITAS", "ARRAY - TAMBAH PESANAN VIP",
                "ARRAY - HAPUS PESANAN", "LINKEDLIST - LIHAT PESANAN",
                "LINKEDLIST - TAMBAH PESANAN REGULER", "LINKEDLIST - TAMBAH PESANAN PRIORITAS",
                "LINKEDLIST - TAMBAH PESANAN VIP", "LINKEDLIST - HAPUS PESANAN"]),
            ("M2 - STACK DAN QUEUE", [
                "STACK - POSTFIX (MESIN KASIR)", "STACK - UNDO", "STACK - REDO",
                "QUEUE - ENQUEUE", "QUEUE - DEQUEUE NAIF", "QUEUE - DEQUEUE CIRCULAR"]),
            ("M3 - SORT DAN SEARCH", [
                "SORT - INSERTION SORT", "SORT - MERGE SORT",
                "SEARCH - LINEAR SEARCH", "SEARCH - BINARY SEARCH"]),
        ]
        for kategori, daftar in menus:
            tk.Label(parent, text=kategori, bg="#f0f0f0", font=("Arial", 8, "bold"),
                     anchor="w").pack(fill=tk.X, pady=(12, 2), padx=5)
            for nama in daftar:
                btn = tk.Button(parent, text=nama, bg="white", relief=tk.SOLID, bd=1,
                                anchor="w", font=("Arial", 8), padx=10, cursor="hand2",
                                command=lambda n=nama: self.pilih_menu(n))
                btn.pack(fill=tk.X, padx=5, pady=1)
                self.tombol_menu.append((nama, btn))

    def tandai_menu(self, nama_aktif):
        for nama, btn in self.tombol_menu:
            if nama == nama_aktif:
                btn.config(bg=WARNA_MENU_AKTIF)
            else:
                btn.config(bg="white")

    # -----------------------------------------------------------------
    # Fungsi bantu tampilan (form, hasil, tabel, log)
    # -----------------------------------------------------------------
    def siapkan_halaman(self, judul, deskripsi, fields, label_tombol, aksi, hint):
        """Mengganti isi panel kanan. `fields` = list of tuple:
        ("entry", label, default, lebar, bantuan) atau ("combo", label, default, pilihan, bantuan)."""
        self.lbl_judul.config(text=judul)
        self.lbl_deskripsi.config(text=deskripsi)
        self.lbl_hint.config(text=hint)
        self.tampil_hasil("")
        self.tampil_tabel(("kolom", "isi"), (160, 420), [])

        for w in self.form_frame.winfo_children():
            w.destroy()
        self.input_widgets = []

        kolom = 0
        for f in fields:
            jenis, label, default, opsi, bantuan = f
            tk.Label(self.form_frame, text=label, bg="white",
                     font=("Arial", 10, "bold")).grid(row=0, column=kolom, sticky="w", padx=(0, 18))
            if jenis == "combo":
                w = ttk.Combobox(self.form_frame, values=opsi, state="readonly", width=14)
                w.set(default)
            else:
                w = tk.Entry(self.form_frame, width=opsi, font=("Arial", 11))
                w.insert(0, default)
                if aksi is not None:
                    w.bind("<Return>", lambda e: aksi())
            w.grid(row=1, column=kolom, sticky="w", padx=(0, 18), pady=2)
            tk.Label(self.form_frame, text=bantuan, bg="white", fg="#888888",
                     font=("Arial", 8)).grid(row=2, column=kolom, sticky="w", padx=(0, 18))
            self.input_widgets.append(w)
            kolom += 1

        if label_tombol is not None:
            tk.Button(self.form_frame, text=label_tombol, bg=WARNA_NAVY, fg="white",
                      width=16, font=("Arial", 10, "bold"), cursor="hand2",
                      command=aksi).grid(row=1, column=kolom, padx=10)

    def ambil(self, i):
        return self.input_widgets[i].get()

    def tampil_hasil(self, teks, galat=False):
        self.lbl_hasil.config(text=teks, fg="#b00020" if galat else "black")

    def tampil_tabel(self, kolom, lebar, baris):
        """kolom: tuple id kolom. Kolom berid 'no' diberi judul '#'."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.tree["columns"] = kolom
        for i in range(len(kolom)):
            judul = "#" if kolom[i] == "no" else kolom[i]
            self.tree.heading(kolom[i], text=judul)
            self.tree.column(kolom[i], width=lebar[i], minwidth=40, anchor="w", stretch=True)
        for b in baris:
            self.tree.insert("", tk.END, values=b)

    def catat(self, perintah, modul, ms):
        """Satu baris di panel COMMAND (terbaru di paling atas) + status bar."""
        teks = f"{perintah:<28}-> {modul:<22}{fmt_waktu(ms)}\n"
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert("1.0", teks)
        self.log_text.config(state=tk.DISABLED)
        self.lbl_status.config(text=f" [{modul}] {fmt_waktu(ms)} ")

    def sibuk(self, pesan):
        self.tampil_hasil(pesan)
        self.root.config(cursor="watch")
        self.root.update()

    def selesai_sibuk(self):
        self.root.config(cursor="")

    def cek_data(self):
        if not self.termuat:
            self.tampil_hasil("Data belum dimuat. Klik tombol Load di panel kiri terlebih dahulu.", galat=True)
            return False
        return True

    def baca_int(self, i, nama_isian):
        teks = self.ambil(i).strip().replace(".", "")
        try:
            nilai = int(teks)
        except ValueError:
            self.tampil_hasil(nama_isian + " harus berupa bilangan bulat, misalnya 100.", galat=True)
            return None
        if nilai < 1:
            self.tampil_hasil(nama_isian + " minimal 1.", galat=True)
            return None
        return nilai

    def baris_detail(self, p):
        return [("oid", p.oid), ("pelanggan", p.pelanggan), ("resto", p.resto),
                ("menu", p.menu), ("harga", fmt_int(p.harga)), ("prioritas", str(p.prioritas)),
                ("masuk", fmt_jam(p.masuk)), ("selesai", fmt_jam(p.selesai)),
                ("status", p.status)]

    def tampil_detail(self, p):
        self.tampil_tabel(("kolom", "isi"), (160, 420), self.baris_detail(p))

    def buat_pesanan(self, nama, prioritas):
        oid = "O-" + f"{self.oid_berikut:06d}"
        self.oid_berikut += 1
        t = time.localtime()
        detik = t.tm_hour * 3600 + t.tm_min * 60 + t.tm_sec
        return Pesanan(oid, nama, "kafe-teknik", "roti-bakar", 12000, prioritas, detik, None, "ANTRE")

    def teks_panjang_antrean(self):
        return (f"naif {fmt_int(m2.naive_queue.data.size)}, "
                f"circular {fmt_int(m2.circular_queue.count)}")

    def teks_tumpukan(self):
        return (f"undo {m2.stack_undo.data.size}, redo {m2.stack_redo.data.size}")

    # -----------------------------------------------------------------
    # Navigasi menu
    # -----------------------------------------------------------------
    def halaman_awal(self):
        self.siapkan_halaman(
            "Selamat Datang di 2EZ4U",
            "Pilih menu di panel kiri. Mulailah dengan tombol Load untuk memuat data/pesanan.csv.",
            [], None, None,
            "Panel COMMAND di bawah mencatat setiap perintah yang sudah dijalankan beserta modul dan waktunya.")

    def pilih_menu(self, nama):
        self.tandai_menu(nama)
        if nama == "Load":
            self.aksi_load()
        elif nama.startswith("ARRAY - ") or nama.startswith("LINKEDLIST - "):
            bagian = nama.split(" - ", 1)
            struktur = bagian[0]
            aksi = bagian[1]
            if aksi == "LIHAT PESANAN":
                self.halaman_lihat(struktur)
            elif aksi == "TAMBAH PESANAN REGULER":
                self.halaman_tambah(struktur, "REGULER")
            elif aksi == "TAMBAH PESANAN PRIORITAS":
                self.halaman_tambah(struktur, "PRIORITAS")
            elif aksi == "TAMBAH PESANAN VIP":
                self.halaman_tambah(struktur, "VIP")
            elif aksi == "HAPUS PESANAN":
                self.halaman_hapus(struktur)
        elif nama == "STACK - POSTFIX (MESIN KASIR)":
            self.halaman_kasir()
        elif nama == "STACK - UNDO":
            self.halaman_undo()
        elif nama == "STACK - REDO":
            self.halaman_redo()
        elif nama == "QUEUE - ENQUEUE":
            self.halaman_enqueue()
        elif nama == "QUEUE - DEQUEUE NAIF":
            self.halaman_dequeue_naif()
        elif nama == "QUEUE - DEQUEUE CIRCULAR":
            self.halaman_dequeue_circular()
        elif nama == "SORT - INSERTION SORT":
            self.halaman_sort("INSERTION")
        elif nama == "SORT - MERGE SORT":
            self.halaman_sort("MERGE")
        elif nama == "SEARCH - LINEAR SEARCH":
            self.halaman_linear()
        elif nama == "SEARCH - BINARY SEARCH":
            self.halaman_binary()

    # -----------------------------------------------------------------
    # DATA: Load
    # -----------------------------------------------------------------
    def aksi_load(self):
        self.siapkan_halaman(
            "Data: muat pesanan.csv",
            "Dibaca baris demi baris tanpa library csv, lalu disimpan ke Array dan LinkedList sekaligus.",
            [], None, None,
            "Pesanan berstatus ANTRE otomatis dimasukkan ke KEDUA antrean (naif dan circular) dengan isi yang sama persis, "
            "supaya perbandingan di menu M2 jujur. Tumpukan undo/redo dikosongkan setiap kali Load.")
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(base_dir, "data", "pesanan.csv")
        if not os.path.exists(path):
            self.tampil_hasil("File pesanan.csv tidak ditemukan di: " + path, galat=True)
            return

        self.sibuk("Memuat data, mohon tunggu...")
        try:
            t0 = time.perf_counter()
            arr = Array()
            ll = LinkedList()
            dilewati = 0
            maks_oid = 0
            with open(path, "r", encoding="utf-8-sig") as f:
                pertama = True
                for baris in f:
                    if pertama:                       # lewati header
                        pertama = False
                        continue
                    baris = baris.rstrip("\r\n")
                    if baris == "":
                        continue
                    k = pecah_csv(baris)
                    if len(k) < 9:
                        dilewati += 1
                        continue
                    try:
                        selesai = None
                        if k[7].strip() != "":
                            selesai = int(k[7])
                        p = Pesanan(k[0].strip(), k[1].strip(), k[2].strip(), k[3].strip(),
                                    int(k[4]), int(k[5]), int(k[6]), selesai, k[8].strip())
                        nomor = int(p.oid[2:])
                    except ValueError:
                        dilewati += 1
                        continue
                    if nomor > maks_oid:
                        maks_oid = nomor
                    arr.append(p)
                    ll.append(p)
            ms_load = (time.perf_counter() - t0) * 1000

            # reset seluruh keadaan M2 lalu isi kedua antrean dengan pesanan ANTRE
            m2.stack_undo = m2.Stack()
            m2.stack_redo = m2.Stack()
            m2.naive_queue = m2.NaiveQueue()
            m2.circular_queue = m2.CircularQueue()
            masuk_antrean = 0
            terpotong = 0
            for i in range(arr.size):
                p = arr.get(i)
                if p.status == "ANTRE":
                    if m2.circular_queue.count >= m2.circular_queue.capacity:
                        terpotong += 1
                        continue
                    m2.naive_queue.enqueue(p)
                    m2.circular_queue.enqueue(p)
                    masuk_antrean += 1
        except Exception as e:
            self.selesai_sibuk()
            self.tampil_hasil("Gagal memuat CSV: " + str(e), galat=True)
            return
        self.selesai_sibuk()

        self.arr = arr
        self.ll = ll
        self.indeks_oid = None
        self.oid_berikut = maks_oid + 1
        self.termuat = True

        teks = (f"{fmt_int(arr.size)} pesanan dimuat ke Array dan LinkedList ({fmt_waktu(ms_load)}).\n"
                f"{fmt_int(masuk_antrean)} pesanan berstatus ANTRE masuk ke KEDUA antrean "
                f"(naif dan circular, kapasitas circular {fmt_int(m2.circular_queue.capacity)}).")
        if dilewati > 0:
            teks += f"\n{fmt_int(dilewati)} baris rusak dilewati."
        if terpotong > 0:
            teks += f"\n{fmt_int(terpotong)} pesanan ANTRE tidak muat di antrean circular dan tidak dimasukkan."
        self.tampil_hasil(teks)

        baris = []
        for i in range(min(10, arr.size)):
            p = arr.get(i)
            baris.append((i + 1, p.oid, p.pelanggan, p.resto, p.menu, fmt_int(p.harga),
                          p.prioritas, fmt_jam(p.masuk), fmt_jam(p.selesai), p.status))
        self.tampil_tabel(("no", "oid", "pelanggan", "resto", "menu", "harga", "prioritas",
                           "masuk", "selesai", "status"),
                          (35, 80, 150, 100, 90, 60, 65, 70, 70, 60), baris)
        self.catat("load", "M1 - larik", ms_load)

    # -----------------------------------------------------------------
    # M1: Array vs Linked List
    # -----------------------------------------------------------------
    def struktur_m1(self, struktur):
        if struktur == "ARRAY":
            return self.arr
        return self.ll

    def nama_tampil(self, struktur):
        if struktur == "ARRAY":
            return "array"
        return "linked list"

    def nama_modul_m1(self, struktur):
        if struktur == "ARRAY":
            return "M1 - array"
        return "M1 - linked list"

    def teks_panjang_m1(self):
        return f"Panjang sekarang: array {fmt_int(self.arr.size)}, linked list {fmt_int(self.ll.size)}."

    def halaman_lihat(self, struktur):
        if struktur == "ARRAY":
            judul = "Array: lihat pesanan ke-i"
            desk = "get(i): posisi elemen dihitung langsung dari indeks, jadi O(1)."
            hint = "Array menyimpan elemen berdampingan di memori, sehingga elemen ke-i langsung bisa dijangkau tanpa menelusuri apa pun."
        else:
            judul = "LinkedList: lihat pesanan ke-i"
            desk = "get(i): menelusuri simpul satu per satu dari head, jadi O(n)."
            hint = ("Linked list tidak punya alamat yang bisa dihitung. Untuk sampai ke pesanan ke-i, "
                    "i simpul harus dilewati dari head. Bandingkan waktunya dengan menu ARRAY - LIHAT PESANAN pada nomor besar.")
        self.siapkan_halaman(
            judul, desk,
            [("entry", "Pesanan ke-i (mulai dari 1)", "1", 14, "urutan dalam barisan")],
            "LIHAT", lambda: self.aksi_lihat(struktur), hint)

    def aksi_lihat(self, struktur):
        if not self.cek_data():
            return
        s = self.struktur_m1(struktur)
        i = self.baca_int(0, "Nomor pesanan")
        if i is None:
            return
        if i > s.size:
            self.tampil_hasil(f"Nomor pesanan di luar jangkauan. Panjang {self.nama_tampil(struktur)} saat ini {fmt_int(s.size)}.", galat=True)
            return
        t0 = time.perf_counter()
        p = s.get(i - 1)
        ms = (time.perf_counter() - t0) * 1000
        if struktur == "ARRAY":
            proses = "Array langsung menuju indeks " + fmt_int(i - 1) + " tanpa menelusuri."
        else:
            proses = "LinkedList menelusuri " + fmt_int(i - 1) + " simpul dari head."
        self.tampil_hasil(f"Pesanan ke-{fmt_int(i)} dari {fmt_int(s.size)}: {p.oid}.\n{proses}")
        self.tampil_detail(p)
        self.catat(struktur.lower() + "_get", self.nama_modul_m1(struktur), ms)

    def halaman_tambah(self, struktur, jenis):
        if jenis == "REGULER":
            if struktur == "ARRAY":
                judul = "Array: pesanan REGULER, masuk paling belakang"
                desk = "append: pesanan biasa mengantre di barisan paling belakang."
                hint = "Array menempel di ujung belakang, O(1) amortized: hanya sesekali menyalin ke petak 2x lebih besar saat kapasitas penuh."
            else:
                judul = "LinkedList: pesanan REGULER, masuk paling belakang"
                desk = "append lewat penunjuk tail: pesanan biasa mengantre di barisan paling belakang."
                hint = "Penunjuk tail disimpan supaya menambah di belakang tetap O(1), tanpa menelusuri simpul."
        elif jenis == "PRIORITAS":
            if struktur == "ARRAY":
                judul = "Array: pesanan PRIORITAS, menyerobot ke tengah"
                desk = "insert di indeks n/2: semua elemen sesudahnya digeser satu langkah ke kanan."
                hint = "Array harus menggeser separuh isinya untuk membuka satu tempat di tengah, jadi O(n)."
            else:
                judul = "LinkedList: pesanan PRIORITAS, menyerobot ke tengah"
                desk = "insert di indeks n/2: menelusuri separuh simpul dari head, lalu menyambung sekali."
                hint = "Menyambung simpul itu murah, tetapi mencapai tengah barisan memerlukan penelusuran O(n)."
        else:
            if struktur == "ARRAY":
                judul = "Array: pesanan VIP, langsung ke urutan pertama"
                desk = "insert di indeks 0: seluruh isi array digeser satu langkah ke kanan."
                hint = "Kasus terburuk array: setiap elemen harus bergeser, O(n)."
            else:
                judul = "LinkedList: pesanan VIP, langsung ke urutan pertama"
                desk = "insert di indeks 0: cukup mengubah satu penunjuk (head)."
                hint = "Linked list tidak perlu menggeser atau menelusuri apa pun, jadi O(1). Bandingkan dengan ARRAY - TAMBAH PESANAN VIP."
        self.siapkan_halaman(
            judul, desk,
            [("entry", "Nama pelanggan", "", 30, "nama untuk pesanan yang akan dibuat")],
            "TAMBAH", lambda: self.aksi_tambah(struktur, jenis), hint)

    def aksi_tambah(self, struktur, jenis):
        if not self.cek_data():
            return
        nama = self.ambil(0).strip()
        if nama == "":
            nama = "Pelanggan Baru"
        if jenis == "REGULER":
            prioritas = 3
        elif jenis == "PRIORITAS":
            prioritas = 2
        else:
            prioritas = 1
        p = self.buat_pesanan(nama, prioritas)
        s = self.struktur_m1(struktur)
        n = s.size
        if jenis == "REGULER":
            idx = n
        elif jenis == "PRIORITAS":
            idx = n // 2
        else:
            idx = 0

        t0 = time.perf_counter()
        if jenis == "REGULER":
            s.append(p)
        else:
            s.insert(idx, p)
        ms = (time.perf_counter() - t0) * 1000

        if struktur == "ARRAY":
            self.indeks_oid = None        # isi array berubah: daftar terurut oid harus dibangun ulang
            if n - idx == 0:
                proses = "Tidak ada elemen yang digeser."
            else:
                proses = f"Array menggeser {fmt_int(n - idx)} elemen ke kanan."
        else:
            if jenis == "PRIORITAS":
                proses = f"LinkedList menelusuri {fmt_int(max(idx - 1, 0))} simpul lalu menyambung sekali."
            elif jenis == "VIP":
                proses = "LinkedList hanya mengubah satu penunjuk (head), tanpa penelusuran."
            else:
                proses = "LinkedList menyambung lewat tail, tanpa penelusuran."
        self.tampil_hasil(f"{p.oid} ({p.pelanggan}) masuk di urutan ke-{fmt_int(idx + 1)}.\n"
                          f"{proses}\n{self.teks_panjang_m1()}")
        self.tampil_detail(p)
        self.catat(struktur.lower() + "_tambah_" + jenis.lower(), self.nama_modul_m1(struktur), ms)

    def halaman_hapus(self, struktur):
        if struktur == "ARRAY":
            judul = "Array: hapus pesanan ke-i"
            desk = "delete(i): semua elemen di kanan i digeser satu langkah ke kiri, O(n)."
            hint = "Menghapus di depan memaksa seluruh sisa elemen bergeser; menghapus di belakang hampir tanpa biaya."
        else:
            judul = "LinkedList: hapus pesanan ke-i"
            desk = "delete(i): menelusuri sampai simpul sebelum i, lalu melompati simpul i. O(n) telusur."
            hint = "Menghapus pesanan pertama hanya menggeser head (O(1)); makin ke belakang, makin panjang penelusurannya."
        self.siapkan_halaman(
            judul, desk,
            [("entry", "Hapus pesanan ke-i (mulai dari 1)", "1", 14, "urutan dalam barisan")],
            "HAPUS", lambda: self.aksi_hapus(struktur), hint)

    def aksi_hapus(self, struktur):
        if not self.cek_data():
            return
        s = self.struktur_m1(struktur)
        i = self.baca_int(0, "Nomor pesanan")
        if i is None:
            return
        if i > s.size:
            self.tampil_hasil(f"Nomor pesanan di luar jangkauan. Panjang {self.nama_tampil(struktur)} saat ini {fmt_int(s.size)}.", galat=True)
            return
        idx = i - 1
        n = s.size
        p = s.get(idx)            # disimpan dulu untuk ditampilkan; tidak ikut diukur
        t0 = time.perf_counter()
        s.delete(idx)
        ms = (time.perf_counter() - t0) * 1000
        if struktur == "ARRAY":
            self.indeks_oid = None
            if n - idx - 1 == 0:
                proses = "Tidak ada elemen yang digeser."
            else:
                proses = f"Array menggeser {fmt_int(n - idx - 1)} elemen ke kiri."
        else:
            if idx == 0:
                proses = "LinkedList hanya menggeser head, tanpa penelusuran."
            else:
                proses = f"LinkedList menelusuri {fmt_int(idx - 1)} simpul untuk mencapai simpul sebelumnya."
        self.tampil_hasil(f"Pesanan ke-{fmt_int(i)} ({p.oid}) dihapus.\n{proses}\n{self.teks_panjang_m1()}")
        self.tampil_detail(p)
        self.catat(struktur.lower() + "_hapus", self.nama_modul_m1(struktur), ms)

    # -----------------------------------------------------------------
    # M2: Stack (kasir, undo, redo) dan Queue
    # -----------------------------------------------------------------
    def halaman_kasir(self):
        self.siapkan_halaman(
            "Stack: hitung struk lewat postfix",
            "Struk ditulis infix, lalu dihitung dua tahap dengan stack: tahap 1 infix menjadi postfix, tahap 2 postfix dievaluasi.",
            [("entry", "Struk belanja (infix)", "( 3 * 12000 ) + ( 2 * 8500 ) - 5000", 44,
              "angka, + - * / dan tanda kurung; 3 x Rp12.000 dan 2 x Rp8.500, potongan Rp5.000")],
            "HITUNG", self.aksi_kasir,
            "Baris 1.x adalah tahap konversi, baris 2.x tahap evaluasi. Tahap 1 menahan operator di stack sampai gilirannya tiba. "
            "Tahap 2 menumpuk angka, dan setiap operator mengambil dua nilai teratas. Operand kanan selalu keluar lebih dulu.")

    def aksi_kasir(self):
        ekspresi = self.ambil(0).strip()
        galat = validasi_infix(ekspresi)
        if galat is not None:
            self.tampil_hasil("Struk tidak valid: " + galat, galat=True)
            self.tampil_tabel(("langkah", "token", "tindakan", "stack", "output"), (75, 60, 330, 140, 270), [])
            return
        try:
            t0 = time.perf_counter()
            hasil_postfix = postfix(ekspresi)       # backend M2: infix -> postfix
            total = hitung(hasil_postfix)           # backend M2: evaluasi postfix
            ms = (time.perf_counter() - t0) * 1000
            langkah = jejak_kasir(ekspresi)         # jejak tiap langkah untuk ditampilkan
        except ZeroDivisionError:
            self.tampil_hasil("Struk tidak valid: ada pembagian dengan nol.", galat=True)
            return
        self.tampil_hasil(f"Struk : {ekspresi}\n"
                          f"Postfix: {isi_larik_teks(hasil_postfix)}\n"
                          f"TOTAL : {fmt_rupiah(total)}")
        self.tampil_tabel(("langkah", "token", "tindakan", "stack", "output"),
                          (75, 60, 330, 140, 270), langkah)
        self.catat("stack_postfix", "M2 - stack", ms)

    def halaman_undo(self):
        self.siapkan_halaman(
            "Stack: batalkan aksi antrean terakhir",
            "Mengambil catatan teratas tumpukan undo, lalu menjalankan kebalikannya. Aksi terakhirlah yang dibatalkan lebih dulu.",
            [], "UNDO", self.aksi_undo,
            "Kebalikan dari enqueue adalah membuang elemen paling belakang. Kebalikan dari dequeue adalah mengembalikan seluruh "
            "pesanan yang keluar ke DEPAN antrean, sehingga catatannya menyimpan daftar pesanan, bukan hanya jumlahnya.")
        self.tampil_hasil(f"Tumpukan {self.teks_tumpukan()}. Klik UNDO untuk membatalkan aksi terakhir.")

    def aksi_undo(self):
        top = m2.stack_undo.peek()
        if top is None:
            self.tampil_hasil("Tumpukan undo kosong, tidak ada yang bisa dibatalkan.", galat=True)
            self.tampil_tabel(("no", "oid", "pelanggan", "resto", "menu"), (40, 110, 180, 140, 140), [])
            return
        aksi = top[0]
        data = top[1]
        t0 = time.perf_counter()
        m2.undo()
        ms = (time.perf_counter() - t0) * 1000
        if aksi == "ENQUEUE":
            teks = f"Pembatalan enqueue: {data.oid} dikeluarkan lagi dari belakang."
            daftar = [data]
        else:
            teks = f"Pembatalan dequeue: {fmt_int(data.size)} pesanan dikembalikan ke DEPAN antrean circular."
            daftar = self.larik_ke_list(data)
        self.tampil_hasil(f"{teks}\nPanjang antrean sekarang: {self.teks_panjang_antrean()}. "
                          f"Tumpukan {self.teks_tumpukan()}.")
        self.tabel_antrean(daftar)
        self.catat("stack_undo", "M2 - stack", ms)

    def halaman_redo(self):
        self.siapkan_halaman(
            "Stack: kerjakan lagi aksi yang dibatalkan",
            "Mengambil catatan teratas tumpukan redo, lalu mengerjakan ulang aksi aslinya. Aksi baru apa pun mengosongkan tumpukan ini.",
            [], "REDO", self.aksi_redo,
            "Redo mengerjakan ULANG aksi aslinya, bukan kebalikannya, lalu mengembalikan catatannya ke tumpukan undo supaya bisa dibatalkan lagi.")
        self.tampil_hasil(f"Tumpukan {self.teks_tumpukan()}. Klik REDO untuk mengulang aksi yang baru dibatalkan.")

    def aksi_redo(self):
        top = m2.stack_redo.peek()
        if top is None:
            self.tampil_hasil("Tumpukan redo kosong, tidak ada yang diulang.", galat=True)
            self.tampil_tabel(("no", "oid", "pelanggan", "resto", "menu"), (40, 110, 180, 140, 140), [])
            return
        aksi = top[0]
        data = top[1]
        t0 = time.perf_counter()
        m2.redo()
        ms = (time.perf_counter() - t0) * 1000
        if aksi == "ENQUEUE":
            teks = f"Enqueue dikerjakan lagi: {data.oid} masuk kembali ke belakang."
            daftar = [data]
        else:
            teks = f"Dequeue dikerjakan lagi: {fmt_int(data.size)} pesanan keluar lagi dari antrean circular."
            daftar = self.larik_ke_list(data)
        self.tampil_hasil(f"{teks}\nPanjang antrean sekarang: {self.teks_panjang_antrean()}. "
                          f"Tumpukan {self.teks_tumpukan()}.")
        self.tabel_antrean(daftar)
        self.catat("stack_redo", "M2 - stack", ms)

    def larik_ke_list(self, larik):
        hasil = []
        for i in range(larik.size):
            hasil.append(larik.get(i))
        return hasil

    def tabel_antrean(self, daftar, dengan_masuk=False):
        """Menampilkan sebagian pesanan (maks 100 baris) sebagai tabel #, oid, pelanggan, resto, menu."""
        baris = []
        for i in range(min(len(daftar), 100)):
            p = daftar[i]
            if dengan_masuk:
                baris.append((i + 1, p.oid, p.pelanggan, p.resto, p.menu, fmt_jam(p.masuk)))
            else:
                baris.append((i + 1, p.oid, p.pelanggan, p.resto, p.menu))
        if dengan_masuk:
            self.tampil_tabel(("no", "oid", "pelanggan", "resto", "menu", "masuk"),
                              (40, 100, 170, 130, 120, 80), baris)
        else:
            self.tampil_tabel(("no", "oid", "pelanggan", "resto", "menu"),
                              (40, 110, 180, 140, 140), baris)

    def halaman_enqueue(self):
        self.siapkan_halaman(
            "Queue: pesanan baru masuk ke belakang",
            "Menambah pesanan di ujung belakang KEDUA antrean sekaligus, yang naif maupun yang circular.",
            [("entry", "Nama pelanggan", "", 30, "untuk pesanan yang akan dibuat")],
            "ENQUEUE", self.aksi_enqueue,
            "enqueue selalu menempel di belakang, jadi O(1) pada kedua versi. Perbedaannya baru muncul saat dequeue.")

    def aksi_enqueue(self):
        if not self.cek_data():
            return
        if m2.circular_queue.count >= m2.circular_queue.capacity:
            self.tampil_hasil("Antrean circular penuh (kapasitas "
                              + fmt_int(m2.circular_queue.capacity) + "). Layani beberapa pesanan dulu.", galat=True)
            return
        nama = self.ambil(0).strip()
        if nama == "":
            nama = "Pelanggan Baru"
        p = self.buat_pesanan(nama, 3)
        t0 = time.perf_counter()
        m2.naive_queue.enqueue(p)
        m2.circular_queue.enqueue(p)
        self.arr.append(p)
        self.ll.append(p)
        self.indeks_oid = None
        ms = (time.perf_counter() - t0) * 1000
        m2.newAction("ENQUEUE", p)       # catat ke tumpukan undo + kosongkan redo
        self.tampil_hasil(f"{p.oid} masuk ke barisan paling belakang pada KEDUA antrean.\n"
                          f"Panjang sekarang: {self.teks_panjang_antrean()}.")
        self.tampil_detail(p)
        self.catat("queue_enqueue", "M2 - queue", ms)

    def halaman_dequeue_naif(self):
        self.siapkan_halaman(
            "Queue naif: ambil dari depan dengan menggeser isi",
            "Mengambil indeks 0 lalu menggeser seluruh sisa isi satu petak ke kiri. Biayanya O(n) setiap dequeue.",
            [("entry", "Berapa kali dequeue", "2", 14,
              "sampai panjang antrean; coba 1 lalu 100 untuk melihat bedanya")],
            "DEQUEUE", self.aksi_dequeue_naif,
            "Mengambil indeks 0 memaksa seluruh sisa isi bergeser satu petak, jadi biaya per dequeue sebanding dengan panjang antrean. "
            "Bandingkan waktunya dengan menu DEQUEUE CIRCULAR. Dequeue naif hanya sebagai pembanding, tidak dicatat di tumpukan undo.")

    def aksi_dequeue_naif(self):
        if not self.cek_data():
            return
        n = self.baca_int(0, "Jumlah dequeue")
        if n is None:
            return
        q = m2.naive_queue
        if q.data.size == 0:
            self.tampil_hasil("Antrean naif kosong, tidak ada yang bisa dilayani.", galat=True)
            return
        catatan = ""
        if n > q.data.size:
            n = q.data.size
            catatan = f" (diminta melebihi isi antrean, dibatasi {fmt_int(n)})"
        self.sibuk("Memproses dequeue...")
        g0 = q.total_geseran
        keluar = []
        t0 = time.perf_counter()
        for i in range(n):
            keluar.append(q.dequeue())
        ms = (time.perf_counter() - t0) * 1000
        self.selesai_sibuk()
        geser = q.total_geseran - g0
        rata = geser // n
        self.tampil_hasil(f"{fmt_int(n)} pesanan keluar dari depan antrean naif{catatan}.\n"
                          f"Total {fmt_int(geser)} elemen digeser, rata-rata {fmt_int(rata)} geseran per dequeue.\n"
                          f"Sisa antrean naif {fmt_int(q.data.size)}.")
        self.tabel_antrean(keluar, dengan_masuk=True)
        self.catat("queue_dequeue_naive", "M2 - queue naif", ms)

    def halaman_dequeue_circular(self):
        self.siapkan_halaman(
            "Queue circular: ambil dari depan dengan memajukan penunjuk",
            "Hanya penunjuk front yang maju, memakai sisa bagi terhadap kapasitas. Isi larik tidak digeser sama sekali.",
            [("entry", "Berapa kali dequeue", "2", 14,
              "sampai panjang antrean; coba 1 lalu 100 untuk melihat bedanya")],
            "DEQUEUE", self.aksi_dequeue_circular,
            "Yang berpindah hanya penunjuk front, sisa isi tidak disentuh sama sekali, jadi biayanya O(1) berapa pun panjang antreannya. "
            "Seluruh pesanan yang keluar dicatat sebagai SATU aksi di tumpukan undo.")

    def aksi_dequeue_circular(self):
        if not self.cek_data():
            return
        n = self.baca_int(0, "Jumlah dequeue")
        if n is None:
            return
        q = m2.circular_queue
        if q.count == 0:
            self.tampil_hasil("Antrean circular kosong, tidak ada yang bisa dilayani.", galat=True)
            return
        catatan = ""
        if n > q.count:
            n = q.count
            catatan = f" (diminta melebihi isi antrean, dibatasi {fmt_int(n)})"
        keluar = []
        t0 = time.perf_counter()
        for i in range(n):
            keluar.append(q.dequeue())
        ms = (time.perf_counter() - t0) * 1000

        batch = Array()                 # catatan undo menyimpan DAFTAR pesanan, bukan hanya jumlahnya
        for p in keluar:
            batch.append(p)
        m2.newAction("DEQUEUE", batch)

        self.tampil_hasil(f"{fmt_int(n)} pesanan keluar dari depan antrean circular{catatan}.\n"
                          f"Tidak ada elemen yang digeser. front sekarang {fmt_int(q.front)}, "
                          f"rear {fmt_int(q.rear)}, kapasitas {fmt_int(q.capacity)}.\n"
                          f"Sisa antrean circular {fmt_int(q.count)}.")
        self.tabel_antrean(keluar, dengan_masuk=True)
        self.catat("queue_dequeue_circular", "M2 - queue circular", ms)

    # -----------------------------------------------------------------
    # M3: Sort dan Search
    # -----------------------------------------------------------------
    def halaman_sort(self, jenis):
        if jenis == "INSERTION":
            judul = "Sort: insertion sort, O(n²)"
            desk = "Setiap elemen digeser mundur sampai menemukan tempatnya. Sederhana, tetapi kerjanya tumbuh kuadratik."
            default_n = "2000"
            default_kunci = "harga"
            hint = ("Setiap elemen digeser mundur sampai menemukan tempatnya, jadi biayanya tumbuh kuadratik: melipatduakan jumlah baris "
                    "membuat perbandingan kira-kira empat kali lipat. Jalankan SORT - MERGE SORT pada jumlah dan kunci yang sama, "
                    f"lalu bandingkan angka perbandingannya. Batas {fmt_int(BATAS_INSERTION)} baris agar aplikasi tidak membeku.")
            tombol = "URUTKAN"
        else:
            judul = "Sort: merge sort, O(n log n)"
            desk = "Larik dibelah dua terus-menerus, lalu potongan yang sudah terurut disatukan kembali."
            default_n = "4000"
            default_kunci = "oid"
            hint = ("Larik dibelah dua terus-menerus lalu potongan yang sudah terurut disatukan kembali. Kedalaman belahannya log n dan "
                    "tiap lapis menyentuh n elemen, jadi O(n log n). Hasilnya sama persis dengan insertion sort karena keduanya stabil.")
            tombol = "URUTKAN"
        self.siapkan_halaman(
            judul, desk,
            [("entry", "Jumlah baris diurutkan", default_n, 14,
              "diambil dari awal data; coba 1.000 lalu 2.000 lalu 4.000"),
             ("combo", "Diurutkan menurut", default_kunci, ["oid", "harga", "selesai"],
              "oid (teks), harga (angka), selesai (waktu selesai)")],
            tombol, lambda: self.aksi_sort(jenis), hint)

    def aksi_sort(self, jenis):
        if not self.cek_data():
            return
        n = self.baca_int(0, "Jumlah baris")
        if n is None:
            return
        kunci = self.ambil(1)
        if n > self.arr.size:
            n = self.arr.size
        if jenis == "INSERTION" and n > BATAS_INSERTION:
            self.tampil_hasil(f"DITOLAK: batasnya {fmt_int(BATAS_INSERTION)} baris, pakai merge sort untuk data penuh.", galat=True)
            self.tampil_tabel(("kolom", "isi"), (160, 420), [])
            return

        self.sibuk(f"Mengurutkan {fmt_int(n)} pesanan menurut {kunci}, mohon tunggu...")
        # Salinan n baris pertama (urutan data asli tidak boleh berubah karena insertion sort bekerja di tempat)
        salinan = Array()
        for i in range(n):
            p = self.arr.get(i)
            salinan.append(KunciUrut(p, ambil_kunci(p, kunci)))

        KunciUrut.geseran = 0
        t0 = time.perf_counter()
        if jenis == "INSERTION":
            hasil, banding = insertion_sort(salinan)
        else:
            hasil, banding = merge_sort(salinan)
        ms = (time.perf_counter() - t0) * 1000
        self.selesai_sibuk()

        if jenis == "INSERTION":
            pindah = KunciUrut.geseran + max(n - 1, 0)     # geseran + satu penempatan per elemen
            perintah = "insertion_sort"
            modul = "M3 - insertion sort"
        else:
            pindah = hitung_pemindahan_merge(n)
            perintah = "merge_sort"
            modul = "M3 - merge sort"
        self.tampil_hasil(f"{fmt_int(n)} pesanan diurutkan menurut {kunci}.\n"
                          f"{fmt_int(banding)} perbandingan, {fmt_int(pindah)} pemindahan.")

        baris = []
        for i in range(min(BARIS_TAMPIL, hasil.size)):
            p = hasil.get(i).pesanan
            baris.append((i + 1, p.oid, fmt_int(p.harga), fmt_jam(p.selesai), p.resto, p.menu))
        self.tampil_tabel(("no", "oid", "harga", "selesai", "resto", "menu"),
                          (40, 100, 80, 90, 140, 130), baris)
        self.catat(perintah, modul, ms)

    def halaman_linear(self):
        n = fmt_int(self.arr.size) if self.termuat else "seluruh"
        self.siapkan_halaman(
            "Search: linear search, O(n)",
            "Memeriksa pesanan satu per satu dari depan. Tidak menuntut data terurut.",
            [("entry", "Nomor pesanan (oid)", "O-137442", 24, "format: O-000001 sampai O-200000")],
            "CARI", self.aksi_linear,
            f"Data tidak perlu terurut, tetapi setiap pesanan diperiksa satu per satu dari depan. "
            f"Kasus terburuk menyentuh seluruh {n} baris.")

    def aksi_linear(self):
        if not self.cek_data():
            return
        target = self.ambil(0).strip().upper()
        if target == "":
            self.tampil_hasil("Isi nomor pesanan (oid) yang dicari.", galat=True)
            return
        self.sibuk("Mencari...")
        t0 = time.perf_counter()
        idx, banding = linear_search(self.arr, target)
        ms = (time.perf_counter() - t0) * 1000
        self.selesai_sibuk()
        if idx == -1:
            self.tampil_hasil(f"{target} tidak ditemukan.\n{fmt_int(banding)} perbandingan (seluruh data diperiksa).", galat=True)
            self.tampil_tabel(("kolom", "isi"), (160, 420), [])
        else:
            self.tampil_hasil(f"Ditemukan pada indeks {fmt_int(idx)}.\n{fmt_int(banding)} perbandingan.")
            self.tampil_detail(self.arr.get(idx))
        self.catat("linear_search", "M3 - linear search", ms)

    def halaman_binary(self):
        if self.termuat:
            n = self.arr.size
            langkah = n.bit_length()
            teks_n = f"{fmt_int(n)} baris habis dalam paling banyak {langkah} langkah"
        else:
            teks_n = "seluruh baris habis dalam sedikit langkah"
        self.siapkan_halaman(
            "Search: binary search, O(log n)",
            "Membuang separuh sisa daftar pada setiap perbandingan. Menuntut daftar yang sudah terurut menurut oid.",
            [("entry", "Nomor pesanan (oid)", "O-137442", 24, "format: O-000001 sampai O-200000")],
            "CARI", self.aksi_binary,
            f"Setiap perbandingan membuang separuh sisa daftar, jadi {teks_n}. "
            "Syaratnya daftar harus SUDAH terurut menurut kunci yang dicari; di sini terurut menurut oid.")

    def aksi_binary(self):
        if not self.cek_data():
            return
        target = self.ambil(0).strip().upper()
        if target == "":
            self.tampil_hasil("Isi nomor pesanan (oid) yang dicari.", galat=True)
            return

        teks_bangun = ""
        if self.indeks_oid is None:
            # Binary search menuntut daftar terurut menurut oid. Daftar ini dibangun SEKALI (salinan terpisah,
            # data asli di Array tidak diubah) dan ongkos pengurutannya dicatat terang-terangan.
            self.sibuk("Membangun daftar terurut oid dengan merge sort (sekali saja), mohon tunggu...")
            salinan = Array()
            for i in range(self.arr.size):
                salinan.append(self.arr.get(i))
            t0 = time.perf_counter()
            terurut, banding_sort = merge_sort(salinan)
            ms_bangun = (time.perf_counter() - t0) * 1000
            self.selesai_sibuk()
            self.indeks_oid = terurut
            self.catat("merge_sort", "M3 - merge sort", ms_bangun)
            teks_bangun = f"Daftar terurut oid dibangun sekali dengan merge sort, {fmt_waktu(ms_bangun)}.\n"
        else:
            teks_bangun = "Memakai daftar terurut oid yang sudah dibangun sebelumnya (tanpa ongkos pengurutan).\n"

        t0 = time.perf_counter()
        idx, banding = binary_search(self.indeks_oid, target)
        ms = (time.perf_counter() - t0) * 1000
        total = self.indeks_oid.size
        if idx == -1:
            self.tampil_hasil(f"{teks_bangun}{target} tidak ditemukan.\n{fmt_int(banding)} perbandingan.", galat=True)
            self.tampil_tabel(("kolom", "isi"), (160, 420), [])
        else:
            self.tampil_hasil(f"{teks_bangun}Ditemukan pada baris ke-{fmt_int(idx + 1)} dari {fmt_int(total)} baris.\n"
                              f"{fmt_int(banding)} perbandingan, bandingkan dengan linear search.")
            self.tampil_detail(self.indeks_oid.get(idx))
        self.catat("binary_search", "M3 - binary search", ms)


if __name__ == "__main__":
    root = tk.Tk()
    app = Aplikasi2EZ4U(root)
    root.mainloop()
