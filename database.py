import sqlite3
from datetime import datetime

from telebot.types import Message, CallbackQuery


def db(func):
    def wrapper(*args, **kwargs):
        conn = sqlite3.connect('perfume.db')
        cursor = conn.cursor()
        cursor.execute('''PRAGMA journal_mode=WAL''')
        data = func(cursor=cursor, *args, **kwargs)
        conn.commit()
        conn.close()
        return data

    return wrapper


# Работа с таблицей парфюма

@db
def get_all_brands(cursor):
    """Выборка всех брендов"""
    res = cursor.execute("SELECT DISTINCT brand_name FROM perfumes")
    data = res.fetchall()
    return list(map(lambda x: x[0], data))


@db
def get_brand_perfumes(cursor, call: CallbackQuery | str):
    """Выборка парфюма бренда"""
    if isinstance(call, CallbackQuery):
        brand = call.data
    else:
        brand = call
    res = cursor.execute(f"SELECT name FROM perfumes WHERE brand_name = '{brand}'")
    data = list(map(lambda x: x[0], res.fetchall()))
    return data


@db
def get_brands_with_alpha(cursor, call: CallbackQuery | str):
    """Выборка всех брендов"""
    if isinstance(call, CallbackQuery):
        alpha = call.data
    else:
        alpha = call
    if alpha[0].isdigit():
        res = cursor.execute("""SELECT DISTINCT brand_name FROM perfumes WHERE substr(brand_name, 1, 1)
                                BETWEEN '0' AND '9'""")
    else:
        res = cursor.execute(f"SELECT DISTINCT brand_name FROM perfumes WHERE brand_name LIKE '{alpha.upper()}%' ")
    data = res.fetchall()
    return list(map(lambda x: x[0], data))


@db
def get_one_perfume(cursor, call: CallbackQuery) -> tuple:
    """Возвращает текст с описанием парфюма"""
    value = call.data
    data = cursor.execute("""SELECT name, brand_name, price, price_3ml, price_5ml, price_10ml, photo
                                 FROM perfumes WHERE name = ?""", (value,))
    perfume = data.fetchone()
    text = f'{perfume[1]} {perfume[0]}\n'
    text += f'Цена за флакон: {int(perfume[2])} р.\n'
    text += f'Цена за 3мл: {int(perfume[3])} р.\n'
    text += f'Цена за 5мл: {int(perfume[4])} р.\n'
    text += f'Цена за 10мл: {int(perfume[5])} р.\n'
    text += '_'*30+'\n'
    text += 'Контакт для заказа @____'
    return text, perfume[-1]


# Работа с таблицей пользователя
@db
def save_user_in_db(cursor, user: Message | CallbackQuery):
    """Сохранение пользователя в БД"""
    if isinstance(user, Message):
        user_msg = user.from_user
    else:
        user_msg = user.message.from_user
    user = cursor.execute(f"""SELECT id FROM users WHERE users.id = {user_msg.id}""")
    if not user.fetchone():
        cursor.execute(
            """INSERT INTO users(id, first_name, last_name, username, time_add, baned, lifetime) VALUES(?,?,?,?,?,?,?)""",
            (user_msg.id, user_msg.first_name, user_msg.last_name, user_msg.username, datetime.now(), 0, datetime.now()))
    else:
        """Если пользователь есть берем id его сообщения меню"""
        current_msg_id = cursor.execute(f"""SELECT current_msg_id, id FROM users WHERE users.id = {user_msg.id}""")
        return current_msg_id.fetchone()


@db
def get_ban_list(cursor, user_id):
    """Проверка на пользователя на бан"""
    res = cursor.execute(f"SELECT baned FROM users WHERE id = {user_id}")
    ban = res.fetchone()
    return ban


@db
def save_current_message_id(cursor, chat_id, id=None, option='save'):
    """Сохранение id последнего сообщения меню"""
    if option == 'save':
        lifetime = datetime.now()
        cursor.execute(f"""UPDATE users SET current_msg_id={id}, lifetime='{lifetime}' WHERE users.id = {chat_id}""")
    elif option == 'get':
        msg_id = cursor.execute(f"""SELECT current_msg_id FROM users WHERE users.id = {chat_id}""")
        return msg_id.fetchone()[0]


@db
def last_command(cursor, user: CallbackQuery | Message, option: str = 'save', value: str = 'time_last_command'):
    """Запись команд в БД"""
    if isinstance(user, CallbackQuery):
        user_id = user.message.chat.id
        save_data = user.data
    else:
        user_id = user.chat.id
        save_data = user.text
    if option == 'save':
        if value == 'time_last_command':
            save_data = datetime.now()
        cursor.execute(f"""UPDATE users SET {value}='{save_data}' WHERE users.id = {user_id}""")
    elif option == 'get':
        res = cursor.execute(f"""SELECT {value} FROM users WHERE users.id = {user_id}""")
        return res.fetchone()[0]

@db
def get_lifetime(cursor, user_id):
    res = cursor.execute(f"""SELECT lifetime FROM users WHERE users.id = {user_id}""")
    return res.fetchone()