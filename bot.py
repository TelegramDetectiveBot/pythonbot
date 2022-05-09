import telebot
from telebot import types

import buttons
import dbworker
import config

import json
import os

bot = telebot.TeleBot(config.token)

sessions = []
PAGE = 0
ITEMS_ON_PAGE = 3

def send_text(user_id, text_array, keyboard = None):
    current_len = 0
    send_str = ""
    is_last_send = False
    for text in text_array:
        current_len += len(text) + 1
        send_str += text + " "
        if current_len >= config.max_message_char:
            if text == text_array[-1]:
                bot.send_message(user_id, send_str, reply_markup = keyboard)
                is_last_send = True
            else:
                bot.send_message(user_id, send_str)
            current_len = 0
            send_str = ""
    
    if not is_last_send:
        bot.send_message(user_id, send_str, reply_markup = keyboard)

def get_game(game_name):
    with open("games/"+game_name+".json", 'r', encoding='utf-8') as f:
        game = json.load(f)
    return game

def add_new_game(user_id, game):
    global sessions
    if sessions == []:
        sessions = [{"user_id": user_id, "game_name": game["Name"], "possible_texts": game["Available texts"], "current_text": 0}]
    else:
        sessions.append({"user_id": user_id, "game_name": game["Name"], "possible_texts": game["Available texts"], "current_text": 0})

def update_current_text(user_id, text_id):
    global sessions
    session_id = 0
    for i, session in enumerate(sessions):
        if session["user_id"] == user_id:
            session_id = i
    
    sessions[session_id]["current_text"] = text_id

def update_possible_texts(user_id, text_id_array):
    global sessions
    session_id = 0
    for i, session in enumerate(sessions):
        if session["user_id"] == user_id:
            session_id = i
    
    for text_id in text_id_array:
        is_available = False
        for available_text in sessions[session_id]["possible_texts"]:
            if text_id == available_text:
                is_available = True
        if not is_available:
           sessions[session_id]["possible_texts"].append(text_id) 

def exit_game(user_id):
    global sessions
    for i, session in enumerate(sessions):
        if session["user_id"] == user_id:
            sessions.pop(i)
            return

def start_game(user_id, game_name):
    game = get_game(game_name)

    bot.send_message(user_id, game["Name"])
    send_text(user_id, game["Start text"])
    markup_array = [1] * len(game["Available texts"])
    string_array = [game["Texts"][i]["Name"] for i in game["Available texts"]]
    keyboard = buttons.button_generator(markup_array, string_array)
    keyboard = all_texts_keyboard(game, game["Available texts"])
    bot_str = all_texts_string(game, game["Available texts"])
    bot.send_message(user_id, bot_str, reply_markup = keyboard)


def choose_game(message):
    global ITEMS_ON_PAGE
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard = True, one_time_keyboard = True)
    dirname = os.getcwd() + "/games"
    filenames = os.listdir(dirname)
    counter = 0
    items = ITEMS_ON_PAGE
    if len(filenames) < ITEMS_ON_PAGE:
        items = len(filenames)
    for i in range (items):
        keyboard.add(filenames[i][:-5])
    if len(filenames) > ITEMS_ON_PAGE:
        keyboard.add("Далее")
    bot.send_message(message.chat.id, "Выберите игру:", reply_markup = keyboard)
    dbworker.set_state(message.chat.id, config.States.S_CHOOSE_GAME.value)

def all_texts_keyboard(game, possible_texts):
    markup_array = [1] * (len(possible_texts) + 1)
    string_array = [game["Texts"][i]["Name"] for i in possible_texts]
    string_array.append("Начальный текст")
    keyboard = buttons.button_generator(markup_array, string_array)
    return keyboard

def all_texts_string(game, possible_texts):
    bot_str = "Доступные тексты:\n\n"
    for text_id in possible_texts:
        bot_str += "\n" + game["Texts"][text_id]["Name"]
    bot_str += "\nНачальный текст"
    return bot_str

def answers_keyboard(answers):
    markup_array = [1] * len(answers)
    markup_array.append(1)
    string_array = answers
    string_array.append("Все тексты")
    keyboard = buttons.button_generator(markup_array, string_array)
    return keyboard

@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_CHOOSE_GAME.value)
def list_of_games_paging(message):
    global PAGE
    global ITEMS_ON_PAGE
    if message.text == "Далее":
        PAGE = PAGE + 1
    elif message.text == "Назад":
        PAGE = PAGE - 1
    else:
        dbworker.set_state(message.chat.id, config.States.S_CHOOSE_TEXT.value)
        add_new_game(message.chat.id, get_game(message.text))
        game_name = ""
        for session in sessions:
            if session["user_id"] == message.chat.id:
                game_name = session["game_name"]
        start_game(message.chat.id, game_name)
        return
    
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard = True, one_time_keyboard = True)
    dirname = os.getcwd() + "/games"
    filenames = os.listdir(dirname)
    items = PAGE * ITEMS_ON_PAGE + ITEMS_ON_PAGE
    if len(filenames) < items:
        items = len(filenames)
    for i in range (PAGE * ITEMS_ON_PAGE, items):
        keyboard.add(filenames[i][:-5])
    if PAGE == 0:
        keyboard.add("Далее")
    else:
        if len(filenames) > PAGE * ITEMS_ON_PAGE + ITEMS_ON_PAGE:
            keyboard.add("Назад", "Далее")
        else:
            keyboard.add("Назад")
    bot.send_message(message.chat.id, "Выберите игру:", reply_markup = keyboard)

@bot.message_handler(commands=["start"])
def start(message, res=False):
    user_id = message.chat.id
    choose_game(message)

@bot.message_handler(content_types=["text"], func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_CHOOSE_TEXT.value)
def step(message):
    global sessions
    user_id = message.chat.id
    game_name = ""
    possible_texts = []
    for i, session in enumerate(sessions):
        if session["user_id"] == user_id:
            game_name = session["game_name"]
            possible_texts = session["possible_texts"]
    game = get_game(game_name)

    if message.text == "Начальный текст":
        markup_array = [1]
        string_array = ["Все тексты"]
        keyboard = buttons.button_generator(markup_array, string_array)
        send_text(user_id, game["Start text"], keyboard)

    if message.text == "Все тексты":
        keyboard = all_texts_keyboard(game, possible_texts)
        bot_str = all_texts_string(game, possible_texts)
        bot.send_message(user_id, bot_str, reply_markup = keyboard)

    if message.text != "Начальный текст" and message.text != "Все тексты":
        text_id = 0
        for text in game["Texts"]:
            if text["Name"] == message.text:
                text_id = text["Id"]
        update_current_text(user_id, text_id)
        keyboard = answers_keyboard(game["Texts"][text_id]["Answers"])
        send_text(user_id, game["Texts"][text_id]["Bot text"], keyboard)
        dbworker.set_state(message.chat.id, config.States.S_CHOOSE_ANSWER.value)

@bot.message_handler(content_types=["text"], func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_CHOOSE_ANSWER.value)
def choose_answer(message):
    global sessions
    user_id = message.chat.id
    game_name = ""
    text_id = 0
    possible_texts = []
    for session in sessions:
        if session["user_id"] == user_id:
            game_name = session["game_name"]
            text_id = session["current_text"]
            possible_texts = session["possible_texts"]
    game = get_game(game_name)

    if message.text == "Все тексты":
        dbworker.set_state(message.chat.id, config.States.S_CHOOSE_TEXT.value)
        keyboard = all_texts_keyboard(game, possible_texts)
        bot_str = all_texts_string(game, possible_texts)
        bot.send_message(user_id, bot_str, reply_markup = keyboard)
        return

    answer_id = 0
    for i, answer in enumerate(game["Texts"][text_id]["Answers"]):
        if answer == message.text:
            answer_id = i
    
    if answer_id == game["Texts"][text_id]["Right answer"]:
        if game["Texts"][text_id]["Next text"] == -1:
            dbworker.set_state(message.chat.id, config.States.S_CHOOSE_GAME.value)
            send_text(user_id, game["Texts"][text_id]["Correct reaction"])
            send_text(user_id, game["Final text"])
            exit_game(user_id)
            choose_game(message)
        else:
            send_text(user_id, game["Texts"][text_id]["Correct reaction"])
            update_possible_texts(user_id, game["Texts"][text_id]["Next text"])
            dbworker.set_state(message.chat.id, config.States.S_CHOOSE_TEXT.value)
            keyboard = all_texts_keyboard(game, possible_texts)
            bot_str = all_texts_string(game, possible_texts)
            bot.send_message(user_id, bot_str, reply_markup = keyboard)
    else:
        send_text(user_id, game["Texts"][text_id]["Incorrect reaction"])
        keyboard = answers_keyboard(game["Texts"][text_id]["Answers"])
        send_text(user_id, game["Texts"][text_id]["Bot text"], keyboard)



bot.polling(none_stop=True, interval=0)