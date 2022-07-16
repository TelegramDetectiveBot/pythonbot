from telebot import types
from enum import Enum

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

class buttons(Enum):
    B_PAGE_BACK = "Назад"
    B_PAGE_FORWARD = "Вперед"
    B_BACKSTORY = "Предыстроия"
    B_ALL_TEXTS = "Все показания"
    B_ACCUSE = "Обвинить"
    B_PREVIOUS_TEXT = "Предыдущий текст"
