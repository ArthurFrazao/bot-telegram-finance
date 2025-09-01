from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.ui import safe_edit_message, go_back_markup
from utils.state import set_state, get_state, clear_state
from utils.database import list_cards, insert_card, delete_card
from models import Card

def menu_cards(bot, chat_id, message_id):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("Show cards", callback_data="cards:show_all_cards"),
        InlineKeyboardButton("New card", callback_data="cards:new_card"),
    )
    markup.add(
        InlineKeyboardButton("Delete card", callback_data="cards:delete_card"),
    )
    markup.add(InlineKeyboardButton("<< Go back", callback_data="start"))
    msg = safe_edit_message(bot, chat_id, message_id, "My cards 💳", markup)

def show_all_cards(bot, chat_id, message_id):
    cards = list_cards()
    markup = go_back_markup(text="<< Go back", callback_target="cards:menu_cards")

    if not cards:
        msg = safe_edit_message(bot, chat_id, message_id, "No cards found!", markup)
        return

    cards_information = [
        f"<b>Name:</b> {card.name}\n<b>Payment date:</b> {card.payment_date}\n<b>Total limit:</b> {card.total_limit:.2f}\n"
        for card in cards
    ]
    msg = safe_edit_message(bot, chat_id, message_id, "\n".join(cards_information), markup)

def cancel_card_flow(bot, call):
    user_id = call.from_user.id
    st = get_state(user_id)
    if "last_message_id" == st.last_message_id:
        try:
            bot.delete_message(call.message.chat.id, USER_STATE[user_id]["last_message_id"])
        except Exception:
            pass
    clear_state(user_id)
    menu_cards(bot, call.message.chat.id, call.message.id)

# ======== add card ========
def start_add_card_flow(bot, call):
    user_id = call.from_user.id
    set_state(user_id, "ask_name", buffer={})
    markup = go_back_markup(text="Cancel", callback_target="cards:cancel_card_flow")
    text = "What is the card name? ✍️"
    try:
        msg = bot.edit_message_text(call.message.chat.id, call.message.id, text, markup)
    except Exception:
        msg = bot.send_message(call.message.chat.id, text, reply_markup=markup)
    set_state(user_id, "ask_name", last_message_id=msg.id)
    bot.register_next_step_handler(msg, lambda m: step_card_name(bot, m))

def step_card_name(bot, message):
    user_id = message.from_user.id
    name = (message.text or "").strip()
    markup = go_back_markup(text="Cancel", callback_target="cards:cancel_card_flow")

    if not name:
        msg = bot.reply_to(message, "Invalid name. Please try again:", reply_markup=markup)
        set_state(user_id, "ask_name", last_message_id=msg.id)
        bot.register_next_step_handler(msg, lambda m: step_card_name(bot, m))
        return

    st = get_state(user_id)
    st.buffer["name"] = name
    set_state(user_id, "ask_payment_date", buffer=st.buffer)
    msg = bot.reply_to(message, "Payment date (1-31)? 📅", reply_markup=markup)
    set_state(user_id, "ask_payment_date", last_message_id=msg.id)
    bot.register_next_step_handler(msg, lambda m: step_payment_date(bot, m))

def step_payment_date(bot, message):
    user_id = message.from_user.id
    markup = go_back_markup(text="Cancel", callback_target="cards:cancel_card_flow")
    try:
        payment_date = int((message.text or "").strip())
        if not (1 <= payment_date <= 31):
            raise ValueError
    except Exception:
        msg = bot.reply_to(message, "Invalid value. Enter a number between 1 and 31:", reply_markup=markup)
        set_state(user_id, "ask_payment_date", last_message_id=msg.id)
        bot.register_next_step_handler(msg, lambda m: step_payment_date(bot, m))
        return

    st = get_state(user_id)
    st.buffer["payment_date"] = payment_date
    set_state(user_id, "ask_total_limit", buffer=st.buffer)
    msg = bot.reply_to(message, "Total limit (e.g., 2500.00)? 📊", reply_markup=markup)
    set_state(user_id, "ask_total_limit", last_message_id=msg.id)
    bot.register_next_step_handler(msg, lambda m: step_total_limit(bot, m))

def step_total_limit(bot, message):
    user_id = message.from_user.id
    markup = go_back_markup(text="Cancel", callback_target="cards:cancel_card_flow")
    try:
        total_limit = float((message.text or "").replace(",", ".").strip())
        if total_limit <= 0:
            raise ValueError
    except Exception:
        msg = bot.reply_to(message, "Invalid limit. Enter a number greater than 0 (e.g., 2500.00):", reply_markup=markup)
        set_state(user_id, "ask_total_limit", last_message_id=msg.id)
        bot.register_next_step_handler(msg, lambda m: step_total_limit(bot, m))
        return

    st = get_state(user_id)
    st.buffer["total_limit"] = total_limit

    try:
        insert_card(Card(**st.buffer))
        list_cards.cache_clear()
    except Exception as error:
        bot.reply_to(message, "Failed to insert card data. Reason: {}".format(error), )
        return

    bot.send_message(message.chat.id, f"Card added ✅\n<b>Name:</b> {st.buffer['name']}\n<b>Payment date:</b> {st.buffer['payment_date']}\n<b>Limit:</b> {st.buffer['total_limit']:.2f}",
                     reply_markup=go_back_markup("<< Go back", "cards:menu_cards"))
    clear_state(user_id)
# ======== delete card ========
def start_del_card_flow(bot, call):
    user_id = call.from_user.id
    set_state(user_id, "delete_card", buffer={})
    markup = go_back_markup(text="Cancel", callback_target="cards:cancel_card_flow")

    cards = list_cards()
    if not cards:
        msg = safe_edit_message(call.message.chat.id, call.message.id, "No cards found!", markup)
        return
    cards_position = {index + 1: card.uuid for index, card in enumerate(cards)}
    text = "Select the card to delete:\n" + "\n".join(f"{i + 1} - {c.name}" for i, c in enumerate(cards))
    try:
        msg = safe_edit_message(call.message.chat.id, call.message.id, text, markup)
    except Exception:
        msg = bot.send_message(call.message.chat.id, text, reply_markup=markup)
    set_state(user_id, "delete_card", last_message_id=msg.id)
    bot.register_next_step_handler(msg, lambda m: step_delete_select(bot, m, user_id, cards_position))

def step_delete_select(bot, message, user_id, cards_position):
    markup = go_back_markup(text="Cancel", callback_target="cards:cancel_card_flow")
    user_input = (message.text or "").strip()
    try:
        idx = int(user_input)
        if idx not in cards_position:
            raise ValueError
        card_uuid = cards_position[idx]
    except Exception:
        msg = bot.reply_to(message, "Invalid option. Please try again:", reply_markup=markup)
        set_state(user_id, "delete_select", last_message_id=msg.id)
        bot.register_next_step_handler(msg, lambda m: step_delete_select(bot, m, user_id, cards_position))
        return

    try:
        delete_card(card_uuid)
        list_cards.cache_clear()
    except Exception as error:
        bot.reply_to(message, "Failed to delete card. Reason: {}".format(error), )
        return

    bot.send_message(message.chat.id, f"Card deleted successfully ✅",
                     reply_markup=go_back_markup("<< Go back", "cards:menu_cards"))
    clear_state(user_id)
# =============================

def handle_cards_callback(bot, call):
    if call.data == "cards:menu_cards":
        return menu_cards(bot, call.message.chat.id, call.message.id)
    if call.data == "cards:show_all_cards":
        return show_all_cards(bot, call.message.chat.id, call.message.id)
    if call.data == "cards:new_card":
        return start_add_card_flow(bot, call)
    if call.data == "cards:delete_card":
        return start_del_card_flow(bot, call)
    if call.data.startswith("cards:confirm_delete:"):
        delete_card(call)
    if call.data == "cards:cancel_card_flow":
        return cancel_card_flow(bot, call)