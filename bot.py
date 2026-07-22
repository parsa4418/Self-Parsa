from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from aiohttp import web
import asyncio
import os
import datetime
import json
import random

TOKEN = "8666764154:AAHL3wtaopyeL5jUyEsD4zLeuLeVLUyxPqk"  # ← توکن جدید از @BotFather

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

# ================== هندلرهای ربات ==================
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

# ================== راه‌اندازی ربات ==================
def create_bot_app():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("secretary_on", secretary_on))
    app.add_handler(CommandHandler("secretary_off", secretary_off))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("time", get_time))
    app.add_handler(CommandHandler("date", get_date))
    app.add_handler(CommandHandler("music", get_music))
    app.add_handler(MessageHandler(filters.ALL, auto_reply))
    return app

# ================== سرور aiohttp برای Render ==================
async def health_check(request):
    return web.Response(text="OK", status=200)

async def start_http_server():
    app = web.Application()
    app.router.add_get('/', health_check)
    app.router.add_get('/health', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"✅ HTTP server running on port {port}")
    # تا ابد منتظر بمون
    await asyncio.Event().wait()

# ================== اجرای همزمان ==================
async def main():
    # راه‌اندازی ربات در پس‌زمینه
    bot_app = create_bot_app()
    await bot_app.initialize()
    await bot_app.start()
    
    # شروع Polling ربات (بدون بلاک کردن)
    asyncio.create_task(bot_app.updater.start_polling())
    print("✅ ربات منشی روشن شد!")
    
    # راه‌اندازی سرور HTTP
    await start_http_server()

if __name__ == "__main__":
    asyncio.run(main())
