#from wsgiref.util import shift_path_info
import config
import csv

def db_clear():
    return

def db_select(user_id, requset):
    pointer = {"user_id": 0, "state": 1, "game_name": 2, "possible_texts": 3, "current_text": 4}
    with open(config.db_file, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            if int(row[0]) == user_id:
                return row[pointer[requset]]
    return config.States.S_BOT_START.value


def db_insert(user_id, request, value):
    pointer = {"user_id": 0, "state": 1, "game_name": 2, "possible_texts": 3, "current_text": 4}
    sessions = []
    is_session_exist = False

    with open(config.db_file, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            if int(row[0]) == user_id:
                row[pointer[request]] = value
                is_session_exist = True
            sessions.append(row)
    
    with open(config.db_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames = ['user_id', 'state', 'game_name', 'possible_texts', 'current_text'])
        for row in sessions:
            writer.writerow({'user_id': row[0], 'state': row[1], 'game_name': row[2], 'possible_texts': row[3], 'current_text': row[4]})
        if not is_session_exist:
            line = {'user_id': user_id, 'state': '', 'game_name': '', 'possible_texts': '', 'current_text': ''}
            line[request] = value
            writer.writerow(line)