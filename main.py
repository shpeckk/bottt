import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor

API_TOKEN = '7957692959:AAGYNF8vHZaHanfSIxjc-l3rtxBALhJ6PDE'

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("Заказать кальян"))
    keyboard.add(KeyboardButton("Меню и цены"))
    await message.answer("Привет! Выбери действие:", reply_markup=keyboard)

@dp.message_handler(lambda message: message.text == "Заказать кальян")
async def hookah_order(message: types.Message):
    await message.answer("Введите вкус, крепость (1-5) и номер телефона.")

@dp.message_handler(lambda message: message.text == "Меню и цены")
async def menu(message: types.Message):
    await message.answer("Вот наше меню и цены (тут будет фото или текст).")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
