from enum import Enum
from ctx import x
from replies import Reply
from telegram import KeyboardButton as Btn, ReplyKeyboardMarkup as Kbd


class RideVariant(Enum):
    HOURLY = 'Почасовой'
    DAILY = 'На весь день'
    BY_AMOUNT = 'На всю сумму'


def ride_hourly():
    u = yield 'На сколько часов?'
    while True:
        if u.message.text.isdigit() and 1 < int(u.message.text) < 11:
            break
        else:
            u = yield 'Неправильный ответ, ещё разок'
    hours = int(u.message.text)


def ride():
    u = yield Reply(
        'Какой вариант вам подходит?',
        reply_markup=Kbd(
            [
                [Btn(RideVariant.HOURLY.value), Btn(RideVariant.DAILY.value)],
                [Btn(RideVariant.BY_AMOUNT.value)]
            ],
            one_time_keyboard=True,
            resize_keyboard=True
        )
    )



