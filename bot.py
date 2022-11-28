import sys
import os
sys.path.append(os.getcwd()+"/telebot")

import telebot
from telebot import types

import buttons
import dbworker
import config

import json

bot = telebot.TeleBot(config.token)

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


def get_text(game, text_id):
    id = text_id.split(".")
    first_id = int(id[0])
    current_text = game["Texts"][first_id]
    if len(id) > 1:
        for current_id in id[1:]:
            current_text = current_text["Subtexts"][int(current_id)]
    return current_text


def get_game(game_name):
    with open("games/"+game_name+".json", 'r', encoding='utf-8') as f:
        game = json.load(f)
    return game


def get_game_name(user_id):
    return dbworker.db_select(user_id, "game_name")


def add_new_game(user_id, game):
    dbworker.db_insert(user_id, "game_name", game["Name"])
    dbworker.db_insert(user_id, "possible_texts", game["Available texts"])
    dbworker.db_insert(user_id, "current_text", "0")


def update_current_text(user_id, text_id):
    dbworker.db_insert(user_id, "current_text", text_id)


def update_current_state(user_id, state):
    dbworker.db_insert(user_id, "state", state)


def get_possible_texts(user_id):
    possible_texts = dbworker.db_select(user_id, "possible_texts").strip('][').split(', ')
    possible_texts = [int(x) for x in possible_texts]
    return possible_texts


def update_possible_texts(user_id, text_id_array):
    lst = get_possible_texts(user_id)

    for text_id in text_id_array:
        is_available = False
        for available_text in lst:
            if text_id == available_text:
                is_available = True
        if not is_available:
           lst = dbworker.db_select(user_id, "possible_texts").strip('][').split(', ')
           lst = [int(x) for x in lst]
           lst.append(text_id)
           dbworker.db_insert(user_id, "possible_texts", lst)


def start_game(user_id, game_name):
    game = get_game(game_name)
    send_text(user_id, game["Name"])
    send_text(user_id, game["Start text"])
    string_array = [game["Texts"][int(i)]["Name"] for i in game["Available texts"]]
    update_current_state(user_id, config.States.S_MAIN_MENU.value)
    keyboard = get_keyboard(user_id, string_array)
    bot_str = get_string(game, game["Available texts"])
    send_text(user_id, bot_str, keyboard)


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
        keyboard.add(buttons.buttons.B_PAGE_FORWARD.value)
    send_text(message.chat.id, ["Выберите игру:"], keyboard)
    update_current_state(message.chat.id, config.States.S_CHOOSE_GAME.value)


def get_keyboard(user_id, string_array = None):
    if string_array is None:
        string_array = []
    markup_array = [1] * (len(string_array))
    current_state = dbworker.db_select(user_id, "state")

    if current_state == config.States.S_CHOOSE_TEXT.value:
        markup_array.append(1)
        string_array.append(buttons.buttons.B_BACKSTORY.value)
        markup_array.append(1)
        string_array.append(buttons.buttons.B_ALL_TEXTS.value)
        markup_array.append(1)
        string_array.append(buttons.buttons.B_ACCUSE.value)

    if current_state == config.States.S_CHOOSE_ANSWER.value:
        markup_array.append(1)
        string_array.append(buttons.buttons.B_BACKSTORY.value)
        markup_array.append(1)
        string_array.append(buttons.buttons.B_ALL_TEXTS.value)

    if current_state == config.States.S_MAIN_MENU.value:
        markup_array.append(1)
        string_array.append(buttons.buttons.B_BACKSTORY.value)

    if len(dbworker.db_select(user_id, "current_text").split(".")) > 1:
        markup_array.append(1)
        string_array.append(buttons.buttons.B_PREVIOUS_TEXT.value)

    keyboard = buttons.button_generator(markup_array, string_array)
    return keyboard


def get_string(game, possible_texts):
    bot_str = "Вы можете ознакомиться со следующими материалами:\n"
    for text_id in possible_texts:
        bot_str += "\n" + game["Texts"][int(text_id)]["Name"]
    bot_str += "\n" + buttons.buttons.B_BACKSTORY.value
    return [bot_str]


def answers_keyboard(answers):
    markup_array = [1] * len(answers)
    markup_array.append(1)
    string_array = answers
    string_array.append(buttons.buttons.B_ALL_TEXTS.value)
    keyboard = buttons.button_generator(markup_array, string_array)
    return keyboard

@bot.message_handler(func=lambda message: dbworker.db_select(message.chat.id, "state") == config.States.S_CHOOSE_GAME.value)
def list_of_games_paging(message):
    global PAGE
    global ITEMS_ON_PAGE
    if message.text == buttons.buttons.B_PAGE_FORWARD.value:
        PAGE = PAGE + 1
    elif message.text == buttons.buttons.B_PAGE_BACK.value:
        PAGE = PAGE - 1
    else:
        try:
            add_new_game(message.chat.id, get_game(message.text))
        except:
            choose_game(message)
            return
        update_current_state(message.chat.id, config.States.S_CHOOSE_TEXT.value)
        game_name = get_game_name(message.chat.id)
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

    if PAGE != 0:
        keyboard.add(buttons.buttons.B_PAGE_BACK.value)
    if PAGE * ITEMS_ON_PAGE + ITEMS_ON_PAGE != len(filenames):
        keyboard.add(buttons.buttons.B_PAGE_FORWARD.value)

    send_text(message.chat.id, "Выберите игру:", keyboard)


@bot.message_handler(commands=["start"])
def start(message, res=False):
    #user_id = message.chat.id
    choose_game(message)


@bot.message_handler(content_types=["text"], func=lambda message: dbworker.db_select(message.chat.id, "state") == config.States.S_MAIN_MENU.value)
def main_menu(message):
    user_id = message.chat.id
    game_name = get_game_name(user_id)
    game = get_game(game_name)
    text_id = dbworker.db_select(user_id, "current_text")
    text = get_text(game, text_id)
    
    ok = 0
    for i, main_text in enumerate(game["Texts"]):
        if main_text["Name"] == message.text:
            update_current_text(user_id, i)
            text = get_text(game, str(i))
            ok = 1
    for butt in buttons.buttons:
        if message.text == butt.value:
            ok = 1
    if(not ok):
            possible_texts = get_possible_texts(user_id)
            string_array = [game["Texts"][int(i)]["Name"] for i in possible_texts]
            keyboard = get_keyboard(user_id, string_array)
            bot_str = get_string(game, possible_texts)
            send_text(user_id, bot_str, keyboard)
            return
    if "Questions" in text:
        update_current_state(user_id, config.States.S_CHOOSE_TEXT.value)
        keyboard = get_keyboard(user_id, text["Questions"])
        send_text(user_id, text["Bot text"], keyboard)
    else:
        update_current_state(user_id, config.States.S_CHOOSE_TEXT.value)
        keyboard = get_keyboard(user_id)
        send_text(user_id, text["Bot text"], keyboard)    


@bot.message_handler(content_types=["text"], func=lambda message: dbworker.db_select(message.chat.id, "state") == config.States.S_CHOOSE_TEXT.value)
def main_text_step(message):
    user_id = message.chat.id
    game_name = get_game_name(user_id)
    game = get_game(game_name)

    if message.text == buttons.buttons.B_PREVIOUS_TEXT.value:
        text_id = dbworker.db_select(user_id, "current_text")
        text_id = text_id[:-2]
        update_current_text(user_id, text_id)
        text = get_text(game, text_id)
        if "Questions" in text:
            keyboard = get_keyboard(user_id, text["Questions"])
            send_text(user_id, text["Bot text"], keyboard)
        else:
            update_current_state(user_id, config.States.S_CHOOSE_ANSWER.value)
            keyboard = get_keyboard(user_id, text["Answers"])
            send_text(user_id, text["Bot text"], keyboard)

    if message.text == buttons.buttons.B_BACKSTORY.value:
        keyboard = get_keyboard(user_id)
        send_text(user_id, game["Start text"], keyboard)

    if message.text == buttons.buttons.B_ALL_TEXTS.value:
        possible_texts = get_possible_texts(message.chat.id)
        string_array = [game["Texts"][int(i)]["Name"] for i in possible_texts]
        update_current_state(user_id, config.States.S_MAIN_MENU.value)
        keyboard = get_keyboard(user_id, string_array)
        bot_str = get_string(game, possible_texts)
        send_text(user_id, bot_str, keyboard)

    if message.text == buttons.buttons.B_ACCUSE.value:
        text_id = dbworker.db_select(user_id, "current_text")
        text = get_text(game, text_id)
        update_current_state(user_id, config.States.S_CHOOSE_ANSWER.value)
        keyboard = get_keyboard(user_id, text["Answers"])
        send_text(user_id, text["Bot text"], keyboard)

    if message.text != buttons.buttons.B_BACKSTORY.value and message.text != buttons.buttons.B_ALL_TEXTS.value and message.text != buttons.buttons.B_ACCUSE.value and message.text != buttons.buttons.B_PREVIOUS_TEXT.value:
        text_id = dbworker.db_select(user_id, "current_text")
        text = get_text(game, text_id)

        ok = 0
        for i, main_text in enumerate(game["Texts"]):
            if main_text["Name"] == message.text:
                update_current_text(user_id, i)
                text = get_text(game, str(i))
                ok = 1
        if(not ok):
            keyboard = get_keyboard(user_id)
            send_text(user_id, text["Bot text"], keyboard)   
            return
        if "Questions" in text:
            for i, question in enumerate(text["Questions"]):
                if message.text == question:
                    text_id += "." + str(i)
                    update_current_text(user_id, text_id)
            text = get_text(game, text_id)

        if "Questions" in text:
            keyboard = get_keyboard(user_id, text["Questions"])
            send_text(user_id, text["Bot text"], keyboard)
        else:
            keyboard = get_keyboard(user_id)
            send_text(user_id, text["Bot text"], keyboard)


@bot.message_handler(content_types=["text"], func=lambda message: dbworker.db_select(message.chat.id, "state") == config.States.S_CHOOSE_ANSWER.value)
def choose_answer(message):
    user_id = message.chat.id
    game_name = get_game_name(user_id)
    game = get_game(game_name)
    text_id = dbworker.db_select(user_id, "current_text")
    text = get_text(game, text_id)

    if message.text == buttons.buttons.B_ALL_TEXTS.value:
        possible_texts = get_possible_texts(user_id)
        string_array = [game["Texts"][int(i)]["Name"] for i in possible_texts]
        update_current_state(message.chat.id, config.States.S_CHOOSE_TEXT.value)
        keyboard = get_keyboard(user_id, string_array)
        bot_str = get_string(game, possible_texts)
        send_text(user_id, bot_str, keyboard)
        return

    answer_id = -1
    for i, answer in enumerate(text["Answers"]):
        if answer == message.text:
            answer_id = i

    if answer_id == -1:
        keyboard = get_keyboard(user_id, text["Answers"])
        send_text(user_id, text["Name"] + ":")
        send_text(user_id, text["Bot text"], keyboard)
        return
    elif answer_id == text["Right answer"]:
        send_text(user_id, text["Detailed answers"][answer_id])
        if text["Next text"] == "Final":
            update_current_state(message.chat.id, config.States.S_CHOOSE_GAME.value)
            send_text(user_id, text["Reaction"][answer_id])
            send_text(user_id, game["Final text"])
            choose_game(message)
        else:
            send_text(user_id, text["Reaction"][answer_id])
            update_possible_texts(user_id, text["Next text"])
            update_current_state(message.chat.id, config.States.S_MAIN_MENU.value)
            possible_texts = get_possible_texts(user_id)
            string_array = [game["Texts"][int(i)]["Name"] for i in possible_texts]
            keyboard = get_keyboard(user_id, string_array)
            bot_str = get_string(game, possible_texts)
            send_text(user_id, bot_str, keyboard)
    else:
        send_text(user_id, text["Detailed answers"][answer_id])
        send_text(user_id, text["Reaction"][answer_id])
        keyboard = get_keyboard(user_id, text["Answers"])
        send_text(user_id, text["Name"] + ":")
        send_text(user_id, text["Bot text"], keyboard)


dbworker.db_clear()
bot.polling(none_stop=True, interval=0)