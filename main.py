import json
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
from config import BOT_TOKEN
from instagram import login_instagram, get_engaged_users, like_and_follow
from scheduler import start_schedule

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

with open("db.json", "r") as f:
    db = json.load(f)

keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(KeyboardButton("➕ Добавить Instagram аккаунт"))
keyboard.add(KeyboardButton("🎯 Добавить цель"))
keyboard.add(KeyboardButton("🚀 Начать парсинг"))
keyboard.add(KeyboardButton("🛑 Стоп"))
keyboard.add(KeyboardButton("📊 Отчет"))

@dp.message_handler(commands=["start"])
async def start_cmd(message: types.Message):
    await message.answer("Привет! Выбери действие:", reply_markup=keyboard)

@dp.message_handler(lambda msg: msg.text == "➕ Добавить Instagram аккаунт")
async def add_account(message: types.Message):
    await message.answer("Отправь логин и пароль через пробел (логин пароль):")

@dp.message_handler(lambda msg: msg.text == "🎯 Добавить цель")
async def add_target(message: types.Message):
    await message.answer("Отправь никнейм цели (без @):")

@dp.message_handler(lambda msg: msg.text == "🚀 Начать парсинг")
async def start_parsing(message: types.Message):
    user_id = str(message.from_user.id)
    user_data = db["users"].get(user_id)
    if not user_data:
        await message.answer("Сначала добавь Instagram аккаунт!")
        return
    cl = login_instagram(user_data["instagram_username"], user_data["instagram_password"])
    all_targets = user_data.get("targets", [])
    report = []
    db["stop_flags"][user_id] = "run"

    for target in all_targets:
        users = get_engaged_users(target)
        await message.answer(f"Найдено: {len(users)} активных у @{target}")
        await asyncio.to_thread(like_and_follow, cl, users[:10], user_id, db["stop_flags"], report)

    db["reports"][user_id] = report
    with open("db.json", "w") as f:
        json.dump(db, f)
    await message.answer("✅ Парсинг завершён!")

@dp.message_handler(lambda msg: msg.text == "🛑 Стоп")
async def stop_task(message: types.Message):
    user_id = str(message.from_user.id)
    db["stop_flags"][user_id] = "stop"
    await message.answer("⛔ Парсинг остановлен.")
    with open("db.json", "w") as f:
        json.dump(db, f)

@dp.message_handler(lambda msg: msg.text == "📊 Отчет")
async def show_report(message: types.Message):
    user_id = str(message.from_user.id)
    report = db.get("reports", {}).get(user_id, [])
    if not report:
        await message.answer("Пока нет отчета.")
    else:
        await message.answer("Вот на кого подписались:
" + "\n".join(report))

@dp.message_handler()
async def handle_text(message: types.Message):
    user_id = str(message.from_user.id)
    parts = message.text.strip().split()
    if len(parts) == 2:
        login, password = parts
        db["users"][user_id] = {
            "instagram_username": login,
            "instagram_password": password,
            "targets": []
        }
        await message.answer("✅ Аккаунт добавлен!")
    elif len(parts) == 1:
        db["users"].setdefault(user_id, {}).setdefault("targets", []).append(parts[0])
        await message.answer(f"🎯 Цель @{parts[0]} добавлена.")
    with open("db.json", "w") as f:
        json.dump(db, f)

def scheduled_parsing():
    import threading
    for user_id, user_data in db["users"].items():
        def task():
            try:
                cl = login_instagram(user_data["instagram_username"], user_data["instagram_password"])
                all_targets = user_data.get("targets", [])
                report = []
                for target in all_targets:
                    users = get_engaged_users(target)
                    like_and_follow(cl, users[:10], user_id, db["stop_flags"], report)
                db["reports"][user_id] = report
                with open("db.json", "w") as f:
                    json.dump(db, f)
            except Exception as e:
                print(f"Ошибка по расписанию: {e}")
        threading.Thread(target=task).start()

if __name__ == "__main__":
    start_schedule()
    executor.start_polling(dp, skip_updates=True)