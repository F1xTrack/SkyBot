# -*- coding: utf-8 -*-
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, CallbackContext
import sqlite3

# Конфигурация бота
TOKEN = '6884763965:AAGaNLTZh0DlBJ3jVUiX9pv5RqwDmebGMbU'
application = Application.builder().token(TOKEN).build()

# Подключение к базе данных
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()

# Вопросы анкеты
questions = [
    "Ваш никнейм в Майнкрафт?",
    "Ваш возраст?",
    "Как вы узнали о нашем сервере?",
    "Как вы относитесь к читам и играли ли вы раньше с ними?",
    "Какие виды деятельности в Майнкрафт вам нравятся больше всего (например, строительство, майнинг, PvP, фермерство и т.д.)?",
    "Были ли у вас какие-либо негативные инциденты на других серверах? Если да, то опишите их.",
    "Как вы относитесь к правилам и готовы ли вы их соблюдать?",
    "Что вы будете делать, если обнаружите нарушения правил другим игроком?",
    "Вы когда-нибудь использовали твинк аккаунты или собираетесь это делать?",
    "Знаете ли вы, что на нашем сервере запрещены дюпы и лаг машины? Как вы к этому относитесь?",
    "Напишите, что вы понимаете под понятием приват территории и как собираетесь его организовывать на сервере?",
    "О себе:\nПожалуйста, расскажите немного о себе, ваших интересах, опыте игры в Майнкрафт и почему вы хотите присоединиться к нашему среверу?"
]

# Хранение состояния пользователей
user_state = {}

async def start(update: Update, context: CallbackContext) -> None:
    keyboard = [[InlineKeyboardButton("Подать заявку!", callback_data='start_application')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "*Здравствуйте! Я - SkyBot!*\nЯ помогу тебе попасть на майнкрафт сервер SkyWorld! Нужно будет подать простую заявку на сервер. Нажимай на кнопку \"Подать заявку!\"",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    username = query.from_user.username or "Unknown"

    if query.data == "start_application":
        cursor.execute("SELECT * FROM Users WHERE User = ?", (username,))
        if cursor.fetchone() is None:
            cursor.execute("INSERT INTO Users (User) VALUES (?)", (username,))
        else:
            cursor.execute("UPDATE Users SET Question1 = NULL, Question2 = NULL, Question3 = NULL, Question4 = NULL, Question5 = NULL, Question6 = NULL, Question7 = NULL, Question8 = NULL, Question9 = NULL, Question10 = NULL, Question11 = NULL, Question12 = NULL, Verdict = NULL WHERE User = ?", (username,))
        conn.commit()
        user_state[user_id] = {"step": 0, "answers": [], "username": username}
        await ask_question(query.message, context)
    elif query.data == "submit_application":
        if await check_subscription(user_id):
            await query.message.reply_text(
                "**Заявка успешно отправлена!**\nОжидайте ответа, обычно это не занимает дольше 24 часов.\nОтвет придёт сюда, по этому не удаляйте/не блокируйте бота и телеграмм канал, иначе ответ может не прийти или прийти не корректно.",
                parse_mode='Markdown'
            )
            await send_application_to_admin(user_id, context)
        else:
            keyboard = [
                [InlineKeyboardButton("Подписаться!", url="https://t.me/SkyWorldServer")],
                [InlineKeyboardButton("Проверить подписку", callback_data="check_subscription")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text(
                "Для отправки заявки на сервер вы должны подписаться на наш телеграмм канал. Там выкладываются все самые важные новости про сервер, а также так вы не потеряете нас!",
                reply_markup=reply_markup
            )
    elif query.data.startswith("accept_") or query.data.startswith("reject_"):
        await handle_admin_action(update, context)

async def ask_question(message, context: CallbackContext) -> None:
    user_id = message.chat_id
    if user_id in user_state:
        step = user_state[user_id]["step"]
        if step < len(questions):
            await context.bot.send_message(
                user_id,
                "**{} вопрос:**\n{}\n\nОтправьте одним сообщением без фото/стикеров/емодзи и т.п. ответ на этот вопрос".format(step + 1, questions[step]),
                parse_mode='Markdown'
            )
        else:
            await show_summary(user_id, context)
    else:
        await context.bot.send_message(user_id, "Произошла ошибка. Попробуйте начать заявку снова.")

async def show_summary(user_id, context: CallbackContext) -> None:
    if user_id in user_state:
        answers = user_state[user_id]["answers"]
        summary = "\n".join(["{}. {}".format(i + 1, answer) for i, answer in enumerate(answers)])
        await context.bot.send_message(
            user_id,
            "Поздравляю, вы ответили на все вопросы!\n\nВот ваши ответы:\n{}\n\nХотите отправить заявку на проверку, или хотите переписать её заново?".format(summary),
            parse_mode='Markdown'
        )
        keyboard = [
            [InlineKeyboardButton("Отправить!", callback_data='submit_application')],
            [InlineKeyboardButton("Переписать!", callback_data='start_application')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(user_id, "Пожалуйста, выберите действие:", reply_markup=reply_markup)
    else:
        await context.bot.send_message(user_id, "Произошла ошибка. Попробуйте начать заявку снова.")

async def check_subscription(user_id) -> bool:
    try:
        member = await application.bot.get_chat_member(chat_id="-1002141926321", user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception:
        return False

async def send_application_to_admin(user_id, context: CallbackContext) -> None:
    if user_id in user_state:
        answers = user_state[user_id]["answers"]
        username = user_state[user_id]["username"]
        summary = "\n".join(["{}. {}".format(i + 1, answer) for i, answer in enumerate(answers)])
        admin_id = 5125745037  # Замените на ваш ID администратора
        keyboard = [
            [InlineKeyboardButton("Принят", callback_data=f"accept_{user_id}")],
            [InlineKeyboardButton("Отклонён", callback_data=f"reject_{user_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(admin_id, f"Новая заявка от @{username}\n\n{summary}", reply_markup=reply_markup)
    else:
        await context.bot.send_message(user_id, "Произошла ошибка. Попробуйте начать заявку снова.")

async def handle_answer(update: Update, context: CallbackContext) -> None:
    user_id = update.message.chat_id
    if user_id in user_state:
        step = user_state[user_id]["step"]
        user_state[user_id]["answers"].append(update.message.text)
        username = user_state[user_id]["username"]
        cursor.execute("UPDATE Users SET Question{} = ? WHERE User = ?".format(step + 1), (update.message.text, username))
        conn.commit()
        user_state[user_id]["step"] += 1
        await ask_question(update.message, context)
    else:
        await context.bot.send_message(user_id, "Произошла ошибка. Попробуйте начать заявку снова.")

async def handle_admin_action(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    user_id = int(query.data.split("_")[1])
    username = user_state[user_id]["username"] if user_id in user_state else "Unknown"
    
    if query.data.startswith("accept_"):
        await context.bot.send_message(
            user_id,
            "*Поздравляем! Вы приняты на сервер!*\nIP сервера - skyworld.mcmem.ru\nДискорд сервер - https://discord.gg/j3dmzCwdjJ",
            parse_mode='Markdown'
        )
        cursor.execute("UPDATE Users SET Verdict = ? WHERE User = ?", ("принят", username))
        conn.commit()
    elif query.data.startswith("reject_"):
        await context.bot.send_message(
            user_id,
            "*Здравствуйте, к сожалению вы не приняты :(*\n\nПричина отклонения: Ваша заявка была отклонена.",
            parse_mode='Markdown'
        )
        cursor.execute("UPDATE Users SET Verdict = ? WHERE User = ?", ("отклонён", username))
        conn.commit()

def main() -> None:
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer))
    application.run_polling()

if __name__ == '__main__':
    main()
