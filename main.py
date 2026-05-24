import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

# Получаем токен из переменных окружения (который мы добавили в GitHub Secrets)
TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Сюда вставь ссылку на свой проект Vercel, которую получишь после деплоя
WEB_APP_URL = "https://твое-имя.vercel.app" 

def get_main_keyboard():
    """Создает клавиатуру с кнопкой Mini App"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="📱 Открыть Mini App", 
            web_app=WebAppInfo(url=WEB_APP_URL)
        )]
    ])
    return keyboard

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Я Wellon Snoser.\nИспользуй /main, чтобы открыть меню.",
        reply_markup=get_main_keyboard()
    )

@dp.message(Command("main"))
async def cmd_main(message: types.Message):
    await message.answer(
        "Главное меню Wellon Snoser:",
        reply_markup=get_main_keyboard()
    )

# Обработка данных, пришедших из Mini App (когда нажмешь кнопку "Запустить атаку")
@dp.message(F.web_app_data)
async def handle_web_app_data(message: types.Message):
    data = message.web_app_data.data
    await message.answer(f"Получены данные из Mini App: {data}")
    # Сюда можно добавить логику запуска сноса

async def main():
    print("Бот запущен и готов к работе!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
