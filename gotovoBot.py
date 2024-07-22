-*- coding: utf-8 -*-
import telebot
from telebot import types
import sqlite3

TOKEN = '6884763965:AAGaNLTZh0DlBJ3jVUiX9pv5RqwDmebGMbU'
bot = telebot.TeleBot(TOKEN)

conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()

questions = [
    "Ваш никнейм в Майнкрафте?",
    "Ваш возраст?",
    "Как вы узнали о нашем сервере?",
    "Как вы относитесь к читам и играли ли вы раньше с ними?",
    "Какие виды деятельности в Майнкрафте вам нравятся больше всего (например, строительство, майнинг, PvP, фермерство и т.д.)?",
    "Были ли у вас какие-либо негативные инциденты на других серверах? Если да, то опишите их.",
    "Как вы относитесь к правилам и готовы ли вы их соблюдать?",
    "Что вы будете делать, если обнаружите нарушения правил другим игроком?",
    "Вы когда-нибудь использовали твинк аккаунты или собираетесь это делать?",
    "Знаете ли вы, что на нашем сервере запрещены дюпы и лаг машины? Как вы к этому относитесь?",
    "Напишите, что вы понимаете под понятием приват территории и как собираетесь его организовывать на сервере?",
    "О себе:\nПожалуйста, расскажите немного о себе, ваших интересах, опыте игры в Майнкрафт и почему вы хотите присоединиться к нашему среверу?"
]

user_state = {}

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton(text="Подать заявку!", callback_data="start_application")
    markup.add(btn)
    bot.send_message(message.chat.id, "*Здравствуйте! Я - SkyBot!*\nЯ помогу тебе попасть на майнкрафт сервер SkyWorld! Нужно будет подать простую заявку на сервер. Нажимай на кнопку \"Подать заявку!\"", parse_mode='Markdown', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "start_application":
        user_id = call.from_user.id
        username = call.from_user.username or "Unknown"
        cursor.execute("SELECT * FROM Users WHERE User = ?", (username,))
        if cursor.fetchone() is None:
            cursor.execute("INSERT INTO Users (User) VALUES (?)", (username,))
        else:
            cursor.execute("UPDATE Users SET Question1 = NULL, Question2 = NULL, Question3 = NULL, Question4 = NULL, Question5 = NULL, Question6 = NULL, Question7 = NULL, Question8 = NULL, Question9 = NULL, Question10 = NULL, Question11 = NULL, Question12 = NULL, Verdict = NULL WHERE User = ?", (username,))
        conn.commit()
        user_state[user_id] = {"step": 0, "answers": [], "username": username}
        ask_question(call.message)
    elif call.data == "submit_application":
        user_id = call.from_user.id
        if check_subscription(user_id):
            bot.send_message(call.message.chat.id, "**Заявка успешно отправлена!**\nОжидайте ответа, обычно это не занимает дольше 24 часов.\nОтвет придёт сюда, по этому не удаляйте/не блокируете бота и телеграмм канал, иначе ответ может не прийти или прийти не корректно.", parse_mode='Markdown')
            send_application_to_admin(user_id)
        else:
            markup = types.InlineKeyboardMarkup()
            btn_subscribe = types.InlineKeyboardButton(text="Подписаться!", url="https://t.me/SkyWorldServer")
            btn_check = types.InlineKeyboardButton(text="Проверить подписку", callback_data="check_subscription")
            markup.add(btn_subscribe, btn_check)
            bot.send_message(call.message.chat.id, "Для отправки заявки на сервер вы должны подписаться на наш телеграмм канал. Там выкладываются все самые важные новости про сервер, а также так вы не потеряете нас!", reply_markup=markup)
    elif call.data == "check_subscription":
        user_id = call.from_user.id
        if check_subscription(user_id):
            bot.send_message(call.message.chat.id, "**Заявка успешно отправлена!**\nОжидайте ответа, обычно это не занимает дольше 24 часов.\nОтвет придёт сюда, по этому не удаляйте/не блокируете бота и телеграмм канал, иначе ответ может не прийти или прийти не корректно.", parse_mode='Markdown')
            send_application_to_admin(user_id)
        else:
            bot.send_message(call.message.chat.id, "Вы всё ещё не подписаны на наш телеграмм канал. Пожалуйста, подпишитесь для отправки заявки.")
    elif call.data.startswith("accept_") or call.data.startswith("reject_"):
        handle_admin_action(call)

def ask_question(message):
    user_id = message.chat.id
    step = user_state[user_id]["step"]
    if step < len(questions):
        bot.send_message(user_id, "**{} вопрос:**\n{}\n\nОтправьте одним сообщением без фото/стикеров/емодзи и т.п. ответ на этот вопрос".format(step + 1, questions[step]), parse_mode='Markdown')
    else:
        show_summary(user_id)

def show_summary(user_id):
    answers = user_state[user_id]["answers"]
    summary = "\n".join(["{}. {}".format(i + 1, answer) for i, answer in enumerate(answers)])
    bot.send_message(user_id, "Поздравляю, вы ответили на все вопросы!\n\nВот ваши ответы:\n{}\n\nХотите отправить заявку на проверку, или хотите переписать её заново?".format(summary), parse_mode='Markdown')
    markup = types.InlineKeyboardMarkup()
    btn_submit = types.InlineKeyboardButton(text="Отправить!", callback_data="submit_application")
    btn_rewrite = types.InlineKeyboardButton(text="Переписать!", callback_data="start_application")
    markup.add(btn_submit, btn_rewrite)
    bot.send_message(user_id, "Пожалуйста, выберите действие:", reply_markup=markup)

def check_subscription(user_id):
    member = bot.get_chat_member(chat_id="-1002141926321", user_id=user_id)
    return member.status in ['member', 'administrator', 'creator']

def send_application_to_admin(user_id):
    answers = user_state[user_id]["answers"]
    username = user_state[user_id]["username"]
    summary = "\n".join(["{}. {}".format(i + 1, answer) for i, answer in enumerate(answers)])
    admin_id = 5125745037  # Замените на ваш ID
    markup = types.InlineKeyboardMarkup()
    btn_accept = types.InlineKeyboardButton(text="Принят", callback_data="accept_{}".format(user_id))
    btn_reject = types.InlineKeyboardButton(text="Отклонён", callback_data="reject_{}".format(user_id))
    markup.add(btn_accept, btn_reject)
    bot.send_message(admin_id, "Новая заявка от @{}\n\n{}".format(username, summary), reply_markup=markup)

@bot.message_handler(func=lambda message: message.chat.id in user_state and user_state[message.chat.id]["step"] < len(questions))
def handle_answer(message):
    user_id = message.chat.id
    step = user_state[user_id]["step"]
    user_state[user_id]["answers"].append(message.text)
    username = user_state[user_id]["username"]
    cursor.execute("UPDATE Users SET Question{} = ? WHERE User = ?".format(step + 1), (message.text, username))
    conn.commit()
    user_state[user_id]["step"] += 1
    ask_question(message)

def handle_admin_action(call):
    user_id = int(call.data.split("_")[1])
    username = user_state[user_id]["username"]
    if call.data.startswith("accept_"):
        bot.send_message(user_id, "*Поздравляем! Вы приняты на сервер!*\nIP сервера - skyworld.mcmem.ru\nДискорд сервер - https://discord.gg/j3dmzCwdjJ", parse_mode='Markdown')
        cursor.execute("UPDATE Users SET Verdict = ? WHERE User = ?", ("принят", username))
        conn.commit()
    elif call.data.startswith("reject_"):
        bot.send_message(call.message.chat.id, "Пожалуйста, укажите причину отклонения:")
        bot.register_next_step_handler(call.message, get_rejection_reason, user_id)

def get_rejection_reason(message, user_id):
    reason = message.text
    username = user_state[user_id]["username"]
    bot.send_message(user_id, "*Здравствуйте, к сожалению вы не приняты :(*\n\nПричина отклонения: {}".format(reason), parse_mode='Markdown')
    cursor.execute("UPDATE Users SET Verdict = ? WHERE User = ?", (reason, username))
    conn.commit()
