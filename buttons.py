from telebot import types

def button_generator(markup_array, string_array):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard = True, one_time_keyboard = True)
    prev_number = 0
    for number in markup_array:
        line = []
        for i in range(prev_number, number + prev_number):
            line.append(string_array[i])
        keyboard.add(*line)
        prev_number = number + prev_number

    return keyboard
    #returning ReplyKeyboardMarkup