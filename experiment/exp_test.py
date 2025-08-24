# exp_test.py

# This runs 10x faster on my laptop, but ratio of timing difference is the same

import math
import time


def test_exp(m, n):
    start = time.clock_gettime(time.CLOCK_MONOTONIC)
    ans = [math.exp(m*i) for i in range(n)]
    end = time.clock_gettime(time.CLOCK_MONOTONIC)
    print("test_exp", (end - start) / n)
    return ans

def test_pow(m, n):
    start = time.clock_gettime(time.CLOCK_MONOTONIC)
    ans = [math.pow(m, i) for i in range(n)]
    end = time.clock_gettime(time.CLOCK_MONOTONIC)
    print("test_pow", (end - start) / n)
    return ans

def run(m, n):
    pow_ans = test_pow(1 + m, n)
    log1p_m = math.log1p(m)
    exp_ans = test_exp(log1p_m, n)
    for i, (x, y) in enumerate(zip(pow_ans, exp_ans)):
        if not math.isclose(x, y, rel_tol=1e-13):  # rel_tol=1e-15 fails
            print(i, x, y)




if __name__ == "__main__":
    run(1.0156, 1000)
