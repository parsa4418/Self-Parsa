from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import datetime
import json
import os
import random
import requests
import pytz
import asyncio
import threading
from aiohttp import web

TOKEN = "8666764154:AAH29o8bOAzmXzvbU428TJ6WLtQQcHWwOTE"  # ← توکن خودت رو از @BotFather بگیر

CONFIG_FILE = "bot_config.json"
DATA_FILE = "user_data.json"

# ================== توابع ذخیره و بارگذاری ==================
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

config = load_config()
user_data = load_data()

# ================== وضعیت‌ها ==================
is_secretary_on = config.get('is_secretary_on', False)
is_time_on = config.get('is_time_on', True)
replied_chats = set()

# ================== دکمه‌های اصلی ==================
def main_menu():
    keyboard = [
        [InlineKeyboardButton("📋 وضعیت", callback_data="status")],
        [InlineKeyboardButton("🎵 نت‌های موسیقی", callback_data="music")],
        [InlineKeyboardButton("⏰ تنظیمات", callback_data="settings")],
        [InlineKeyboardButton("ℹ️ راهنما", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)

def settings_menu():
    keyboard = [
        [InlineKeyboardButton("🕐 ساعت روشن" if not is_time_on else "🕐 ساعت خاموش", callback_data="toggle_time")],
        [InlineKeyboardButton("📨 منشی روشن" if not is_secretary_on else "📨 منشی خاموش", callback_data="toggle_secretary")],
        [InlineKeyboardButton("🔙 برگشت", callback_data="back")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ================== دستور /start ==================
async def start(update: Update, context):
    await update.message.reply_text(
        "🤖 **ربات کامل و حرفه‌ای**\n\n"
        "✅ همه قابلیت‌ها در یک ربات!\n"
        "🔹 `.منشی روشن`\n"
        "🔹 `.منشی خاموش`\n"
        "🔹 `.ساعت روشن`\n"
        "🔹 `.ساعت خاموش`\n"
        "🔹 `.وضعیت`\n"
        "🔹 `.موسیقی`\n"
        "🔹 `.تاریخ`\n"
        "🔹 `.ساعت`\n"
        "🔹 `.راهنما`\n\n"
        "📌 از دکمه‌ها هم می‌تونی استفاده کنی.",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )

# ================== دکمه‌ها ==================
async def button_handler(update: Update, context):
    global is_secretary_on, is_time_on
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "status":
        text = f"📊 **وضعیت:**\n• منشی: {'روشن' if is_secretary_on else 'خاموش'}\n• ساعت: {'روشن' if is_time_on else 'خاموش'}"
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=main_menu())

    elif data == "music":
        notes = random.choice([
            "🎵 ♩ ♪ ♫ ♬", "🎶 ♬ ♪ ♩ ♫", "♫ ♩ ♪ ♬ 🎵", "🎶 ♫ ♬ ♪"
        ])
        await query.edit_message_text(f"{notes}\n\nاین هم یه ریتم موسیقی!", reply_markup=main_menu())

    elif data == "settings":
        await query.edit_message_text("⚙️ **تنظیمات:**", reply_markup=settings_menu(), parse_mode="Markdown")

    elif data == "toggle_time":
        is_time_on = not is_time_on
        config['is_time_on'] = is_time_on
        save_config(config)
        text = "✅ ساعت روشن شد" if is_time_on else "❌ ساعت خاموش شد"
        await query.edit_message_text(text, reply_markup=settings_menu())

    elif data == "toggle_secretary":
        is_secretary_on = not is_secretary_on
        config['is_secretary_on'] = is_secretary_on
        save_config(config)
        text = "✅ منشی روشن شد" if is_secretary_on else "❌ منشی خاموش شد"
        await query.edit_message_text(text, reply_markup=settings_menu())

    elif data == "help":
        await query.edit_message_text(
            "📖 **راهنما:**\n\n"
            "🔹 `.منشی روشن` / `.منشی خاموش`\n"
            "🔹 `.ساعت روشن` / `.ساعت خاموش`\n"
            "🔹 `.وضعیت`\n"
            "🔹 `.موسیقی`\n"
            "🔹 `.تاریخ`\n"
            "🔹 `.ساعت`\n"
            "🔹 `.راهنما`",
            reply_markup=main_menu()
        )

    elif data == "back":
        await query.edit_message_text("🤖 **منوی اصلی**", reply_markup=main_menu())

# ================== دستورات متنی ==================
async def text_commands(update: Update, context):
    global is_secretary_on, is_time_on
    text = update.message.text.strip()

    if text == ".منشی روشن":
        is_secretary_on = True
        config['is_secretary_on'] = True
        save_config(config)
        await update.message.reply_text("✅ منشی روشن شد")

    elif text == ".منشی خاموش":
        is_secretary_on = False
        config['is_secretary_on'] = False
        save_config(config)
        await update.message.reply_text("❌ منشی خاموش شد")

    elif text == ".ساعت روشن":
        is_time_on = True
        config['is_time_on'] = True
        save_config(config)
        await update.message.reply_text("✅ ساعت روشن شد")

    elif text == ".ساعت خاموش":
        is_time_on = False
        config['is_time_on'] = False
        save_config(config)
        await update.message.reply_text("❌ ساعت خاموش شد")

    elif text == ".وضعیت":
        await update.message.reply_text(
            f"📊 **وضعیت:**\n• منشی: {'روشن' if is_secretary_on else 'خاموش'}\n• ساعت: {'روشن' if is_time_on else 'خاموش'}",
            parse_mode="Markdown"
        )

    elif text == ".موسیقی":
        notes = random.choice(["♩ ♪ ♫ ♬", "♬ ♪ ♩ ♫", "🎵 ♫ ♬ ♪"])
        await update.message.reply_text(f"🎵 {notes}")

    elif text == ".تاریخ":
        now = datetime.datetime.now()
        shamsi = now.strftime("%Y/%m/%d")  # قابل تبدیل به شمسی با کتابخونه
        await update.message.reply_text(f"📅 تاریخ امروز: {shamsi}")

    elif text == ".ساعت":
        tehran = pytz.timezone('Asia/Tehran')
        now = datetime.datetime.now(tehran).strftime("%H:%M:%S")
        await update.message.reply_text(f"🕐 ساعت الان: {now}")

    elif text == ".راهنما":
        await update.message.reply_text(
            "📖 **راهنما:**\n\n"
            "🔹 `.منشی روشن` / `.منشی خاموش`\n"
            "🔹 `.ساعت روشن` / `.ساعت خاموش`\n"
            "🔹 `.وضعیت`\n"
            "🔹 `.موسیقی`\n"
            "🔹 `.تاریخ`\n"
            "🔹 `.ساعت`\n"
            "🔹 `.راهنما`"
        )

# ================== پاسخ خودکار ==================
async def auto_reply(update: Update, context):
    if is_secretary_on and update.message.chat_id not in replied_chats:
        await update.message.reply_text("سلام، فعلاً آفلاینم. آنلاین شدم جواب می‌دم ✅")
        replied_chats.add(update.message.chat_id)

# ================== سرور HTTP برای Render ==================
async def health_check(request):
    return web.Response(text="OK", status=200)

async def start_http_server():
    app = web.Application()
    app.router.add_get('/health', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 10000)
    await site.start()
    print("✅ HTTP server is running on port 10000")
    await asyncio.Event().wait()

def run_http_server():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_http_server())

# ================== اجرا ==================
def main():
    # اجرای سرور HTTP در یک ترد جداگانه
    threading.Thread(target=run_http_server, daemon=True).start()
    
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_commands))
    app.add_handler(MessageHandler(filters.ALL, auto_reply))

    print("✅ ربات کامل با همه قابلیت‌ها روشن شد!")
    app.run_polling()

if __name__ == "__main__":
    main()
