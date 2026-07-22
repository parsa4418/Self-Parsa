from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from flask import Flask
import threading
import os
import datetime
import json
import random

TOKEN = "8666764154:AAHGJCuDbgHg7uJb3UYlL04tmlwVZzTrNJs"  # ← توکن جدید از @BotFather

# ========== فلاسک اپ برای Render ==========
flask_app = Flask(__name__)

@flask_app.route('/')
@flask_app.route('/health')
def health_check():
    return "OK", 200

# ========== ربات تلگرام ==========
CONFIG_FILE = "bot_config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

config = load_config()
is_secretary_on = config.get('is_secretary_on', False)
replied_chats = set()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 **ربات منشی حرفه‌ای**\n\n"
        "📌 دستورات:\n"
        "/secretary_on - روشن کردن منشی\n"
        "/secretary_off - خاموش کردن منشی\n"
        "/status - وضعیت فعلی\n"
        "/time - ساعت الان\n"
        "/date - تاریخ امروز\n"
        "/music - نت موسیقی",
        parse_mode="Markdown"
    )

async def secretary_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_secretary_on
    is_secretary_on = True
    config['is_secretary_on'] = True
    save_config(config)
    await update.message.reply_text("✅ منشی روشن شد")

async def secretary_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_secretary_on
    is_secretary_on = False
    config['is_secretary_on'] = False
    save_config(config)
    await update.message.reply_text("❌ منشی خاموش شد")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status_text = "روشن" if is_secretary_on else "خاموش"
    await update.message.reply_text(f"📊 وضعیت منشی: {status_text}")

async def get_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.datetime.now().strftime("%H:%M:%S")
    await update.message.reply_text(f"🕐 ساعت: {now}")

async def get_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.datetime.now().strftime("%Y/%m/%d")
    await update.message.reply_text(f"📅 تاریخ: {now}")

async def get_music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    notes = random.choice(["♩ ♪ ♫ ♬", "♬ ♪ ♩ ♫", "🎵 ♫ ♬ ♪", "🎶 ♬ ♪ ♩ ♫"])
    await update.message.reply_text(f"🎵 {notes}")

async def auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    chat_id = update.message.chat_id
    if is_secretary_on and chat_id not in replied_chats:
        await update.message.reply_text("سلام، فعلاً آفلاینم. آنلاین شدم جواب می‌دم ✅")
        replied_chats.add(chat_id)

def run_bot():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("secretary_on", secretary_on))
    app.add_handler(CommandHandler("secretary_off", secretary_off))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("time", get_time))
    app.add_handler(CommandHandler("date", get_date))
    app.add_handler(CommandHandler("music", get_music))
    app.add_handler(MessageHandler(filters.ALL, auto_reply))
    
    print("✅ ربات منشی روشن شد!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    # ====== اجرای ربات در یک ترد جداگانه ======
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # ====== اجرای سرور Flask برای Render ======
    port = int(os.environ.get("PORT", 10000))
    print(f"✅ Flask server running on port {port}")
    flask_app.run(host="0.0.0.0", port=port)
