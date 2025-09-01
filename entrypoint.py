import os
import dotenv
from flask import Flask, request
from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flows import handle_cards_callback, handle_subscriptions_callback
from utils.ui import safe_edit_message

dotenv.load_dotenv()

TOKEN = os.environ.get("TOKEN")
bot = TeleBot(TOKEN, parse_mode="HTML")
app = Flask(__name__)

# Comandos
@bot.message_handler(commands=["start"])
def start(message):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton(text="Cards", callback_data="cards:menu_cards"),
        InlineKeyboardButton(text="Subscriptions", callback_data="subs:menu_subscriptions")
    )
    safe_edit_message(
        bot, chat_id=message.chat.id, message_id=message.id,
        text="What would you like to do?", reply_markup=markup
    )

# Callback handler
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

# Endpoint webhook do Telegram
@app.route("/", methods=["POST"])
def webhook():
    update = request.get_json(force=True)
    bot.process_new_updates([bot.types.Update.de_json(update)])
    return "OK"

# Endpoint de teste
@app.route("/", methods=["GET"])
def index():
    return "Bot Telegram ativo!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
