from telethon import TelegramClient, events
from telethon.tl.functions.account import UpdateProfileRequest
import asyncio
import datetime
import json
import os

api_id = 2880224
api_hash = '58f48230fbcf37ffb844ad36c982c86d'
your_name = "𝗣𝗔𝗥𝗦𝗔"
CONFIG_FILE = "bot_config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

client = TelegramClient(
    'self_session',
    api_id,
    api_hash,
    timeout=30,
    retry_delay=5,
    auto_reconnect=True
)

config = load_config()
is_secretary_on = config.get('is_secretary_on', False)
is_time_on = config.get('is_time_on', True)
is_smart_reply_on = config.get('is_smart_reply_on', False)
replied_chats = set()

default_smart_text = "سلام، الان ساعت {hour} هستش. اگر بین ۵ تا ۷ باشه، پیام میدم: ساعت کاریه، آفلاینم بعدا جواب میدم ✅"
smart_reply_text = config.get('smart_reply_text', default_smart_text)
reminders = {}

async def update_name_with_time():
    while True:
        try:
            if client.is_connected():
                config = load_config()
                time_status = config.get('is_time_on', True)
                if time_status:
                    current_time = datetime.datetime.now().strftime("%H:%M")
                    new_first_name = f"{your_name} | {current_time}"
                else:
                    new_first_name = your_name
                await client(UpdateProfileRequest(first_name=new_first_name))
        except Exception as e:
            print(f"⚠️ خطا در آپدیت اسم: {e}")
        await asyncio.sleep(60)

def get_time_based_reply():
    now = datetime.datetime.now()
    hour = now.hour
    current_time = now.strftime("%H:%M")
    if 5 <= hour <= 7:
        time_context = "ساعت کاریه"
    else:
        time_context = "ساعت غیرکاریه"
    reply = smart_reply_text.replace("{hour}", current_time)
    reply = reply.replace("{time_context}", time_context)
    return reply

async def check_reminders():
    while True:
        try:
            now = datetime.datetime.now()
            to_remove = []
            for user_id, (msg, remind_time) in reminders.items():
                if now >= remind_time:
                    await client.send_message(user_id, f"⏰ یادآوری: {msg}")
                    to_remove.append(user_id)
            for user_id in to_remove:
                del reminders[user_id]
        except Exception as e:
            print(f"⚠️ خطا در چک یادآوری: {e}")
        await asyncio.sleep(10)

@client.on(events.NewMessage(incoming=True))
async def handler(event):
    global is_secretary_on, is_time_on, is_smart_reply_on, replied_chats, smart_reply_text
    try:
        if event.is_private and event.out:
            text = event.raw_text.strip()
            if text == ".منشی روشن":
                is_secretary_on = True
                replied_chats.clear()
                config = load_config()
                config['is_secretary_on'] = True
                save_config(config)
                await event.reply("✅ منشی روشن شد")
                return
            elif text == ".منشی خاموش":
                is_secretary_on = False
                config = load_config()
                config['is_secretary_on'] = False
                save_config(config)
                await event.reply("❌ منشی خاموش شد")
                return
            elif text == ".ساعت اسم روشن":
                is_time_on = True
                config = load_config()
                config['is_time_on'] = True
                save_config(config)
                await event.reply("✅ نمایش ساعت در اسم فعال شد")
                current_time = datetime.datetime.now().strftime("%H:%M")
                new_first_name = f"{your_name} | {current_time}"
                await client(UpdateProfileRequest(first_name=new_first_name))
                return
            elif text == ".ساعت اسم خاموش":
                is_time_on = False
                config = load_config()
                config['is_time_on'] = False
                save_config(config)
                await event.reply("❌ نمایش ساعت در اسم غیرفعال شد")
                await client(UpdateProfileRequest(first_name=your_name))
                return
            elif text.startswith(".تنظیم منشی "):
                new_text = text[len(".تنظیم منشی "):].strip()
                if new_text:
                    smart_reply_text = new_text
                    config = load_config()
                    config['smart_reply_text'] = smart_reply_text
                    save_config(config)
                    await event.reply(f"✅ متن پاسخ هوشمند به‌روز شد:\n\n{smart_reply_text}")
                else:
                    await event.reply("❌ لطفاً متن جدید رو بعد از دستور بنویسید.")
                return
            elif text == ".منشی هوشمند روشن":
                is_smart_reply_on = True
                config = load_config()
                config['is_smart_reply_on'] = True
                save_config(config)
                await event.reply("✅ پاسخ هوشمند (بر اساس ساعت) فعال شد")
                return
            elif text == ".منشی هوشمند خاموش":
                is_smart_reply_on = False
                config = load_config()
                config['is_smart_reply_on'] = False
                save_config(config)
                await event.reply("❌ پاسخ هوشمند غیرفعال شد")
                return
            elif text.startswith(".یادآوری "):
                parts = text.split(" ", 2)
                if len(parts) >= 3:
                    try:
                        minutes = int(parts[1])
                        msg = parts[2]
                        if 1 <= minutes <= 60:
                            remind_time = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
                            reminders[event.chat_id] = (msg, remind_time)
                            await event.reply(f"⏰ یادآوری برای {minutes} دقیقه دیگه تنظیم شد:\n{msg}")
                        else:
                            await event.reply("❌ زمان باید بین ۱ تا ۶۰ دقیقه باشه")
                    except ValueError:
                        await event.reply("❌ فرمت صحیح: .یادآوری 10 پیام شما")
                else:
                    await event.reply("❌ فرمت صحیح: .یادآوری 10 پیام شما")
                return
            elif text == ".یادآوری خاموش":
                if event.chat_id in reminders:
                    del reminders[event.chat_id]
                    await event.reply("❌ یادآوری‌های شما لغو شد")
                else:
                    await event.reply("ℹ️ شما یادآوری فعالی ندارید")
                return
            elif text == ".وضعیت":
                status = f"""📊 وضعیت بات:
• منشی: {'روشن' if is_secretary_on else 'خاموش'}
• ساعت اسم: {'روشن' if is_time_on else 'خاموش'}
• منشی هوشمند: {'روشن' if is_smart_reply_on else 'خاموش'}
• یادآوری فعال: {'دارید' if event.chat_id in reminders else 'ندارید'}
• تعداد پیام‌های پاسخ داده شده: {len(replied_chats)}"""
                await event.reply(status)
                return
        if event.is_private and not event.out and event.chat_id not in replied_chats:
            reply_text = None
            if is_smart_reply_on:
                reply_text = get_time_based_reply()
            elif is_secretary_on:
                reply_text = "سلام، فعلاً آفلاینم. آنلاین شدم جواب می‌دم ✅"
            if reply_text:
                await event.reply(reply_text)
                replied_chats.add(event.chat_id)
    except Exception as e:
        print(f"⚠️ خطا در پردازش پیام: {e}")

async def main():
    try:
        print("🔄 در حال اتصال به تلگرام...")
        await client.start()
        print("✅ سلف بات روشن شد!")
        print("\n📌 دستورات:")
        print("   • .منشی روشن  |  .منشی خاموش")
        print("   • .ساعت اسم روشن  |  .ساعت اسم خاموش")
        print("   • .منشی هوشمند روشن  |  .منشی هوشمند خاموش")
        print("   • .تنظیم منشی [متن جدید]")
        print("   • .یادآوری [دقیقه] [پیام]")
        print("   • .یادآوری خاموش")
        print("   • .وضعیت")
        asyncio.create_task(update_name_with_time())
        asyncio.create_task(check_reminders())
        await client.run_until_disconnected()
    except Exception as e:
        print(f"❌ خطای اصلی: {e}")
        print("🔄 دوباره تلاش میکنم...")
        await asyncio.sleep(5)
        await main()

if __name__ == "__main__":
    asyncio.run(main())
