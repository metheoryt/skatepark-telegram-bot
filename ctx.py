import threading

from sqlalchemy.orm.exc import NoResultFound

from db.models import Client


class CTX(threading.local):
    """Thread-safe контекст, заполняющийся перед вызовом любого Update handler"""
    def __init__(self):
        self.client = None
        """
        Клиент, от которого пришёл запрос.
        None, если его ещё нет в базе
        :type: Client | None"""


x = CTX()


def populate_context(update):
    """Популяризует контекст данными на основе входящего апдейта"""
    chat_id = update.message.chat.id
    try:
        x.client = Client.q.filter(Client.tg_id == chat_id).one()
    except NoResultFound:
        pass


def clear_context(update):
    x.client = None
