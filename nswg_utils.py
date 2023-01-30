import numpy as np
import string

def timeformat(secs):
    if type(secs) is not int: secs = int(secs)
    # Formats an integer secs into a HH:MM:SS format.
    return f"{str(secs // 3600).zfill(2)}:{str((secs // 60) % 60).zfill(2)}:{str(secs % 60).zfill(2)}"

def round_percentages(numbers, norm=100):
    # make sure numbers add up to 100
    numbers = np.array(numbers)
    numbers = numbers * norm / np.sum(numbers)

    fracs, floors = np.modf(numbers)

    K = norm - np.sum(floors, dtype=int)

    if K > 0:
        argsort_byfracs = np.argsort(-fracs)

        for k in range(K):
            j = argsort_byfracs[k]
            floors[j] = floors[j] + 1

    return floors

def yesno(bool, if_false, if_true):
    if bool:
        return if_true
    else:
        return if_false


def print_list_with_duplicates(L):
    counts = dict()
    for l in L:
        counts[l] = counts.get(l, 0) + 1

    def func(k):
        return yesno(counts[k] > 1, "", f" x{counts[k]}")

    return f"{', '.join([f'{k}{func(k)}' for k in counts.keys()])}"

"""
a = [13.4, 16.8, 22.2, 31.6, 16]
r = round_percentages(a)
print(f"{a}, sum={np.sum(a)}")
print(f"{r}, sum={np.sum(r)}")

[13.4, 16.8, 22.2, 31.6, 16], sum=100.0
[13. 17. 22. 32. 16.], sum=100.0
"""