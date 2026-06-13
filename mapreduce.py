from collections import defaultdict
from multiprocessing import Pool

# ---------------- MAP ----------------
def mapper(chunk):
    results = []

    for line in chunk:
        if "404" in line:
            results.append(("404", 1))
        if "500" in line:
            results.append(("500", 1))

        for hour in range(24):
            if f"{hour}:" in line:
                results.append((f"Hour_{hour}", 1))
                break

    return results

# ---------------- SHUFFLE ----------------
def shuffle(mapped_data):
    grouped = defaultdict(list)

    for item in mapped_data:
        for key, value in item:
            grouped[key].append(value)

    return grouped

# ---------------- REDUCE ----------------
def reducer(grouped):
    return {k: sum(v) for k, v in grouped.items()}

# ---------------- SPLIT ----------------
def split_data(lines, chunk_size=10):
    return [lines[i:i+chunk_size] for i in range(0, len(lines), chunk_size)]

# ---------------- MAPREDUCE ----------------
def run_mapreduce(lines):
    chunks = split_data(lines)

    with Pool() as pool:
        mapped = pool.map(mapper, chunks)

    grouped = shuffle(mapped)
    reduced = reducer(grouped)

    return reduced