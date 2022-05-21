import config
import csv


def get_current_state(user_id, requset):
    pointer = {"user_id": 0, "state": 1, "game_name": 2, "possible_texts": 3, "current_text": 4}
    with open(config.db_file, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            if int(row[0]) == user_id:
                print("фул", row)
                print("че", requset, row[pointer[requset]])
                return row[pointer[requset]]
    return config.States.S_START.value


def set_state(user_id, request, value):
    pointer = {"user_id": 0, "state": 1, "game_name": 2, "possible_texts": 3, "current_text": 4}
    sessions = []
    with open(config.db_file, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            if int(row[0]) == user_id:
                row[pointer[request]] = value
            sessions.append(row)
    # print(sessions)
    with open(config.db_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames = ['user_id', 'state', 'game_name', 'possible_texts', 'current_text'])
        for row in sessions:
            writer.writerow({'user_id': row[0], 'state': row[1], 'game_name': row[2], 'possible_texts': row[3], 'current_text': row[4]})
