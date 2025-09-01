from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def go_back_markup(text: str, callback_target: str):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton(text, callback_data=callback_target))
    return markup

def safe_edit_message(bot, chat_id, message_id, text, reply_markup):
    if not text or not str(text).strip():
        text = "⚠️ No data available."
    try:
        return bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=reply_markup)
    except Exception as e:
        msg_error = str(e).lower()
        if ("message to edit not found" in msg_error or
            "message can't be edited" in msg_error or
            "message is not modified" in msg_error):
            return bot.send_message(chat_id, text, reply_markup=reply_markup)
        raise