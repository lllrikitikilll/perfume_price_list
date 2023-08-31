from datetime import datetime, date
from database import db


@db
def info_admin(cursor) -> str:
    """Возвращает текст с информацией о пользователях"""
    today = date.today()
    res = cursor.execute("SELECT time_add FROM users ")
    all_users = res.fetchall()
    new_users = [i[0] for i in all_users if datetime.fromisoformat(i[0]).date() == today]
    # res = cursor.execute(f"SELECT time_last_command FROM users ")
    # using_today = [i[0] for i in res.fetchall() if datetime.fromisoformat(i[0]).date() == today]
    text = f'Всего пользователей бота: {len(all_users)}\n'
    text += f'Новых за сегодня: {len(new_users)}\n'
    # text += f'Ботом воспользовалось: {len(using_today)}\n'
    text += f'{"_" * 35}\nПосмотреть продукцию /start\n'
    text += """Посмотреть статистику /info\nПосмотреть пользователей /users"""

    return text


@db
def get_list_users(cursor):
    """Вернуть список пользователей"""
    users = cursor.execute("SELECT first_name, time_add FROM users ORDER BY time_add DESC")
    text = ''
    for user in users.fetchall():
        text += f'{user[1].split(".")[0]}\n{user[0]}\n\n'
    return text


@db
def add_perfume(cursor, new_perfume):
    brand = new_perfume[0]
    name = new_perfume[1]
    full_price = new_perfume[2]
    three_ml = new_perfume[3]
    five_ml = new_perfume[4]
    ten_ml = new_perfume[5]
    cursor.execute(
        """INSERT INTO perfumes
        (brand_name, name, price, price_3ml, price_5ml, price_10ml)
        VALUES(?,?,?,?,?,?)""",
        (brand, name, full_price, three_ml, five_ml, ten_ml))


@db
def del_perfume(cursor, name):
    cursor.execute(f"""DELETE FROM perfumes WHERE name='{name}'""")


@db
def replace_photo(cursor, photo, perfume):
    """Замена фото """
    cursor.execute(f"""UPDATE perfumes SET photo='{photo}' WHERE name = '{perfume}'""")


@db
def replace_price(cursor, perfume, price):
    """Замена цены парфюма"""
    cursor.execute(f"""UPDATE perfumes SET price='{price[0]}', price_3ml='{price[1]}', price_5ml='{price[2]}',
     price_10ml='{price[3]}' WHERE name = '{perfume}'""")
