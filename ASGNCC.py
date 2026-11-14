
import time
import matplotlib.pyplot as plt

# Function to calculate sum of cubes
def sum_of_cubes(N):
    total = 0

    for i in range(1, N + 1):
        total += i**3

    return total

# Different values of N
N_values = [100, 500, 1000, 2000, 5000,
            10000, 20000, 50000]

running_times = []

# Calculate sum and measure execution time
for N in N_values:

    start = time.perf_counter()

    result = sum_of_cubes(N)

    end = time.perf_counter()

    elapsed_time = end - start
    running_times.append(elapsed_time)

    print("N =", N)
    print("Sum =", result)
    print("Running time =", elapsed_time, "seconds")
    print("------------------------")

# Plot graph
plt.plot(N_values, running_times, marker='o')

plt.xlabel("N")
plt.ylabel("Running Time (seconds)")
plt.title("Running Time vs N for Sum of Cubes")

plt.grid(True)
plt.show()
