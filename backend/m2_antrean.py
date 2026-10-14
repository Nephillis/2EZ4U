from backend.m1_pesanan import Array

class Stack:
    def __init__(self):
        self.data = Array()
        

    def push(self, x):
        self.data.append(x)
        

    def pop(self):
        if self.is_empty():
            return None

        index_top = self.data.size - 1
        popData = self.data.get(index_top)
        self.data.delete(index_top)
        return popData

    def peek(self):
        if self.is_empty():
            return None
        
        return self.data.get(self.data.size - 1)

    def is_empty(self):
        return self.data.size == 0


def splitToken(expression):
        hasil = Array()
        temp_angka = ""

        for char in expression:
            if char.isdigit():
                temp_angka += char
            else:
                if temp_angka != "":
                    hasil.append(temp_angka)
                    temp_angka = ""
                if char != " ":
                    hasil.append(char)
        if temp_angka != "":
            hasil.append(temp_angka)
        
        return hasil

def cek_prioritas(operator):
    if operator == "*" or operator == "/":
        return 2
    elif operator == "+" or operator == "-":
        return 1
    return 0

def postfix(expression):
    token_list = splitToken(expression)
    stack_op = Stack()
    hasil_postfix = Array()

    for i in range(token_list.size):
        token = token_list.get(i)
        if token.isdigit():
            hasil_postfix.append(token)
        elif token == "(":
            stack_op.push(token)
        elif token == ")":
            while not stack_op.peek() == "(":
                    hasil_postfix.append(stack_op.pop())
            stack_op.pop()
        else:
            while not stack_op.is_empty() and cek_prioritas(stack_op.peek()) >= cek_prioritas(token):
                hasil_postfix.append(stack_op.pop())
            stack_op.push(token) 

    while not stack_op.is_empty():
        hasil_postfix.append(stack_op.pop())

    return hasil_postfix

def hitung(postfix_list):
    stack_hitung = Stack()

    for i in range(postfix_list.size):
        token = postfix_list.get(i)
        if token.isdigit():
            stack_hitung.push(int(token))
        else:
            b = stack_hitung.pop()
            a = stack_hitung.pop()

            if token == "+":
                hasil_sementara = a + b
            elif token ==  "-":
                hasil_sementara = a - b
            elif token == "*":
                hasil_sementara = a * b
            elif token == "/":
                hasil_sementara = a / b

            stack_hitung.push(hasil_sementara)

    return stack_hitung.pop()

def newAction(action, data):
    stack_undo.push((action, data)) 
    while not stack_redo.is_empty():
        stack_redo.pop()

def undo():
    if stack_undo.is_empty():
        return None
    catatan = stack_undo.pop()
    action = catatan[0]
    data = catatan[1]

    if action == "ENQUEUE":
        naive_queue.cancel_enqueue()
        circular_queue.cancel_enqueue()
    if action == "DEQUEUE":
        # data = Array berisi pesanan yang keluar (urutan keluar).
        # Kembalikan ke DEPAN antrean circular, mulai dari yang paling akhir keluar,
        # supaya urutan aslinya pulih. (Dequeue naif hanya pembanding, tidak dicatat.)
        for i in range(data.size - 1, -1, -1):
            circular_queue.cancel_dequeue(data.get(i))

    stack_redo.push((action, data))
    return catatan

def redo():
    if stack_redo.is_empty():
        return None
    catatan = stack_redo.pop()
    action = catatan[0]
    data = catatan[1]

    if action == "ENQUEUE":
        naive_queue.enqueue(data)
        circular_queue.enqueue(data)
    if action == "DEQUEUE":
        # kerjakan ulang aksi aslinya: keluarkan lagi sebanyak isi catatan
        for i in range(data.size):
            circular_queue.dequeue()

    stack_undo.push((action, data))
    return catatan

class NaiveQueue:
    def __init__(self):
        self.data = Array()
        self.total_geseran = 0

    def enqueue(self, value):
        self.data.append(value)

    def dequeue(self):
        if self.data.size == 0:
            return None
        elemen_keluar = self.data.get(0)

        for i in range(0, self.data.size - 1):
            self.data.data[i] = self.data.data[i + 1]
            self.total_geseran += 1

        self.data.size -= 1

        return elemen_keluar

    def cancel_enqueue(self):
        if self.data.size == 0:
            return None

        lastIndex = self.data.size - 1
        self.data.delete(lastIndex)

    def cancel_dequeue(self,nilai):
        self.data.insert(0,nilai)

class CircularQueue:
    def __init__(self, capacity=32768):
        self.capacity = capacity
        self.data = [None] * self.capacity
        self.front = 0
        self.rear = 0
        self.count = 0

    def enqueue(self, value):
        if self.count == self.capacity:
            return None

        self.data[self.rear] = value
        self.rear = (self.rear + 1) % self.capacity
        self.count += 1

    def dequeue(self):
        if self.count == 0:
            return None

        elemen_keluar = self.data[self.front]
        self.front = (self.front + 1) % self.capacity
        self.count -= 1
        return elemen_keluar

    def cancel_enqueue(self):
        if self.count == 0:
            return None

        self.rear = (self.rear - 1) % self.capacity
        self.data[self.rear] = None
        self.count -= 1

    def cancel_dequeue(self, nilai):
        if self.count == self.capacity:
            return None

        self.front = (self.front - 1) % self.capacity
        self.data[self.front] = nilai 
        self.count += 1

stack_undo = Stack()
stack_redo = Stack()
naive_queue = NaiveQueue()
circular_queue = CircularQueue()

#Tes
