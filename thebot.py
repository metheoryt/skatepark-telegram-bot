import collections
from functools import wraps
from ctx import populate_context, clear_context
from replies import send_answer
import logging


log = logging.getLogger(__name__)


def begin():
    """Сообщение, которое вернётся пользователю,
    если он введёт любой бред кроме ожидаемого ботом.
    Единственный
    """
    yield "Жми /start для начала диалога"


dialog_registry = collections.defaultdict(begin)
"""Реестр текущих диалогов и их состояний"""


def main_handler(bot, update):
    """Стандартный обработчик всех Update'ов"""
    populate_context(update)  # популяризуем контекст для обработчиков
    chat_id = update.message.chat_id
    if chat_id in dialog_registry:
        # Если чат числится в реестре диалогов, пробуем его продолжить
        try:
            answer = dialog_registry[chat_id].send(update)
            # answer это то что выбрасывает yield
        except TypeError:
            # Диалог ещё не начат, начинаем
            try:
                answer = next(dialog_registry[chat_id])
            except StopIteration:
                # Диалог не yield'нул ничего, начинаем сначала
                del dialog_registry[chat_id]
                return main_handler(bot, update)
        except StopIteration:
            # Если диалог закончился (последний yield отработал),
            # удаляем диалог и запускаем обработчик заново
            # (приветственное сообщение)
            del dialog_registry[chat_id]
            return main_handler(bot, update)
    else:
        # Диалога не было - начинаем его приветственным сообщением
        answer = next(dialog_registry[chat_id])

    send_answer(answer, update, bot)
    # теперь - надо ли чистить контекст?
    # конечно надо - неизвестно, от кого тред получит следующее сообщение
    clear_context(update)


def new_dialog(f):
    """Декоратор, начинающий новый диалог с пользователем.
    Заменяет дефолтный обработчик `begin` на обёрнутый.

    ДЕКОРИРУЕМАЯ ФУНКЦИЯ ДОЛЖНА БЫТЬ ИТЕРАТОРОМ!

    Пример:

        @new_dialog
        def start(update):
            upd = yield 'Привет, как тебя зовут?'
            if upd.message.text == 'Вася Пупкин':
                yield from personal_greet('Вася')
            else:
                yield 'Извини, я тебя не знаю'

        def personal_greet(person_name):
            yield f'Привет, {person_name}!'
    """
    @wraps(f)
    def wrapped_handler(bot, update):
        dialog_registry[update.message.chat_id] = f(update)
        # Сохраняем итератор в реестре
        # и вызываем стандартную обработку update
        return main_handler(bot, update)
    return wrapped_handler


def private_only(f):
    """Декоратор, запрещающий диалог вне приватных чатов"""
    @wraps(f)
    def wrapper(bot, update):
        if update.message.chat.type != 'private':
            return bot.sendMessage(chat_id=update.message.chat_id, text='Простите, обратитесь ко мне лично')
        else:
            return f(bot, update)

    return wrapper
