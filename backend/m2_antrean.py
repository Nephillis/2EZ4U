from backend.m1_pesanan import Array, LinkedList

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