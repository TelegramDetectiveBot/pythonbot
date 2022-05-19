import config
import csv

# Пытаемся узнать из базы «состояние» пользователя
def get_current_state(user_id):
    dict_from_csv = {}

    with open(config.db_file, mode='r') as inp:
        reader = csv.reader(inp)
        dict_from_csv = {rows[0]:rows[1] for rows in reader}
        try:
            return dict_from_csv[str(user_id)]
        except:
            return config.States.S_START.value

# Сохраняем текущее «состояние» пользователя в нашу базу
def set_state(user_id, value):
    dict_from_csv = {}
    with open(config.db_file, mode='r') as inp:
        reader = csv.reader(inp)

        dict_from_csv = {rows[0]:rows[1] for rows in reader}
        try:
            dict_from_csv[str(user_id)] = value
        except:
            # тут желательно как-то обработать ситуацию
            return False
    with open(config.db_file, 'w') as f:
        for key in dict_from_csv.keys():
            f.write("%s,%s\n" % (key, dict_from_csv[key]))