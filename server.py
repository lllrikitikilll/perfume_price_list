import os
from dotenv import load_dotenv

import telebot
from telebot.apihelper import delete_message
from telebot.types import Message, CallbackQuery, InlineKeyboardButton

from utils import print_user_command

load_dotenv('./config.env')
TOKEN = os.getenv('TELEGRAM_TOKEN')
ADMIN = os.getenv('TELEGRAM_ADMIN')

ALPHA = list("ABCEFGHIJKLMNOPRSTVWZ")
ALPHA.append('123...')  # начальные буквы парфюма


bot = telebot.TeleBot(TOKEN)


def admin(func):
    """Проверка на админа"""
    def wrapper(message: Message):
        print_user_command(message)
        if str(message.from_user.id) not in ADMIN:
            return
        return func(message)
    return wrapper


def restart(func):
    """При ошибке на клавиатуре удаляет сообщение и просит нажать /start"""
    def wrapper(message: Message | CallbackQuery):
        try:
            func(message)
        except Exception as e:
            print(e)
            if isinstance(message, Message):
                to = message.from_user.id
                return bot.send_message(to, 'Ой-йой\nПопробуйте нажать на /start')

            else:
                to = message.message.chat.id
                delete_message(TOKEN, chat_id=message.message.chat.id, message_id=message.message.id)
                return bot.send_message(to, 'Ой-йой\nПопробуйте нажать на /start')
    return wrapper