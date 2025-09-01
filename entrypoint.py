import os
import dotenv
from utils.ui import safe_edit_message
from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flows import handle_cards_callback, handle_subscriptions_callback
dotenv.load_dotenv()

TOKEN = os.getenv("TOKEN")
bot = TeleBot(TOKEN, parse_mode="HTML")

@bot.message_handler(commands=["start"])
def start(message):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton(text="Cards", callback_data="cards:menu_cards"),
        InlineKeyboardButton(text="Subscriptions", callback_data="subs:menu_subscriptions")
    )
    safe_edit_message(bot, chat_id=message.chat.id, message_id=message.id, text="What would you like to do?",
                      reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_router(call):
    if call.data.startswith("cards:"):
        handle_cards_callback(bot, call)
        return

    if call.data.startswith("start"):
        start(call.message)
        return

    if call.data.startswith("subs:"):
        handle_subscriptions_callback(bot, call)
        return

if __name__ == "__main__":
    print("Bot running... Press Ctrl+C to exit.")
    bot.infinity_polling()