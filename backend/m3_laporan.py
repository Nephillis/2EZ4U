from backend.m1_pesanan import Array

def insertion_sort(arr):
    perbandingan = 0
    for i in range(1, arr.size):
        key = arr.get(i)
        j = i - 1
        while j >= 0:
            perbandingan += 1

            if arr.get(j) > key:
                arr.data[j + 1] = arr.get(j)
                j -= 1
            else:
                break
        arr.data[j + 1] = key

    return arr, perbandingan

def merge_sort(arr):
    if arr.size <= 1:
        return arr, 0
    
    mid = arr.size // 2
    left_half = Array()
    right_half = Array()

    for i in range(0, mid):
        left_half.append(arr.get(i))

    for i in range (mid, arr.size):
        right_half.append(arr.get(i))   

    left_sorted, count_left = merge_sort(left_half)
    right_sorted, count_right = merge_sort(right_half)

    hasil_gabung, count_merge = merge(left_sorted, right_sorted)
    total_perbandingan = count_left + count_right + count_merge

    return hasil_gabung, total_perbandingan

def merge(left, right):
    hasil = Array()
    perbandingan = 0
    i = 0 
    j = 0

    while i < left.size and j < right.size:
        perbandingan += 1
        if left.get(i) <= right.get(j):
            hasil.append(left.get(i))
            i += 1
        else:
            hasil.append(right.get(j))
            j += 1

    while i < left.size:
        hasil.append(left.get(i))
        i += 1
    while j < right.size:
        hasil.append(right.get(j))
        j += 1

    return hasil, perbandingan

def linear_search(arr, target):
    perbandingan = 0

    for i in range(arr.size):
        perbandingan += 1

        if arr.get(i) == target:
            return i, perbandingan

    return -1, perbandingan

def binary_search(arr, target):
    perbandingan = 0

    left = 0
    right = arr.size - 1

    while left <= right:
        perbandingan += 1
        mid = (left + right) // 2
        midpoint = arr.get(mid)

        if midpoint == target:
            return mid,  perbandingan
        elif midpoint < target:
            left = mid + 1
        else:
            right = mid - 1

    return -1, perbandingan

