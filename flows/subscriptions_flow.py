from models import Subscription
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.ui import safe_edit_message, go_back_markup
from utils.state import set_state, get_state, clear_state
from utils.database import list_cards, list_subscriptions, insert_subscription, delete_subscription

def menu_subscriptions(bot, chat_id, message_id):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("Show subscriptions", callback_data="subs:show_all_subscriptions"),
        InlineKeyboardButton("New subscription", callback_data="subs:new_subscription"),
    )
    markup.add(
        InlineKeyboardButton("Delete subscription", callback_data="subs:delete_subscription"),
    )
    markup.add(InlineKeyboardButton("<< Go back", callback_data="start"))
    msg = safe_edit_message(bot, chat_id, message_id, "My subscriptions 🎥", markup)

def show_all_subscriptions(bot, chat_id, message_id):
    subscriptions = list_subscriptions()
    markup = go_back_markup(text="<< Go back", callback_target="subs:menu_subscriptions")

    if not subscriptions:
        msg = safe_edit_message(bot, chat_id, message_id, "No subscriptions found!", markup)
        return

    subscriptions_information = [
        f"<b>Name:</b> {subs.name}\n<b>Payment date:</b> {subs.payment_date}\n<b>Price:</b> {subs.price:.2f}\n"
        for subs in subscriptions
    ]
    msg = safe_edit_message(bot, chat_id, message_id, "\n".join(subscriptions_information), markup)

def cancel_subscription_flow(bot, call):
    user_id = call.from_user.id
    st = get_state(user_id)
    if "last_message_id" == st.last_message_id:
        try:
            bot.delete_message(call.message.chat.id, USER_STATE[user_id]["last_message_id"])
        except Exception:
            pass
    clear_state(user_id)
    menu_subscriptions(bot, call.message.chat.id, call.message.id)

# ======== add subs ========
def start_add_subs_flow(bot, call):
    user_id = call.from_user.id
    set_state(user_id, "ask_name", buffer={})
    markup = go_back_markup(text="Cancel", callback_target="subs:cancel_subscription_flow")
    text = "What is the subscription name? ✍️"
    try:
        msg = bot.edit_message_text(call.message.chat.id, call.message.id, text, markup)
    except Exception:
        msg = bot.send_message(call.message.chat.id, text, reply_markup=markup)
    set_state(user_id, "ask_name", last_message_id=msg.id)
    bot.register_next_step_handler(msg, lambda m: step_subscription_name(bot, m))

def step_subscription_name(bot, message):
    user_id = message.from_user.id
    name = (message.text or "").strip()
    markup = go_back_markup(text="Cancel", callback_target="subs:cancel_subscription_flow")

    if not name:
        msg = bot.reply_to(message, "Invalid name. Please try again:", reply_markup=markup)
        set_state(user_id, "ask_name", last_message_id=msg.id)
        bot.register_next_step_handler(msg, lambda m: step_subscription_name(bot, m))
        return

    st = get_state(user_id)
    st.buffer["name"] = name
    set_state(user_id, "ask_description", buffer=st.buffer)
    msg = bot.reply_to(message, "What is the description?", reply_markup=markup)
    set_state(user_id, "ask_description", last_message_id=msg.id)
    bot.register_next_step_handler(msg, lambda m: step_subscription_description(bot, m))

def step_subscription_description(bot, message):
    user_id = message.from_user.id
    description = (message.text or "").strip()
    markup = go_back_markup(text="Cancel", callback_target="subs:cancel_subscription_flow")

    if not description:
        msg = bot.reply_to(message, "Invalid description. Please try again:", reply_markup=markup)
        set_state(user_id, "ask_description", last_message_id=msg.id)
        bot.register_next_step_handler(msg, lambda m: step_subscription_description(bot, m))
        return

    st = get_state(user_id)
    st.buffer["description"] = description
    set_state(user_id, "ask_payment_date", buffer=st.buffer)
    msg = bot.reply_to(message, "Payment date (1-31)? 📅", reply_markup=markup)
    set_state(user_id, "ask_payment_date", last_message_id=msg.id)
    bot.register_next_step_handler(msg, lambda m: step_payment_date(bot, m))

def step_payment_date(bot, message):
    user_id = message.from_user.id
    markup = go_back_markup(text="Cancel", callback_target="subs:cancel_subscription_flow")

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
    set_state(user_id, "ask_price", buffer=st.buffer)

    msg = bot.reply_to(message, "What is the subscription price? 💲", reply_markup=markup)
    set_state(user_id, "ask_price", last_message_id=msg.id)
    bot.register_next_step_handler(msg, lambda m: step_subscription_price(bot, m))

def step_subscription_price(bot, message):
    user_id = message.from_user.id
    markup = go_back_markup(text="Cancel", callback_target="subs:cancel_subscription_flow")

    try:
        price = float((message.text or "").replace(",", ".").strip())
        if price < 0:
            raise ValueError
    except Exception:
        msg = bot.reply_to(message, "Invalid price. Enter a positive number:", reply_markup=markup)
        set_state(user_id, "ask_price", last_message_id=msg.id)
        bot.register_next_step_handler(msg, lambda m: step_subscription_price(bot, m))
        return

    st = get_state(user_id)
    st.buffer["price"] = price
    set_state(user_id, "ask_link_card", buffer=st.buffer)

    cards = list_cards()
    cards_position = {index + 1: card.uuid for index, card in enumerate(cards)}
    last_position = len(cards) + 1

    text = "Link with a card? 💳\n"
    if cards:
        text += "\n".join(f"{i+1} - {c.name}" for i, c in enumerate(cards))
    else:
        text += "No cards found.\n"
    text += f"{last_position} - No"

    msg = bot.reply_to(message, text, reply_markup=markup)
    set_state(user_id, "ask_link_card", last_message_id=msg.id)
    bot.register_next_step_handler(msg, lambda m: step_link_card(bot, m, cards_position, last_position))

def step_link_card(bot, message, cards_position, last_position):
    user_id = message.from_user.id
    markup = go_back_markup(text="Cancel", callback_target="subs:cancel_subscription_flow")

    try:
        selected = int(message.text)
        if selected > last_position or selected < 1:
            raise ValueError
        card_id = None if selected == last_position else cards_position[selected]
    except Exception:
        msg = bot.reply_to(message, f"Invalid option. Enter a number between 1 and {last_position}:", reply_markup=markup)
        set_state(user_id, "ask_link_card", last_message_id=msg.id)
        bot.register_next_step_handler(msg, lambda m: step_link_card(bot, m, cards_position, last_position))
        return

    st = get_state(user_id)
    st.buffer["card_id"] = card_id

    try:
        insert_subscription(Subscription(**st.buffer))
        list_subscriptions.cache_clear()
    except Exception as error:
        bot.reply_to(message, f"Failed to insert subscription data. Reason: {error}")
        return

    bot.send_message(
        message.chat.id,
        f"Subscription added ✅\n<b>Name:</b> {st.buffer['name']}"
        f"\n<b>Description:</b> {st.buffer['description']}"
        f"\n<b>Payment date:</b> {st.buffer['payment_date']}"
        f"\n<b>Price:</b> {st.buffer['price']:.2f}",
        reply_markup=go_back_markup("<< Go back", "subs:menu_subscriptions")
    )
    clear_state(user_id)
# ======== delete subs ========
def start_del_subs_flow(bot, call):
    user_id = call.from_user.id
    set_state(user_id, "delete_subs", buffer={})
    markup = go_back_markup(text="Cancel", callback_target="subs:cancel_subscription_flow")

    subscriptions = list_subscriptions()
    if not subscriptions:
        msg = safe_edit_message(call.message.chat.id, call.message.id, "No subscriptions found!", markup)
        return

    subscriptions_position = {index + 1: subs.uuid for index, subs in enumerate(subscriptions)}
    text = "Select the subscription to delete:\n" + "\n".join(f"{i + 1} - {c.name}" for i, c in enumerate(subscriptions))
    try:
        msg = safe_edit_message(call.message.chat.id, call.message.id, text, markup)
    except Exception:
        msg = bot.send_message(call.message.chat.id, text, reply_markup=markup)
    set_state(user_id, "delete_subs", last_message_id=msg.id)
    bot.register_next_step_handler(msg, lambda m: step_delete_select(bot, m, user_id, subscriptions_position))

def step_delete_select(bot, message, user_id, subscriptions_position):
    markup = go_back_markup(text="Cancel", callback_target="subs:cancel_subscription_flow")
    user_input = (message.text or "").strip()
    try:
        idx = int(user_input)
        if idx not in subscriptions_position:
            raise ValueError
        card_uuid = subscriptions_position[idx]
    except Exception:
        msg = bot.reply_to(message, "Invalid option. Please try again:", reply_markup=markup)
        set_state(user_id, "delete_select", last_message_id=msg.id)
        bot.register_next_step_handler(msg, lambda m: step_delete_select(bot, m, user_id, subscriptions_position))
        return

    try:
        delete_subscription(card_uuid)
        list_subscriptions.cache_clear()
    except Exception as error:
        bot.reply_to(message, "Failed to delete subscription. Reason: {}".format(error), )
        return

    bot.send_message(message.chat.id, f"Subscription deleted successfully ✅",
                     reply_markup=go_back_markup("<< Go back", "subs:menu_subscriptions"))
    clear_state(user_id)
# =============================
def handle_subscriptions_callback(bot, call):
    if call.data == "subs:menu_subscriptions":
        return menu_subscriptions(bot, call.message.chat.id, call.message.id)
    if call.data == "subs:show_all_subscriptions":
        return show_all_subscriptions(bot, call.message.chat.id, call.message.id)
    if call.data == "subs:new_subscription":
        return start_add_subs_flow(bot, call)
    if call.data == "subs:delete_subscription":
        return start_del_subs_flow(bot, call)
    if call.data.startswith("subs:confirm_delete:"):
        delete_subscription(call)
    if call.data == "subs:cancel_subscription_flow":
        return cancel_subscription_flow(bot, call)