from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import os

API_TOKEN = os.getenv("BOT_TOKEN")
STAFF_CHAT_ID = os.getenv("BOT_STAFF_CHAT_ID")  # Например: -100123456789

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# Состояния FSM
class OrderHookah(StatesGroup):
    strength = State()
    flavors = State()
    additive = State()
    phone = State()
    comment = State()
    confirm = State()

# Главное меню
@dp.message_handler(commands=['start'], state='*')
async def start_menu(message: types.Message, state: FSMContext):
    await state.finish()
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Заказать кальян", "Меню")
    await message.answer("Добро пожаловать! Выберите действие:", reply_markup=keyboard)

# Начало заказа
@dp.message_handler(lambda m: m.text == "Заказать кальян", state='*')
async def order_start(message: types.Message, state: FSMContext):
    await state.update_data(price=3000, bowl="Кальян на чаше")
    await OrderHookah.strength.set()
    cancel_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    cancel_kb.add("Отмена")
    await message.answer("Выберите крепость кальяна от 1 до 10 (можно диапазон, например: 6-7, 8-10):", reply_markup=cancel_kb)

# Отмена
@dp.message_handler(lambda m: m.text == "Отмена", state='*')
async def cancel_order(message: types.Message, state: FSMContext):
    await state.finish()
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Заказать кальян", "Меню")
    await message.answer("Заказ отменён. Возвращаемся в меню.", reply_markup=keyboard)

# Крепость
@dp.message_handler(state=OrderHookah.strength)
async def set_strength(message: types.Message, state: FSMContext):
    await state.update_data(strength=message.text)
    await OrderHookah.next()
    await message.answer("Напишите пожелания по вкусам (например: Фруктовый с холодком):")

# Вкусы
@dp.message_handler(state=OrderHookah.flavors)
async def set_flavors(message: types.Message, state: FSMContext):
    await state.update_data(flavors=message.text)
    await OrderHookah.next()

    buttons = [
        types.KeyboardButton("Молоко (+200)"),
        types.KeyboardButton("Вино (+400)"),
        types.KeyboardButton("Абсент (+500)"),
        types.KeyboardButton("Без добавок (+0)")
    ]
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True).add(*buttons)
    markup.add("Отмена")
    await message.answer("Выберите добавку:", reply_markup=markup)

# Добавка
@dp.message_handler(state=OrderHookah.additive)
async def set_additive(message: types.Message, state: FSMContext):
    additives = {
        "Молоко (+200)": 200,
        "Вино (+400)": 400,
        "Абсент (+500)": 500,
        "Без добавок (+0)": 0
    }
    selected = message.text
    if selected not in additives:
        await message.answer("Пожалуйста, выбери одну из предложенных добавок.")
        return

    await state.update_data(additive=selected, addon_price=additives[selected])
    await OrderHookah.next()
    await message.answer("Введите контактный номер телефона (Telegram / WhatsApp):", reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("Отмена"))

# Телефон
@dp.message_handler(state=OrderHookah.phone)
async def set_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await OrderHookah.next()
    await message.answer("Комментарий к заказу (необязательно). Можешь просто нажать 'Отмена', чтобы пропустить.")

# Комментарий
@dp.message_handler(state=OrderHookah.comment)
async def set_comment(message: types.Message, state: FSMContext):
    comment = message.text if message.text != "Отмена" else "Без комментария"
    await state.update_data(comment=comment)
    await OrderHookah.next()

    data = await state.get_data()
    total = data['price'] + data['addon_price']

    order_text = (
        f"<b>Новый заказ кальяна:</b>\n"
        f"Гость: @{message.from_user.username or message.from_user.full_name}\n"
        f"Чаша: {data['bowl']} — {data['price']}₽\n"
        f"Крепость: {data['strength']}\n"
        f"Добавка: {data['additive']}\n"
        f"Вкусы: {data['flavors']}\n"
        f"Телефон: {data['phone']}\n"
        f"Комментарий: {comment}\n"
        f"<b>Итого: {total}₽</b>\n"
        f"Способ оплаты: наличные / перевод\n\n"
        f"Статус: ❌ Не подтверждён"
    )

    # Отправка в чат сотрудников
    await bot.send_message(chat_id=STAFF_CHAT_ID, text=order_text, parse_mode="HTML")

    # Сообщение клиенту
    await message.answer("Спасибо! Ваш заказ принят, мы свяжемся с вами в ближайшее время 🙌", reply_markup=types.ReplyKeyboardRemove())
    await state.finish()
if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)