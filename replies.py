import telegram
from telegram import Bot, Update
from telegram import KeyboardButton as Btn, ReplyKeyboardMarkup as Kbd


class Reply:

    def __init__(self,
                 text: str=None,
                 parse_mode: telegram.ParseMode=None,
                 reply_markup: telegram.ReplyKeyboardMarkup=None,
                 remove_kb: bool=False
                 ):
        self.text = text
        self.parse_mode = parse_mode
        self.reply_markup = reply_markup
        if remove_kb:
            self.reply_markup = telegram.ReplyKeyboardRemove()


def send_answer(answer, update: Update, bot: Bot):
    """От user-defined обработчиков могут возвращаться различные типы ответов
    Эта функция ответственна за отсылку ответа различных типов"""
    chat_id = update.message.chat_id
    if isinstance(answer, str):
        bot.sendMessage(chat_id=chat_id, text=answer)
    elif isinstance(answer, Reply):
        bot.sendMessage(
            chat_id=chat_id,
            text=answer.text,
            parse_mode=answer.parse_mode,
            reply_markup=answer.reply_markup,
        )
