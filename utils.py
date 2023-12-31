import datetime
from math import ceil
from telebot.types import Message, CallbackQuery
from telebot.util import quick_markup


def print_user_command(data: Message | CallbackQuery) -> None:
    """Выводит действия пользователя на экран"""
    if isinstance(data, Message):
        text = f'{(datetime.datetime.now() + datetime.timedelta(hours=3)).strftime("%d.%m | %H:%M:%S")} | {data.from_user.first_name:^20} | {data.text}'
    else:
        text = f'{(datetime.datetime.now() + datetime.timedelta(hours=3)).strftime("%d.%m | %H:%M:%S")} | {data.from_user.first_name:^20} | {data.data}'
    print(text)


def do_markup(data, row=5):
    """Создание инлайн кнопок"""
    dct = {}
    for item in data:
        dct[item] = {'callback_data': item}
    markup = quick_markup(dct, row_width=row)
    return markup


def round_price(price):
    return int(ceil(price / 50)) * 50