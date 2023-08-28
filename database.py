import sqlite3
from datetime import datetime

from telebot.types import Message, CallbackQuery

def db(func):
    def wrapper(*args, **kwargs):
        conn = sqlite3.connect('perfume.db')
        cursor = conn.cursor()
        data = func(cursor=cursor, *args, **kwargs)
        conn.commit()
        conn.close()
        return data

    return wrapper