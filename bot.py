import logging
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime, time as dtime
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

import config

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
log = logging.getLogger(__name__)

STATE_FILE = "state.json"

DEFAULT_STATE = {
    "is_online": True,
    "clock_enabled": False,
    "locks": {"links": False, "forward": False, "sticker": False},
    "banned_words": list(config.BANNED_WORDS),
}


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            merged = DEFAULT_STATE.copy()
            merged.update(data)
            return merged
    return DEFAULT_STATE.copy()


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


state = load_state()


def is_owner(update: Update) -> bool:
    return update.effective_user and update.effective_user.id == config.OWNER_ID


async def owner_only_guard(update: Update) -> bool:
    if not is_owner(update):
        await update.message.reply_text("این دستور فقط برای مالک بات مجازه.")
        return False
    return True


# ---------------- دستورات پایه ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_owner(update):
        await update.message.reply_text(
            "سلام! دستورات موجود:\n"
            "/online - حالت آنلاین\n"
            "/offline - حالت آفلاین (منشی خودکار جواب می‌ده)\n"
            "/clock on|off - نمایش ساعت به‌جای اسم بات\n"
            "/addword کلمه - اضافه کردن کلمه به فیلتر\n"
            "/removeword کلمه - حذف کلمه از فیلتر\n"
            "/listwords - لیست کلمات فیلتر شده\n"
            "/lock links|forward|sticker - قفل کردن نوع پیام در گروه\n"
            "/unlock links|forward|sticker - باز کردن قفل"
        )
    else:
        await update.message.reply_text("سلام!")


async def go_online(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await owner_only_guard(update):
        return
    state["is_online"] = True
    save_state(state)
    await update.message.reply_text("وضعیت: آنلاین ✅")


async def go_offline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await owner_only_guard(update):
        return
    state["is_online"] = False
    save_state(state)
    await update.message.reply_text("وضعیت: آفلاین. منشی خودکار فعال شد ✅")


# ---------------- ساعت به‌جای اسم ----------------

async def clock_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await owner_only_guard(update):
        return
    if not context.args or context.args[0] not in ("on", "off"):
        await update.message.reply_text("استفاده: /clock on یا /clock off")
        return
    state["clock_enabled"] = context.args[0] == "on"
    save_state(state)
    await update.message.reply_text(f"نمایش ساعت: {'فعال' if state['clock_enabled'] else 'غیرفعال'}")


async def update_clock_job(context: ContextTypes.DEFAULT_TYPE):
    if not state.get("clock_enabled"):
        return
    now = datetime.now().strftime("%H:%M")
    try:
        await context.bot.set_my_name(name=f"⏰ {now}")
    except Exception as e:
        log.warning(f"clock update failed: {e}")


# ---------------- فیلتر کلمات ----------------

async def add_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await owner_only_guard(update):
        return
    if not context.args:
        await update.message.reply_text("استفاده: /addword کلمه")
        return
    word = " ".join(context.args).strip()
    if word not in state["banned_words"]:
        state["banned_words"].append(word)
        save_state(state)
    await update.message.reply_text(f"اضافه شد: {word}")


async def remove_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await owner_only_guard(update):
        return
    if not context.args:
        await update.message.reply_text("استفاده: /removeword کلمه")
        return
    word = " ".join(context.args).strip()
    if word in state["banned_words"]:
        state["banned_words"].remove(word)
        save_state(state)
        await update.message.reply_text(f"حذف شد: {word}")
    else:
        await update.message.reply_text("این کلمه توی لیست نیست.")


async def list_words(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await owner_only_guard(update):
        return
    words = state["banned_words"]
    await update.message.reply_text("لیست کلمات فیلتر:\n" + ("\n".join(words) if words else "خالیه"))


# ---------------- قفل‌های گروه ----------------

async def lock_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await owner_only_guard(update):
        return
    if not context.args or context.args[0] not in state["locks"]:
        await update.message.reply_text("استفاده: /lock links یا forward یا sticker")
        return
    state["locks"][context.args[0]] = True
    save_state(state)
    await update.message.reply_text(f"قفل {context.args[0]} فعال شد.")


async def unlock_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await owner_only_guard(update):
        return
    if not context.args or context.args[0] not in state["locks"]:
        await update.message.reply_text("استفاده: /unlock links یا forward یا sticker")
        return
    state["locks"][context.args[0]] = False
    save_state(state)
    await update.message.reply_text(f"قفل {context.args[0]} غیرفعال شد.")


# ---------------- هندلر پیام‌های گروه (فیلتر و قفل) ----------------

async def group_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg:
        return

    text = (msg.text or msg.caption or "")

    # فیلتر کلمات
    for word in state["banned_words"]:
        if word and word.lower() in text.lower():
            try:
                await msg.delete()
            except Exception as e:
                log.warning(f"delete failed (need admin rights?): {e}")
            return

    # قفل لینک
    if state["locks"]["links"] and msg.entities:
        for ent in msg.entities:
            if ent.type in ("url", "text_link"):
                try:
                    await msg.delete()
                except Exception:
                    pass
                return

    # قفل فوروارد
    if state["locks"]["forward"] and msg.forward_date:
        try:
            await msg.delete()
        except Exception:
            pass
        return

    # قفل استیکر
    if state["locks"]["sticker"] and msg.sticker:
        try:
            await msg.delete()
        except Exception:
            pass
        return


# ---------------- هندلر پیام خصوصی (منشی) ----------------

async def private_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_owner(update):
        return
    if not state.get("is_online", True):
        await update.message.reply_text(config.AWAY_MESSAGE)


# ---------------- سرور وب کوچک (فقط برای اینکه Render راضی بشه) ----------------

class _HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is running")

    def log_message(self, format, *args):
        pass  # لاگ بی‌مورد رو خاموش می‌کنیم


def run_health_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), _HealthHandler)
    server.serve_forever()


def main():
    # سرور وب رو تو یه ترد جدا اجرا می‌کنیم که Render فکر کنه یه Web Service زنده است
    threading.Thread(target=run_health_server, daemon=True).start()

    app = Application.builder().token(config.BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("online", go_online))
    app.add_handler(CommandHandler("offline", go_offline))
    app.add_handler(CommandHandler("clock", clock_toggle))
    app.add_handler(CommandHandler("addword", add_word))
    app.add_handler(CommandHandler("removeword", remove_word))
    app.add_handler(CommandHandler("listwords", list_words))
    app.add_handler(CommandHandler("lock", lock_cmd))
    app.add_handler(CommandHandler("unlock", unlock_cmd))
    app.add_handler(MessageHandler(filters.ChatType.GROUPS & ~filters.COMMAND, group_message_handler))
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & ~filters.COMMAND, private_message_handler))

    # جاب ساعت هر 5 دقیقه
    app.job_queue.run_repeating(update_clock_job, interval=300, first=5)

    log.info("Bot started.")
    app.run_polling()


if __name__ == "__main__":
    main()
        
