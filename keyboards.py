from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_keyboard(is_admin=False):
    buttons = [
        ["💼 Đầu Tư", "💸 Rút Lãi"],
        ["💳 Nạp Tiền", "👤 Tài Khoản"]
    ]
    if is_admin:
        buttons.append(["⚙️ Admin Panel"])
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=b) for b in row] for row in buttons], resize_keyboard=True)

admin_panel_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📥 Duyệt Nạp"), KeyboardButton(text="📊 Thống Kê")],
        [KeyboardButton(text="🔙 Quay Lại")]
    ],
    resize_keyboard=True
)
