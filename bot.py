import logging
import os
import csv
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Загрузка переменных среды
load_dotenv()

# Конфигурация
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
CSV_HEADER = ["Дата", "ID пользователя", "Самочувствие", "Активность", "Настроение", "Открытый вопрос 1", "Открытый вопрос 2"]

# Инициализация логгера
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=LOG_LEVEL,
    handlers=[
        logging.FileHandler("./logs/bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Состояния диалога
(
    CHOOSING_ACTION,
    ASK_SAMOCHUVSTVIE_1,
    ASK_SAMOCHUVSTVIE_2,
    ASK_ACTIVITY_1,
    ASK_ACTIVITY_2,
    ASK_MOOD_1,
    ASK_MOOD_2,
    ASK_OPEN_1,
    ASK_OPEN_2
) = range(9)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[KeyboardButton(btn)] for btn in ["Тест", "Ретроспектива", "Помощь"]]
    await update.message.reply_text(
        "Добро пожаловать! Выберите действие:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return CHOOSING_ACTION

async def handle_test_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    handlers = {
        CHOOSING_ACTION: choose_action,
        ASK_SAMOCHUVSTVIE_1: ask_samochuvstvie_1,
        ASK_SAMOCHUVSTVIE_2: ask_samochuvstvie_2,
        ASK_ACTIVITY_1: ask_activity_1,
        ASK_ACTIVITY_2: ask_activity_2,
        ASK_MOOD_1: ask_mood_1,
        ASK_MOOD_2: ask_mood_2,
        ASK_OPEN_1: ask_open_1,
        ASK_OPEN_2: ask_open_2
    }
    return await handlers[context.user_data.get('step', CHOOSING_ACTION)](update, context)

async def save_and_show_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = context.user_data
    
    try:
        scores = {key: int(data[key]) for key in ["samo_1", "samo_2", "act_1", "act_2", "mood_1", "mood_2"]}
        if any(not (1 <= v <= 7) for v in scores.values()):
            raise ValueError
    except (ValueError, KeyError):
        await update.message.reply_text("Ошибка: ответы должны быть числами от 1 до 7")
        context.user_data.clear()
        return

    # Расчет средних значений
    averages = {
        "Самочувствие": (scores["samo_1"] + scores["samo_2"]) / 2,
        "Активность": (scores["act_1"] + scores["act_2"]) / 2,
        "Настроение": (scores["mood_1"] + scores["mood_2"]) / 2
    }

    # Сохранение в CSV
    filename = f"./data/user_{user_id}.csv"
    try:
        with open(filename, "a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            if not os.path.isfile(filename) or os.stat(filename).st_size == 0:
                writer.writerow(CSV_HEADER)
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                user_id,
                *averages.values(),
                data.get("open_1", ""),
                data.get("open_2", "")
            ])
    except IOError as e:
        logger.error(f"Ошибка записи в CSV: {e}")
        await update.message.reply_text("Ошибка сохранения результатов")
        return

    # Формирование отчета
    report = "\n".join(
        f"{k}: {v:.1f} - {interpret_score(v)}"
        for k, v in averages.items()
    )
    await update.message.reply_text(f"{report}\n\nРекомендация: {get_recommendation(averages)}")
    context.user_data.clear()
    return await start_command(update, context)

def interpret_score(score: float) -> str:
    if score >= 5: return "Отлично"
    if score >= 3: return "Средне"
    return "Низкий уровень"

def get_recommendation(averages: dict) -> str:
    avg = sum(averages.values()) / 3
    return (
        "Продолжайте в том же духе!" if avg >= 5 else
        "Нужны улучшения" if avg >= 3 else
        "Требуются изменения"
    )

# Остальные обработчики вопросов остаются без изменений (ask_samochuvstvie_1, ask_activity_1 и т.д.)

def main():
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start_command)],
        states={
            state: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_test_flow)]
            for state in [
                CHOOSING_ACTION, ASK_SAMOCHUVSTVIE_1, ASK_SAMOCHUVSTVIE_2,
                ASK_ACTIVITY_1, ASK_ACTIVITY_2, ASK_MOOD_1, ASK_MOOD_2,
                ASK_OPEN_1, ASK_OPEN_2
            ]
        },
        fallbacks=[CommandHandler("start", start_command)],
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == "__main__":
    # Создаем необходимые директории при запуске
    os.makedirs("./data", exist_ok=True)
    os.makedirs("./logs", exist_ok=True)
    main()
