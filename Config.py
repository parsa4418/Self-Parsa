import os

# ===== تنظیمات بات =====
# توکن رو از Environment Variable می‌خونه (تو Render تنظیمش می‌کنی)
# برای تست رو کامپیوتر خودت هم می‌تونی مستقیم اینجا بذاری
BOT_TOKEN = os.environ.get("BOT_TOKEN", "PASTE_YOUR_BOT_TOKEN_HERE")

# آیدی عددی خودت (مالک بات). با ارسال هر پیامی به @userinfobot می‌تونی آیدیتو بگیری
OWNER_ID = int(os.environ.get("OWNER_ID", "8904869158"))

# متن پیشفرض منشی (وقتی وضعیتت "آفلاین"ه)
AWAY_MESSAGE = "سلام! الان آنلاین نیستم، پیامتو دیدم و بهت جواب می‌دم 🙏"

# لیست اولیه کلمات فیلتر شده (می‌تونی بعدا با دستور /addword اضافه کنی)
BANNED_WORDS = []
