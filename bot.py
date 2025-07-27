import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardRemove
from aiogram import Router
from aiogram.utils.markdown import hbold
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from config import *
from keyboards import main_keyboard, admin_panel_kb
from states import *
from utils import *

bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

router = Router()
dp.include_router(router)

@dp.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    get_or_create_user(message.from_user.id)
    is_admin = str(message.from_user.id) in ADMIN_IDS
    await message.answer("🎉 Chào mừng đến với bot đầu tư!", reply_markup=main_keyboard(is_admin))

@dp.message(F.text == "💼 Đầu Tư")
async def invest_menu(message: Message, state: FSMContext):
    await state.set_state(InvestmentStates.waiting_for_package_choice)
    text = "📦 Gói đầu tư:\n"
    for i, g in enumerate(INVESTMENTS, 1):
        text += f"{i}. {g['name']}: {g['amount']:,}đ - {g['daily']:,}đ/ngày × {g['days']} ngày\n"
    text += "\n👉 Nhập số thứ tự gói bạn chọn:"
    await message.answer(text)

@dp.message(InvestmentStates.waiting_for_package_choice)
async def handle_package(message: Message, state: FSMContext):
    try:
        idx = int(message.text) - 1
        package = INVESTMENTS[idx]
    except:
        await message.answer("❌ Vui lòng nhập số thứ tự hợp lệ.")
        return
    data = load_users()
    user = get_or_create_user(message.from_user.id, data)
    if user["balance"] < package["amount"]:
        await message.answer("❌ Bạn không đủ số dư.")
        await state.clear()
        return
    user["balance"] -= package["amount"]
    invest(message.from_user.id, package)
    await state.clear()
    await message.answer(f"✅ Đầu tư {package['name']} thành công!")

@dp.message(F.text == "💳 Nạp Tiền")
async def ask_deposit(message: Message, state: FSMContext):
    await state.set_state(DepositStates.waiting_for_amount)
    await message.answer("💰 Nhập số tiền muốn nạp:")

@dp.message(DepositStates.waiting_for_amount)
async def process_deposit(message: Message, state: FSMContext):
    try:
        amount = int(message.text.strip())
        if amount < 1000:
            raise ValueError
    except:
        await message.answer("❌ Nhập số hợp lệ (>1000đ).")
        return
    data = load_users()
    user = get_or_create_user(message.from_user.id, data)
    user["deposits"].append({"amount": amount, "time": current_time()})
    save_users(data)
    await state.clear()
    await message.answer(
        f"✅ Ghi nhận nạp {amount:,}đ.\n\n"
        f"🏦 {BOT_BANK_NAME} - {BOT_BANK_NUMBER}\n"
        f"📄 Nội dung: NAP {message.from_user.id}"
    )

@dp.message(F.text == "💸 Rút Lãi")
async def ask_withdraw(message: Message, state: FSMContext):
    await state.set_state(WithdrawStates.waiting_for_amount)
    user = get_or_create_user(message.from_user.id)
    profit = calculate_profit(message.from_user.id)
    withdrawn = sum(w["amount"] for w in user["withdrawals"])
    available = profit - withdrawn
    await message.answer(f"💰 Lãi khả dụng: {available:,}đ\n👉 Nhập số muốn rút:")

@dp.message(WithdrawStates.waiting_for_amount)
async def process_withdraw(message: Message, state: FSMContext):
    try:
        amount = int(message.text.strip())
    except:
        await message.answer("❌ Nhập số tiền hợp lệ.")
        return
    if withdraw(message.from_user.id, amount):
        await message.answer(f"✅ Đã gửi yêu cầu rút {amount:,}đ.")
    else:
        await message.answer("❌ Số tiền không hợp lệ hoặc vượt quá hạn mức/lãi.")
    await state.clear()

@dp.message(F.text == "👤 Tài Khoản")
async def account_info(message: Message, state: FSMContext):
    await state.clear()
    user = get_or_create_user(message.from_user.id)
    profit = calculate_profit(message.from_user.id)
    withdrawn = sum(w["amount"] for w in user["withdrawals"])
    available = profit - withdrawn
    text = (
        f"👤 ID: <code>{message.from_user.id}</code>\n"
        f"💰 Số dư: {user['balance']:,}đ\n"
        f"📈 Lãi khả dụng: {available:,}đ\n"
        f"🏦 STK: {user['bank']} - {user['bank_number']}"
    )
    await message.answer(text)

@dp.message(F.text == "/bank")
async def set_bank(message: Message, state: FSMContext):
    await state.clear()
    try:
        _, bank, number = message.text.strip().split(maxsplit=2)
        data = load_users()
        user = get_or_create_user(message.from_user.id, data)
        user["bank"] = bank
        user["bank_number"] = number
        save_users(data)
        await message.answer("✅ Đã cập nhật STK.")
    except:
        await message.answer("❌ Dùng đúng cú pháp: /bank TênNH STK")

@dp.message(F.text == "⚙️ Admin Panel")
async def admin_panel(message: Message):
    if str(message.from_user.id) in ADMIN_IDS:
        await message.answer("🔧 Admin Panel:", reply_markup=admin_panel_kb)

@dp.message(F.text == "📥 Duyệt Nạp")
async def approve_deposits(message: Message):
    if str(message.from_user.id) not in ADMIN_IDS:
        return
    data = load_users()
    text = ""
    for uid, u in data.items():
        for d in u.get("deposits", []):
            text += f"👤 {uid}: {d['amount']:,}đ lúc {d['time']}\n"
    await message.answer(text or "📥 Không có yêu cầu nạp.")

@dp.message(F.text == "📊 Thống Kê")
async def show_stats(message: Message):
    if str(message.from_user.id) not in ADMIN_IDS:
        return
    data = load_users()
    total_users = len(data)
    total_balance = sum(u["balance"] for u in data.values())
    total_profit = sum(calculate_profit(uid) for uid in data)
    await message.answer(
        f"📊 Người dùng: {total_users}\n"
        f"💰 Tổng số dư: {total_balance:,}đ\n"
        f"📈 Tổng lãi: {total_profit:,}đ"
    )

@dp.message(F.text == "🔙 Quay Lại")
async def back_to_menu(message: Message, state: FSMContext):
    await state.clear()
    is_admin = str(message.from_user.id) in ADMIN_IDS
    await message.answer("⬅️ Trở về menu", reply_markup=main_keyboard(is_admin))

# Auto cộng lãi mỗi 24h
async def auto_profit_loop():
    while True:
        load_users()
        await asyncio.sleep(86400)

if __name__ == "__main__":
    dp.run_polling(bot)
