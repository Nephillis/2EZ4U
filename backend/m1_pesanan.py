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
