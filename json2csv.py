import json
import csv


json_file_path = r"T:\RL-Replayer\scratch\replay_test_220926.json"
csv_file_path = json_file_path.replace(".json",".csv")

with open(json_file_path) as json_file:
    jsondata = json.load(json_file)

data_file = open(csv_file_path, 'w', newline='')
csv_writer = csv.writer(data_file)

count = 0
for data in jsondata:
    if count == 0:
        header = data.keys()
        csv_writer.writerow(header)
        count += 1
    csv_writer.writerow(data.values())

data_file.close()
