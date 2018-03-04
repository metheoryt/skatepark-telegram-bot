import logging
from telegram import Update
from telegram.ext import CommandHandler
from telegram import KeyboardButton as Btn, ReplyKeyboardMarkup as Kbd

from db.models import Client
from db import db_context, dbc
from dialog.admin.notify import aware_about_new_client
from thebot import new_dialog, private_only
from bot import bot, dispatcher
from ctx import x
from replies import Reply
from util.menu import client_menu

log = logging.getLogger(__name__)


def create_client(update) -> Client:
    contact = update.message.contact
    client = Client(
        tg_id=contact.user_id,
        first_name=contact.first_name,
        last_name=contact.last_name,
        phone=contact.phone_number
    )

    dbc.s.add(client)

    dbc.s.commit()

    return client


@private_only
@new_dialog
@db_context
def welcome(update: Update):
    """
    /start
    Проверить, существует ли такой клиент
    Существующих приветствует и предлагает меню
    Несуществующих регистрирует, и уведомляет админа(ов)
    """

    if not x.client:
        u = yield Reply(
            text='Добро пожаловать в скейт-парк "ЦЕХ"! Представьтесь, пожалуйста',
            reply_markup=Kbd(
                [[Btn('Вот мой контакт', request_contact=True)]],
                resize_keyboard=True,
                one_time_keyboard=True
            )
        )
        """:type: Update"""

        client = create_client(u)
        change_fi = f'Приятно познакомиться, {client.first_name}!\n' \
                    f'Ваш персональный ID - {client.id}\n' \
                    f'Хотите изменить имя и фамилию? ' \
                    f'Если вы укажете реальное имя, нам с вами будет легче общаться'
        u = yield Reply(text=change_fi, reply_markup=Kbd(
            [[Btn('Да, хочу'), Btn('Нет, всё в порядке')]],
            resize_keyboard=True,
            one_time_keyboard=True
        ))
        """:type: Update"""

        if u.message.text == 'Да, хочу':
            u = yield Reply('Напишите ваше имя и фамилию', remove_kb=True)
            while True:
                fi = u.message.text.title().split()
                if len(fi) != 2:
                    u = yield 'Я думаю, двух слов вам должно хватить, попробуйте ещё раз'
                else:
                    break

            client.first_name, client.last_name = fi
            dbc.s.commit()
            aware_about_new_client(client)
            yield Reply(f'Отлично, добро пожаловать, {client.first_name}!', remove_kb=True)
        else:
            aware_about_new_client(client)
            yield Reply(f'Ну что ж, добро пожаловать, {client.first_name}!', remove_kb=True)
    else:
        yield from client_menu()


dispatcher.add_handler(CommandHandler('start', welcome))
