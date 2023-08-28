import datetime

from telebot.types import Message, CallbackQuery
from telebot.util import quick_markup


def print_user_command(data: Message | CallbackQuery) -> None:
    """Выводит действия пользователя на экран"""
    if isinstance(data, Message):
        print(f'{datetime.datetime.now()} | {data.from_user.first_name:^20} | {data.text}')
    else:
        print(f'{datetime.datetime.now()} | {data.from_user.first_name:^20} | {data.data}')


def do_markup(data, row=5):
    """Создание инлайн кнопок"""
    dct = {}
    for item in data:
        dct[item] = {'callback_data': item}
    markup = quick_markup(dct, row_width=row)
    return markup
