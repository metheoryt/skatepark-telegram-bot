from enum import Enum
from db import dbc, db_context
from thebot import private_only, new_dialog
from ctx import x
from replies import Reply
from telegram import KeyboardButton as Btn, ReplyKeyboardMarkup as Kbd


class Actions(Enum):
    ENTER_RIDE = 'Покататься'
    ENTER_HANGOUT = 'Потусить'
    # ABOUT_ME = 'Обо мне' - отдельная коменда пизже


def client_menu():
    k = Kbd(
        [
            [Btn(Actions.ENTER_RIDE.value), Btn(Actions.ENTER_HANGOUT.value)]
        ],
        resize_keyboard=True, one_time_keyboard=True)
    u = yield Reply('Чего изволите?', reply_markup=k)
    while True:
        try:
            action = Actions(u.message.text)
        except Exception:
            u = yield 'Я не понимаю, чего вы хотите, давайте ещё раз'
        else:
            break
    yield f'Вы выбрали {action}'
