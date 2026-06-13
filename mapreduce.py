from collections import defaultdict
from multiprocessing import Pool


# MAP function
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


# SHUFFLE
def shuffle(mapped):
    grouped = defaultdict(list)

    for sublist in mapped:
        for key, value in sublist:
            grouped[key].append(value)

    return grouped


# REDUCE
def reducer(grouped):
    return {k: sum(v) for k, v in grouped.items()}


# SPLIT
def split_data(lines, size=10):
    return [lines[i:i+size] for i in range(0, len(lines), size)]


# MAIN PIPELINE (PARALLEL MAPREDUCE)
def run_mapreduce(lines):
    chunks = split_data(lines)

    with Pool() as pool:
        mapped = pool.map(mapper, chunks)

    grouped = shuffle(mapped)
    reduced = reducer(grouped)

    return reduced