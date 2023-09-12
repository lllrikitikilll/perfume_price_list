import logging
import os
from dotenv import load_dotenv

import telebot
from telebot.apihelper import delete_message
from telebot.types import Message, CallbackQuery, InlineKeyboardButton

from database import get_ban_list, save_user_in_db, save_current_message_id, last_command, get_brands_with_alpha, \
    get_all_brands, get_brand_perfumes, get_one_perfume

from admin_utils import replace_photo, replace_price, add_perfume, del_perfume, info_admin, get_list_users
from utils import print_user_command, do_markup

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


def ban(func):
    """Проверка на содержание метки banned"""

    def wrapper(message: Message | CallbackQuery):
        if isinstance(message, Message):
            user_id = message.from_user.id
        else:
            user_id = message.message.chat.id
        banned = get_ban_list(user_id=user_id)
        if type(banned) is tuple and banned[0] == 1:
            print_user_command(message)
            return bot.send_message(user_id, 'Ошибка, разбираемся')
        return func(message)

    return wrapper


def restart(func):
    """При ошибке на клавиатуре удаляет сообщение и просит нажать /start"""

    def wrapper(message: Message | CallbackQuery):
        try:
            func(message)
        except Exception as e:

            if "Error code: 400" in str(e):
                print("Незачем модифицировать")
                return
            print(e)
            if isinstance(message, Message):
                to = message.from_user.id
                return bot.send_message(to, 'Ой-йой\nПопробуйте нажать на /start')

            else:
                to = message.message.chat.id
                return bot.send_message(to, 'Ой-йой\nПопробуйте нажать на /start')

    return wrapper


@bot.message_handler(commands=['info', 'users', 'price', 'add', 'del'])
@admin
def admin_command(message: Message):
    """Отправляет ответы только на команды администратора"""
    match list(map(lambda x: x.strip(), message.text.split(','))):
        case ['/info']:
            # Статистика посещений
            text = info_admin()
            bot.send_message(message.from_user.id, text)
        case ['/price', price] if price.isdigit():
            # Поменять цену парфюма
            perfume = last_command(user=message, option='get', value='last_perfume')
            replace_price(perfume=perfume, price=int(price))
            bot.send_message(message.from_user.id, "Цена изменена\n/start")
        case ['/add', str(brand), str(name), price] if price.isdigit():
            # Добавить парфюм
            add_perfume(new_perfume=(brand, name, int(price)))
            bot.send_message(message.from_user.id, f"Добавлен: {brand} {name}")
        case ['/del', str(name)]:
            # Удалить парфюм
            del_perfume(name=name)
            bot.send_message(message.from_user.id, f"Удален парфюм: {name}")
        case ['/users']:
            # Показать пользователей
            bot.send_message(message.from_user.id, get_list_users())
        case _:
            bot.send_message(message.from_user.id, "Ошибка в команде")


@bot.message_handler(content_types=['document'])
@admin
def handle_docs_photo(message: Message):
    """Изменить фото парфюма"""
    try:
        brand = last_command(user=message, option='get', value='last_brand')
        perfume = last_command(user=message, option='get', value='last_perfume')
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        file_name = perfume + '.' + message.document.file_name.split('.')[-1]
        src = './tmp/' + file_name
        replace_photo(perfume=perfume, photo=file_name)
        with open(src, 'wb') as new_file:
            new_file.write(downloaded_file)
        bot.reply_to(message, f"Смена фото для {brand}: {perfume}")
    except Exception as e:
        bot.reply_to(message, f"Проблема '{e}'\nДавай фото как файл\nПосмотреть продукцию /start")


@bot.message_handler(commands=['start'])
@restart
@ban
def start_bot(message: Message):
    """Обработчик команд пользователей"""
    print_user_command(message)
    #last_command(user=message, option='save')
    match message.text:
        case '/start':
            old_user = save_user_in_db(user=message)
            markup = do_markup(ALPHA, row=5)  # Создаем алфавитные кнопки шириной в 5 столбцов
            text = "🔠 Выберите бренд, начинающийся с указанной буквы:"

            if old_user:
                # Если такой пользователь есть, то пытаемся удалить прошлое меню и отправить новое
                try:
                    delete_message(TOKEN, chat_id=old_user[1], message_id=old_user[0])
                except Exception as e:
                    print(e)
            msg = bot.send_message(message.chat.id, text, reply_markup=markup)
            save_current_message_id(option='save', id=msg.id, chat_id=msg.chat.id)


@bot.message_handler(content_types=['text'])
def just_see(message):
    """Выводит в консоль сообщения пользователя"""
    print_user_command(message)


@bot.callback_query_handler(lambda call: call.data)
@restart
@ban
def callback(call: CallbackQuery):
    """Обработчик inline кнопок с продукцией"""
    #last_command(user=call, option='save')
    print_user_command(call)
    # Поиск по первой букве, возвращает бренды
    if call.data in ALPHA:
        markup = do_markup(get_brands_with_alpha(call=call), row=2)
        markup.row(InlineKeyboardButton('⬅ Назад', callback_data='back_to_alpha'))
        bot.edit_message_text(f"🔤 Бренды с начальной '{call.data}':", call.message.chat.id, call.message.id,
                              reply_markup=markup)

    # Поиск по бренду, возвращает линейку бренда
    elif call.data in get_all_brands():
        last_command(user=call, option='save', value='last_perfume')
        last_command(user=call, option='save', value='last_brand')
        markup = do_markup(get_brand_perfumes(call=call), row=2)
        markup.row(InlineKeyboardButton('⬅ Назад', callback_data='back_to_brand'))
        bot.edit_message_text(f"🌟 Линейка бренда '{call.data}':", call.message.chat.id, call.message.id,
                              reply_markup=markup)

    # Возвращает информацию о парфюме
    elif call.data in get_brand_perfumes(call=last_command(user=call, option='get', value='last_brand')):
        # Если текущий парфюм нажимается повторно
        if last_command(user=call, option='get', value='last_perfume') == call.data:
            bot.answer_callback_query(callback_query_id=call.id, text=f'Выбран {call.data}')  # Вызов "Вы уже выбрали"
        else:
            brand = last_command(user=call, option='get', value='last_brand')
            text, photo_name = get_one_perfume(call=call)
            last_command(user=call, option='save', value='last_perfume')
            markup = do_markup(get_brand_perfumes(call=brand), 2)
            markup.row(InlineKeyboardButton('⬅ Назад', callback_data='back_to_brand_with_delete'))

            if not photo_name:
                photo_name = 'духи2.jpg'  # Фотозаглушка
            photo = open('./tmp/' + photo_name, 'rb')

            delete_message(TOKEN, chat_id=call.message.chat.id, message_id=call.message.id)
            msg = bot.send_photo(caption=text, chat_id=call.message.chat.id, reply_markup=markup, photo=photo)
            save_current_message_id(option='save', id=msg.id, chat_id=msg.chat.id)

    # Возврат на страницу с буквами
    elif call.data == 'back_to_alpha':
        markup = do_markup(ALPHA, row=5)
        bot.edit_message_text("🔠 Выберите бренд, начинающийся с указанной буквы:", call.message.chat.id,
                              call.message.id, reply_markup=markup)

    # Возврат на страницу с брендами
    elif call.data == 'back_to_brand':
        alpha = last_command(user=call, option='get', value='last_brand')[0]
        markup = do_markup(get_brands_with_alpha(call=alpha), row=2)
        markup.row(InlineKeyboardButton('⬅ Назад', callback_data='back_to_alpha'))
        bot.edit_message_text(f"🔤 Бренды с начальной '{alpha}':", call.message.chat.id, call.message.id,
                              reply_markup=markup)

    # Возврат на страницу с брендами с перезаписью сообщения
    elif call.data == 'back_to_brand_with_delete':
        alpha = last_command(user=call, option='get', value='last_brand')[0]
        markup = do_markup(get_brands_with_alpha(call=alpha), row=2)
        markup.row(InlineKeyboardButton('⬅ Назад', callback_data='back_to_alpha'))
        delete_message(TOKEN, chat_id=call.message.chat.id, message_id=call.message.id)
        msg = bot.send_message(call.message.chat.id, f"🔤 Бренды с начальной '{alpha}':", reply_markup=markup)
        save_current_message_id(option='save', id=msg.id, chat_id=msg.chat.id)


if __name__ == '__main__':
    print('Работаем')
    bot.infinity_polling(logger_level=logging.INFO)
