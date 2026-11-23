"""Telegram-бот подборщика ЖК. Запуск: BOT_TOKEN=... python bot/bot.py
Токен получите у @BotFather. Не коммитьте токен в репозиторий.
"""
import logging
import os

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (Application, CommandHandler, ContextTypes, ConversationHandler,
                          MessageHandler, filters)

from matcher import format_matches, normalize_city, pick

logging.basicConfig(level=logging.INFO)
CITY, BUDGET, AREA = range(3)
CITIES = [["Сочи", "Москва", "Санкт-Петербург"]]


def _num(text: str) -> float:
    """Понимает '45000000', '45 000 000', '45млн', '45 млн', '45,5 млн'."""
    t = text.lower().replace(" ", "").replace(",", ".")
    mult = 1
    for suffix, m in (("млн", 1e6), ("тыс", 1e3), ("к", 1e3)):
        if t.endswith(suffix):
            t, mult = t[: -len(suffix)], m
            break
    return float(t) * mult


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Подберу 3 ЖК бизнес/премиум-класса. В каком городе ищем?",
        reply_markup=ReplyKeyboardMarkup(CITIES, one_time_keyboard=True, resize_keyboard=True))
    return CITY


async def city(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    c = normalize_city(update.message.text)
    if not c:
        await update.message.reply_text("Выберите: Сочи, Москва или Санкт-Петербург.")
        return CITY
    ctx.user_data["city"] = c
    await update.message.reply_text("Бюджет на квартиру? Например: 45 млн", reply_markup=ReplyKeyboardRemove())
    return BUDGET


async def budget(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        b = _num(update.message.text)
        assert b > 0
    except Exception:
        await update.message.reply_text("Не понял сумму. Пример: 45 млн или 45000000")
        return BUDGET
    ctx.user_data["budget"] = b
    await update.message.reply_text("Желаемая площадь, м²? Например: 60")
    return AREA


async def area(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        a = _num(update.message.text.replace("м²", "").replace("м2", ""))
        assert 10 <= a <= 1000
    except Exception:
        await update.message.reply_text("Не понял площадь. Пример: 60")
        return AREA
    d = ctx.user_data
    await update.message.reply_text(format_matches(pick(d["city"], d["budget"], a), d["city"], d["budget"], a),
                                    disable_web_page_preview=True)
    await update.message.reply_text("Чтобы подобрать заново — /start")
    return ConversationHandler.END


async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отменено. /start — начать заново.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def main():
    # Необязательный прокси (если VPN работает как локальный прокси): PROXY_URL=http://127.0.0.1:7890
    from telegram.request import HTTPXRequest
    proxy = os.environ.get("PROXY_URL")
    kw = dict(proxy=proxy, connect_timeout=30, read_timeout=30, write_timeout=30, pool_timeout=30)
    app = (Application.builder().token(os.environ["BOT_TOKEN"])
           .request(HTTPXRequest(**kw)).get_updates_request(HTTPXRequest(**kw)).build())
    t = filters.TEXT & ~filters.COMMAND
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={CITY: [MessageHandler(t, city)], BUDGET: [MessageHandler(t, budget)],
                AREA: [MessageHandler(t, area)]},
        fallbacks=[CommandHandler("cancel", cancel), CommandHandler("start", start)]))
    app.run_polling(bootstrap_retries=-1)  # при 429/сетевых сбоях при старте ждём и пробуем снова


if __name__ == "__main__":
    main()
