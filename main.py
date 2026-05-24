import asyncio
import logging
from datetime import datetime, timedelta
import sqlite3

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    Message, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    PreCheckoutQuery, 
    LabeledPrice, 
    ContentType
)

# --- КОНФИГУРАЦИЯ ---
BOT_TOKEN = "8805662504:AAGc1gByo0xNpK3hUlBiXppN14g25PzC_t8"
ADMIN_IDS = [8624430245]  # ЗАМЕНИ СВОИМ ТЕЛЕГРАМ ID ДЛЯ АДМИН-ПАНЕЛИ

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- РАБОТА С БАЗОЙ ДАННЫХ ---
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            sub_expiry TEXT,
            is_whitelist INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def get_user(user_id, username=None):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username, sub_expiry, is_whitelist FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    
    if not user and username is not None:
        cursor.execute("INSERT INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
        conn.commit()
        cursor.execute("SELECT user_id, username, sub_expiry, is_whitelist FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
        
    conn.close()
    return user

def update_sub(user_id_or_username, days, action="give"):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    # Проверяем, передан ID или username
    if isinstance(user_id_or_username, int) or user_id_or_username.isdigit():
        sql_where = "user_id = ?"
        param = int(user_id_or_username)
    else:
        sql_where = "username = ?"
        param = user_id_or_username.replace("@", "")

    if action == "give":
        expiry_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(f"UPDATE users SET sub_expiry = ? WHERE {sql_where}", (expiry_date, param))
    else:
        cursor.execute(f"UPDATE users SET sub_expiry = NULL WHERE {sql_where}", (param,))
        
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    return success

# --- ХЕНДЛЕРЫ КОМАНД ---

@dp.message(Command("start"))
async def cmd_start(message: Message):
    get_user(message.from_user.id, message.from_user.username)
    
    # Инлайн клавиатура с Mini App и переходом в /main
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📱 Открыть Mini App", web_app={"url": "https://your-miniapp-url.com"})], # Замени на свой URL
    ])
    
    await message.answer(
        "Привет! Сн#сти можно либо в Mini App либо в своем боте. "
        "Чтобы продолжить с ботом напишите: /main.",
        reply_markup=kb
    )

@dp.message(Command("main"))
async def cmd_main(message: Message):
    get_user(message.from_user.id, message.from_user.username)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💥 Уничтожитель", callback_query_data="menu_destroy")],
        [InlineKeyboardButton(text="💎 Оформить подписку", callback_query_data="menu_subscribe")],
        [InlineKeyboardButton(text="👤 Профиль", callback_query_data="menu_profile")],
        [InlineKeyboardButton(text="ℹ️ О нас", callback_query_data="menu_about")]
    ])
    
    await message.answer(
        "Здравствуйте! Это уничтожитель Telegram аккаунтов, чатов, ботов и т.д\n"
        "Выберите интересующий пункт меню ниже:",
        reply_markup=kb
    )

# --- ОБРАБОТКА МЕНЮ ---

@dp.callback_query(F.data == "menu_profile")
async def cb_profile(callback: Message):
    user = get_user(callback.from_user.id, callback.from_user.username)
    username = f"@{user[1]}" if user[1] else "Не установлен"
    
    # Расчет дней подписки
    sub_text = "Отсутствует 🚫"
    if user[2]:
        expiry = datetime.strptime(user[2], "%Y-%m-%d %H:%M:%S")
        if expiry > datetime.now():
            days_left = (expiry - datetime.now()).days
            sub_text = f"Активна (Осталось дней: {days_left})"
        else:
            sub_text = "Истекла ❌"

    wl_text = "🛡 Включен (Вас нельзя снести)" if user[3] == 1 else "❌ Выключен"

    text = (
        f"👤 *Ваш профиль:*\n\n"
        f" ID: `{callback.from_user.id}`\n"
        f" Юзернейм: {username}\n"
        f" Подписка: {sub_text}\n"
        f" White List: {wl_text}"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_query_data="back_to_main")]
    ])
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)

@dp.callback_query(F.data == "menu_about")
async def cb_about(callback: Message):
    text = (
        "ℹ️ *О нас*\n\n"
        "Самый мощный инструмент для очистки и деструктуризации сущностей Telegram.\n"
        "Быстрая работа через сессии, обход ограничений."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_query_data="back_to_main")]
    ])
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)

@dp.callback_query(F.data == "back_to_main")
async def cb_back(callback: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💥 Уничтожитель", callback_query_data="menu_destroy")],
        [InlineKeyboardButton(text="💎 Оформить подписку", callback_query_data="menu_subscribe")],
        [InlineKeyboardButton(text="👤 Профиль", callback_query_data="menu_profile")],
        [InlineKeyboardButton(text="ℹ️ О нас", callback_query_data="menu_about")]
    ])
    await callback.message.edit_text(
        "Здравствуйте! Это уничтожитель Telegram аккаунтов, чатов, ботов и т.д", 
        reply_markup=kb
    )

# --- ПЛАТЕЖНАЯ СИСТЕМА (TELEGRAM STARS) ---

@dp.callback_query(F.data == "menu_subscribe")
async def cb_subscribe(callback: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="10 дней — 50 Stars 🌟", callback_query_data="buy_10")],
        [InlineKeyboardButton(text="30 дней — 130 Stars 🌟", callback_query_data="buy_30")],
        [InlineKeyboardButton(text="50 дней — 200 Stars 🌟", callback_query_data="buy_50")],
        [InlineKeyboardButton(text="🔥 Получить скидку", url="https://t.me/moresocean")],
        [InlineKeyboardButton(text="🔙 Назад", callback_query_data="back_to_main")]
    ])
    await callback.message.edit_text("💎 *Выбор тарифа подписки:*", parse_mode="Markdown", reply_markup=kb)

@dp.callback_query(F.data.startswith("buy_"))
async def send_invoice(callback: Message):
    plan = callback.data.split("_")[1]
    
    prices = {
        "10": (50, "Подписка на 10 дней"),
        "30": (130, "Подписка на 30 дней"),
        "50": (200, "Подписка на 50 дней")
    }
    
    stars, description = prices[plan]
    
    await callback.message.answer_invoice(
        title="Оформление подписки Snoser",
        description=description,
        payload=f"sub_{plan}",
        provider_token="", # Для Telegram Stars оставляется пустым
        currency="XTR",
        prices=[LabeledPrice(label=description, amount=stars)]
    )
    await callback.answer()

@dp.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)

@dp.message(F.content_type == ContentType.SUCCESSFUL_PAYMENT)
async def success_payment_handler(message: Message):
    payload = message.successful_payment.invoice_payload
    days = int(payload.split("_")[1])
    
    update_sub(message.from_user.id, days, action="give")
    
    await message.answer("✅ Подписка успешно оформлена! Напишите /main для продолжения.")

# --- АДМИН-ПАНЕЛЬ (УПРАВЛЕНИЕ ЧЕРЕЗ КОМАНДЫ) ---

@dp.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    text = (
        "⚙️ *Административная панель:*\n\n"
        "Выдать подписку:\n"
        "`/givesub [ID или Юзернейм] [кол-во дней]`\n\n"
        "Забрать подписку:\n"
        "`/removesub [ID или Юзернейм]`"
    )
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("givesub"))
async def admin_give_sub(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    try:
        args = message.text.split()
        target = args[1]
        days = int(args[2])
        
        if update_sub(target, days, "give"):
            await message.answer(f"✅ Подписка для {target} успешно выдана на {days} дней.")
        else:
            await message.answer("❌ Пользователь не найден в базе данных.")
    except Exception:
        await message.answer("⚠️ Ошибка. Пример: `/givesub @username 30` или `/givesub 12345678 10`")

@dp.message(Command("removesub"))
async def admin_remove_sub(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
        
    try:
        args = message.text.split()
        target = args[1]
        
        if update_sub(target, 0, "remove"):
            await message.answer(f"❌ Подписка для {target} аннулирована.")
        else:
            await message.answer("❌ Пользователь не найден в базе данных.")
    except Exception:
        await message.answer("⚠️ Ошибка. Пример: `/removesub @username` или `/removesub 12345678`")

# --- ЗАПУСК БОТА ---
async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
