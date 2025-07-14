from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.callback_data import CallbackData
import os

# ───────────────────────────────  конфиг  ───────────────────────────────
API_TOKEN   = os.getenv("BOT_TOKEN")
STAFF_CHAT  = int(os.getenv("STAFF_CHAT_ID"))

if not API_TOKEN or not STAFF_CHAT:
    raise RuntimeError("BOT_TOKEN и STAFF_CHAT_ID должны быть заданы в Render → Environment!")

bot = Bot(API_TOKEN, parse_mode="HTML")
dp  = Dispatcher(bot, storage=MemoryStorage())

# callback‑data для inline‑кнопок
order_cb = CallbackData("order", "action", "user_id")

# ───────────────────────────────  FSM  ───────────────────────────────
class Order(StatesGroup):
    strength = State()
    flavors  = State()
    additive = State()
    phone    = State()
    comment  = State()

# ─────────────────────────────  хэндлеры  ──────────────────────────────
@dp.message_handler(commands="start", state="*")
async def cmd_start(m: types.Message, state: FSMContext):
    await state.finish()
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Заказать кальян", "Меню и цены")
    await m.answer("Добро пожаловать! Выберите действие:", reply_markup=kb)

@dp.message_handler(lambda x: x.text == "Отмена", state="*")
async def any_cancel(m: types.Message, state: FSMContext):
    await state.finish()
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Заказать кальян", "Меню и цены")
    await m.answer("Отменено. Возвращаемся в меню.", reply_markup=kb)

@dp.message_handler(lambda x: x.text == "Заказать кальян", state="*")
async def start_order(m: types.Message, state: FSMContext):
    await state.update_data(price=3000, bowl="Кальян на чаше")
    await Order.strength.set()
    await m.answer("Крепость от 1 до 10 (можно диапазон 6‑7, 8‑10):",
                   reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("Отмена"))

@dp.message_handler(state=Order.strength)
async def set_strength(m: types.Message, state: FSMContext):
    await state.update_data(strength=m.text)
    await Order.next()
    await m.answer("Пожелания по вкусам (например: Фруктовый с холодком):")

@dp.message_handler(state=Order.flavors)
async def set_flavors(m: types.Message, state: FSMContext):
    await state.update_data(flavors=m.text)
    kb = (types.ReplyKeyboardMarkup(resize_keyboard=True)
          .add("Молоко (+200)", "Вино (+400)")
          .add("Абсент (+500)", "Без добавок (+0)")
          .add("Отмена"))
    await Order.next()
    await m.answer("Выберите добавку:", reply_markup=kb)

@dp.message_handler(state=Order.additive)
async def set_additive(m: types.Message, state: FSMContext):
    prices = {"Молоко (+200)":200, "Вино (+400)":400, "Абсент (+500)":500, "Без добавок (+0)":0}
    if m.text not in prices:
        return await m.answer("Выбери кнопку.")
    await state.update_data(additive=m.text, addon_price=prices[m.text])
    await Order.next()
    await m.answer("Телефон (WhatsApp / Telegram):",
                   reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("Отмена"))

@dp.message_handler(state=Order.phone)
async def set_phone(m: types.Message, state: FSMContext):
    await state.update_data(phone=m.text)
    await Order.next()
    await m.answer("Комментарий (необязательно) или «-»:",
                   reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("Отмена"))

@dp.message_handler(state=Order.comment)
async def finish_order(m: types.Message, state: FSMContext):
    await state.update_data(comment=m.text if m.text.strip() != "-" else "Без комментария")
    data = await state.get_data()
    total = data["price"] + data["addon_price"]

    user_tag = f"@{m.from_user.username}" if m.from_user.username else m.from_user.full_name
    order_txt = (f"<b>Новый заказ кальяна:</b>\n\n"
                 f"Гость: {user_tag}\n"
                 f"Чаша: {data['bowl']} — {data['price']}₽\n"
                 f"Крепость: {data['strength']}\n"
                 f"Добавка: {data['additive']}\n"
                 f"Вкусы: {data['flavors']}\n"
                 f"Телефон: {data['phone']}\n"
                 f"Комментарий: {data['comment']}\n"
                 f"<b>Итого: {total}₽</b>\n"
                 f"Оплата: наличные/перевод.\n\n"
                 f"Статус: ❌ Не подтверждён")

    # inline‑кнопки подтверждения
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("✅ Подтвердить",
                                   callback_data=order_cb.new(action="ok", user_id=m.from_user.id)),
        types.InlineKeyboardButton("❌ Отменить",
                                   callback_data=order_cb.new(action="cancel", user_id=m.from_user.id))
    )

    await bot.send_message(STAFF_CHAT, order_txt, reply_markup=kb)
    await m.answer("Спасибо! Заказ передан сотрудникам 😊", reply_markup=types.ReplyKeyboardRemove())
    await state.finish()

# ──────────────────  обработка inline‑кнопок в чате персонала ──────────────────
@dp.callback_query_handler(order_cb.filter())
async def cb_staff(query: types.CallbackQuery, callback_data: dict):
    action   = callback_data["action"]
    user_id  = int(callback_data["user_id"])

    if action == "ok":
        new_text = query.message.html_text.replace("❌ Не подтверждён", "✅ Подтверждён")
        status   = "✅ Заказ подтверждён!"
    else:
        new_text = query.message.html_text.replace("❌ Не подтверждён", "❌ Отменён")
        status   = "❌ Заказ отменён."

    await query.message.edit_text(new_text, reply_markup=None)
    await bot.send_message(user_id, status)
    await query.answer("Статус обновлён")

# ─────────────────────────  запуск ─────────────────────────
if __name__ == "__main__":
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
