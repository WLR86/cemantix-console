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


def display_csv(filename):
    dataset = load_csv(filename)
    # format the dataset to the output is neat
    dataset = [f"{row['word']}, {row['score']}, {row['percentile']}" for row in dataset]
    print("\n".join(dataset))


def write_csv(filename, word, score, percentile):
    with open(filename, 'a+', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([word, score, percentile])


word = input("Enter a word: ")
if (word == "Quit"):
    exit()
else:
    write_csv(filename, word, 0, 0)

s_cache = sorted(
        load_csv(filename),
        key=lambda x: (x['score'], x['percentile']),
        reverse=True)
print(s_cache)
display_csv(filename)
