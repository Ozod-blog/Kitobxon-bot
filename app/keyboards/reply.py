from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu(is_admin: bool = False):
    rows = [
        [KeyboardButton(text="📚 Kitoblar"), KeyboardButton(text="📖 O‘qishni boshlash")],
        [KeyboardButton(text="👤 Mening profilim"), KeyboardButton(text="🏆 Reyting")],
        [KeyboardButton(text="🎁 Sovg‘alar bozori"), KeyboardButton(text="👥 Do‘stlarni taklif qilish")],
        [KeyboardButton(text="ℹ️ Yordam")],
    ]
    if is_admin:
        rows.append([KeyboardButton(text="🛠 Admin paneli")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)

def admin_menu():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="📊 Statistika"), KeyboardButton(text="👥 Foydalanuvchilar")],
        [KeyboardButton(text="📚 Kitoblarni boshqarish"), KeyboardButton(text="➕ Kitob qo‘shish")],
        [KeyboardButton(text="➕ PDF kitob yuklash")],
        [KeyboardButton(text="📄 Sahifa matni qo‘shish"), KeyboardButton(text="🎁 Sovg‘a qo‘shish")],
        [KeyboardButton(text="🎁 Sovg‘alarni boshqarish")],
        [KeyboardButton(text="🧾 Buyurtmalar"), KeyboardButton(text="🪙 Tangalarni boshqarish")],
        [KeyboardButton(text="📣 Xabar yuborish"), KeyboardButton(text="🚫 BAN boshqaruvi")],
        [KeyboardButton(text="⬅️ Asosiy menyu")],
    ], resize_keyboard=True)

def contact_keyboard():
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)],
                                         [KeyboardButton(text="❌ Bekor qilish")]], resize_keyboard=True, one_time_keyboard=True)
