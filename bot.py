from telegram import Update, Message
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8666764154:AAHGJCuDbgHg7uJb3UYlL04tmlwVZzTrNJs"

# لیست کاربرانی که قبلاً بهشون پاسخ داده شده
replied_users = set()

async def start(update: Update, context):
    await update.message.reply_text("✅ ربات روشن شد! منشی رو با /secretary_on فعال کن.")

async def secretary_on(update: Update, context):
    context.bot_data['is_secretary_on'] = True
    await update.message.reply_text("✅ منشی روشن شد")

async def secretary_off(update: Update, context):
    context.bot_data['is_secretary_on'] = False
    await update.message.reply_text("❌ منشی خاموش شد")

async def auto_reply(update: Update, context):
    if not update.message or not update.message.text:
        return
    
    is_on = context.bot_data.get('is_secretary_on', False)
    chat_id = update.message.chat_id
    
    if is_on and chat_id not in replied_users:
        await update.message.reply_text("سلام، فعلاً آفلاینم. آنلاین شدم جواب می‌دم ✅")
        replied_users.add(chat_id)

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("secretary_on", secretary_on))
    app.add_handler(CommandHandler("secretary_off", secretary_off))
    app.add_handler(MessageHandler(filters.ALL, auto_reply))
    
    print("✅ ربات منشی روشن شد!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
