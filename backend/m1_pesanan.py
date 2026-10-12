# M1 Linked List & Array

class Array:
    # Menginisialisasi ukuran awal array dan kapasitasnya
    def __init__(self, initCapacity=4):
        self.capacity = initCapacity
        self.size = 0
        self.data = [None] * self.capacity

    # Menambahkan elemen array baru ke akhir array (Penambahan customer reguler)
    def append(self, value):
        if self.size == self.capacity:
            newCapacity = self.capacity * 2
            newData = [None] * newCapacity

            for i in range (self.size):
                newData[i] = self.data[i]

            self.data = newData
            self.capacity = newCapacity

        self.data[self.size] = value 
        self.size += 1
            
    # Menyisipkan elemen baru array ke index tertentu (Penambahan customer prioritas & VIP)
    def insert(self, index, value):
        if self.size == self.capacity:
            newCapacity = self.capacity * 2
            newData = [None] * newCapacity

            for i in range (self.size):
                newData[i] = self.data [i]
                
            self.data = newData
            self.capacity = newCapacity

        for i in range (self.size - 1, index - 1, -1):
            self.data[i + 1] = self.data[i]

           

        self.data[index] = value
        self.size += 1


    def get(self, index):
        if 0<= index < self.size:
            return self.data[index]
        return None

    def delete(self, index):
            if index < 0 or index >= self.size:
                return
            for i in range (index, self.size - 1):
                self.data[i] = self.data[i + 1]
    
            self.data[self.size - 1] = None
            self.size -= 1

class Node:
    def __init__(self, value):
        self.data = value
        self.next = None

class LinkedList:
    def __init__(self):
        self.head = None
        self.tail = None
        self.size = 0

    def append(self, value):
        newNode = Node(value)
        if self.head is None:
            self.head = newNode
            self.tail = newNode
        else:
            self.tail.next = newNode
            self.tail = newNode
        self.size += 1

    def insert(self, index, value):
        newNode = Node(value)
        if index == 0:
            newNode.next = self.head
            self.head = newNode
            if self.size == 0:
                self.tail = newNode
            self.size += 1
            return 

        current = self.head

        for i in range(index - 1):
            if current.next is not None:
                current = current.next

        newNode.next = current.next
        current.next = newNode

        if newNode.next is None:
            self.tail = newNode

        self.size += 1
            
    def get(self, index):
        if index < 0 or index >= self.size:
            return None
        current = self.head
        for i in range(index):
            current = current.next

        return current.data

    def delete(self, index):
        if index < 0 or index >= self.size:
            return 

        if index == 0:
            self.head = self.head.next
            self.size -= 1
            if self.size == 0:
                self.tail = None
            return

        current = self.head
        for i in range(index - 1):
            current = current.next
        current.next = current.next.next

        if current.next is None:
            self.tail = current

        self.size -=1

import csv

def muat_data_csv(nama_file, struktur_data):
    print(f"Membaca data dari {nama_file}...")
    try:
        # Membuka file CSV
        with open(nama_file, mode='r', encoding='utf-8') as file:
            csv_reader = csv.reader(file)
            
            # Lewati baris pertama karena itu adalah header (judul kolom)
            header = next(csv_reader)
            
            for baris in csv_reader:
                # Lewati jika ada baris kosong di akhir file
                if len(baris) < 9:
                    continue
                    
                # Ambil angka prioritas dari kolom ke-6 (indeks 5)
                angka_prioritas = int(baris[5])
                
                
                data_pesanan = (baris[0], baris[1], baris[2], baris[3], baris[4], angka_prioritas, baris[6], baris[7], baris[8])
                
                # Masukkan ke dalam struktur data sesuai prioritasnya
                if angka_prioritas == 1:
                    struktur_data.insert(0, data_pesanan) # VIP menyerobot ke paling depan
                elif angka_prioritas == 2:
                    struktur_data.insert(1, data_pesanan) # Prioritas diletakkan setelah VIP
                else:
                    struktur_data.append(data_pesanan)    # Reguler (3) antre di belakang
                    
        print(f"Berhasil! Total antrean saat ini: {struktur_data.size} pesanan.")
        
    except FileNotFoundError:
        print(f"ERROR: File {nama_file} tidak ditemukan. Cek kembali letak foldernya!")

ll_antrean = LinkedList()


lokasi_file = 'data/pesanan.csv' 

muat_data_csv(lokasi_file, ll_antrean)

if ll_antrean.size > 0:
    print("\n3 Antrean Terdepan Saat Ini:")
    current = ll_antrean.head
    for i in range(3):
        if current is not None:
            print(f"{i+1}. [{current.data[0]}] {current.data[1]} (Prioritas: {current.data[5]})")
            current = current.next