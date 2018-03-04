from functools import wraps

import telegram

from bot import bot
from db.models import Client


def for_all_admins(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        admins = Client.q.filter(Client.is_admin == True).all()
        for admin in admins:
            f(admin, *args, **kwargs)

    return wrapper


@for_all_admins
def aware_about_new_client(admin: Client, client: Client):
    if admin.subscribed:
        msg = f'У нас новый клиент: `{client.first_name}'
        if client.last_name:
            msg += f' {client.last_name}'
        msg += f'`! Персональный ID `#{client.id}`'
        if client.username:
            msg += f', никнейм в телеге @{client.username}'
        bot.sendMessage(
            chat_id=admin.tg_id,
            text=msg,
            parse_mode=telegram.ParseMode.MARKDOWN
        )
