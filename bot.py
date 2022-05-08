import telebot
import json
import os
from pprint import pprint 

def get_token():
    f = open("token", "r")
    token = f.read()
    f.close()
    return token

bot = telebot.TeleBot(get_token())
sessions = []

def get_game(game_name):
    with open("games/"+game_name+".json", 'r', encoding='utf-8') as f:
        game = json.load(f)
    return game

def add_new_game(user_id, game):
    global sessions
    if sessions == []:
        sessions = [{"user_id": user_id, "game_name": game["Name"], "possible texts": game["Available texts"]}]
    else:
        sessions.append({"user_id": user_id, "game_name": game["Name"], "possible texts": game["Available texts"]})

def exit_game(user_id):
    global sessions
    for i, session in enumerate(sessions):
        if session["user_id"] == user_id:
            sessions.erase(i)
            return

def start_game(message):
    user_id = message.chat.id
    game_name = message.text
    game = get_game(game_name)

    add_new_game(user_id, game)

    bot.send_message(message.chat.id, game["Name"])
    bot.send_message(message.chat.id, game["Start text"])
    for text_id in game["Available texts"]:
        bot.send_message(message.chat.id, game["Texts"][text_id - 1]["Bot text"])

@bot.message_handler(commands=["start"])
def start(message, res=False):
    dirname = os.getcwd() + "/games"
    files = os.listdir(dirname)

    bot.send_message(message.chat.id, "Приветствую! Выбери игру:")
    for game in files:
        bot.send_message(message.chat.id, game[:-5])

    bot.register_next_step_handler(message, start_game)


@bot.message_handler(content_types=["text"])
def state(message):
    global sessions
    user_id = message.chat.id
    game_name = ""
    for session in sessions:
        if session["user_id"] == user_id:
            game_name = session["game_name"]

    game = get_game(game_name)
    state_id = int(message.text)

    if state_id == 0:
        bot.send_message(message.chat.id, game["Name"])
        bot.send_message(message.chat.id, game["Start text"])

    if state_id == -1:
        bot.send_message(message.chat.id, game["Final text"])
        exit_game(message.chat.id)

    if state_id != 0 and state_id != 1:
            bot.send_message(message.chat.id, game["Texts"][state_id]["Bot text"])

bot.polling(none_stop=True, interval=0)