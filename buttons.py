import telebot
from telebot import types
from os import walk

PAGE = 0
ITEMS_ON_PAGE = 3

def get_token():
    f = open("token", "r")
    token = f.read()
    f.close()
    return token

bot = telebot.TeleBot(get_token())

@bot.message_handler(commands="reply")
def button_generator(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard = True, one_time_keyboard = True)
    test_array = [1,2,1]
    test_strings = ["abc","abcd","abcde","blyad"]
    prev_number = 0
    for number in test_array:
        line = []
        for i in range(prev_number, number + prev_number):
            line.append(test_strings[i])
        keyboard.add(*line)
        prev_number = number + prev_number

    return keyboard
    #returning ReplyKeyboardMarkup

@bot.message_handler(commands="list")
def list_of_games(message):
    global ITEMS_ON_PAGE
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard = True, one_time_keyboard = True)
    filenames = next(walk("games"), (None, None, []))[2]
    print(filenames)
    counter = 0
    items = ITEMS_ON_PAGE
    if len(filenames) < ITEMS_ON_PAGE:
        items = len(filenames)
    for i in range (items):
        keyboard.add(filenames[i])
    if len(filenames) > ITEMS_ON_PAGE:
        keyboard.add("Далее")
    msg = bot.send_message(message.chat.id, "Выберите игру:", reply_markup = keyboard)
    game_name = bot.register_next_step_handler(msg, list_of_games_paging)
    print(game_name)
    return game_name

def list_of_games_paging(message):
    global PAGE
    global ITEMS_ON_PAGE
    if message.text == "Далее":
        PAGE = PAGE + 1
    elif message.text == "Назад":
        PAGE = PAGE - 1
    else:
        print(message.text)
        return message.text
    
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard = True, one_time_keyboard = True)
    filenames = next(walk("games"), (None, None, []))[2]
    items = PAGE * ITEMS_ON_PAGE + ITEMS_ON_PAGE
    if len(filenames) < items:
        items = len(filenames)
    for i in range (PAGE * ITEMS_ON_PAGE, items):
        keyboard.add(filenames[i])
    if PAGE == 0:
        keyboard.add("Далее")
    else:
        if len(filenames) > PAGE * ITEMS_ON_PAGE + ITEMS_ON_PAGE:
            keyboard.add("Назад", "Далее")
        else:
            keyboard.add("Назад")
    msg = bot.send_message(message.chat.id, "Выберите игру:", reply_markup = keyboard)
    bot.register_next_step_handler(msg, list_of_games_paging)


bot.polling(non_stop = True)