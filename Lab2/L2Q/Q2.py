import numpy as np

arr = np.array([10, 20, 30, 40, 50])

# Access the third element
third = arr[2]          # 30
print(third)

# Get the first three elements
first_three = arr[:3]   # [10 20 30]
print(first_three)


# Replace 30 with 35
arr[2] = 35
print(arr[2])