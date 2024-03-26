import csv

filename = "/home/willy/.cemantix/cem755.csv"
# load a csv file from disk


def load_csv(filename):
    dataset = list()
    with open(filename, 'r') as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            if not row:
                continue
            dataset.append({
                    'word': row[0],
                    'score': float(row[1]),
                    'percentile': int(row[2])
                })
    return dataset


s_cache = sorted(
        load_csv(filename),
        key=lambda x: (x['score'], x['percentile']),
        reverse=True)
print(s_cache)
