import logging
import os
from datetime import datetime
import requests
import pandas as pd

from dotenv import load_dotenv
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Загружаем переменные среды из .env (если используется)
load_dotenv()

# Инициализируем нужные переменные окружения
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Проверяем, что токен Telegram-бота задан
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("Не указан TELEGRAM_BOT_TOKEN в окружении или .env")

# Настраиваем логирование
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=LOG_LEVEL,
    handlers=[
        logging.FileHandler("./logs/bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Определяем шаги ConversationHandler
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
    """
    Обработчик команды /start – формирует главное меню.
    """
    user_id = update.effective_user.id
    logger.info("Пользователь %s отправил /start", user_id)

    keyboard = [
        [KeyboardButton("Тест")],
        [KeyboardButton("Ретроспектива")],
        [KeyboardButton("Помощь")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "Добро пожаловать! Выберите действие:",
        reply_markup=reply_markup
    )
    return CHOOSING_ACTION


async def choose_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает выбор: Тест / Ретроспектива / Помощь.
    """
    user_text = update.message.text
    user_id = update.effective_user.id
    logger.info("Пользователь %s выбрал: %s", user_id, user_text)

    if user_text == "Тест":
        await update.message.reply_text(
            "Начнём тест.\n"
            "Оцените своё физическое состояние (самочувствие) по шкале от 1 до 7."
        )
        return ASK_SAMOCHUVSTVIE_1

    elif user_text == "Ретроспектива":
        # Заглушка — здесь может быть логика просмотра прошлых результатов
        await update.message.reply_text("Функция 'Ретроспектива' в разработке.")
        return await start_command(update, context)

    elif user_text == "Помощь":
        help_text = (
            "Этот бот помогает отслеживать ваше состояние по трем категориям:\n"
            "1. Самочувствие\n2. Активность\n3. Настроение\n\n"
            "Пройдите тест, и бот сохранит результаты и предоставит простые рекомендации."
        )
        await update.message.reply_text(help_text)
        return await start_command(update, context)

    else:
        await update.message.reply_text("Пожалуйста, используйте кнопки в меню.")
        return CHOOSING_ACTION


# --------------- ВОПРОСЫ О САМОЧУВСТВИИ ---------------
async def ask_samochuvstvie_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["samo_1"] = update.message.text
    await update.message.reply_text(
        "Чувствуете ли вы себя бодрым/здоровым? (1–7)"
    )
    return ASK_SAMOCHUVSTVIE_2


async def ask_samochuvstvie_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["samo_2"] = update.message.text
    await update.message.reply_text(
        "Чувствуете ли вы себя энергичным? (1–7)"
    )
    return ASK_ACTIVITY_1


# --------------- ВОПРОСЫ ОБ АКТИВНОСТИ ---------------
async def ask_activity_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["act_1"] = update.message.text
    await update.message.reply_text(
        "Чувствуете ли вы усталость или необходимость отдохнуть? (1–7)"
    )
    return ASK_ACTIVITY_2


async def ask_activity_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["act_2"] = update.message.text
    await update.message.reply_text(
        "Как вы оцениваете своё настроение сейчас? (1–7)"
    )
    return ASK_MOOD_1


# --------------- ВОПРОСЫ О НАСТРОЕНИИ ---------------
async def ask_mood_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mood_1"] = update.message.text
    await update.message.reply_text(
        "Чувствуете ли вы себя позитивно или негативно? (1–7)"
    )
    return ASK_MOOD_2


async def ask_mood_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mood_2"] = update.message.text
    await update.message.reply_text(
        "Какие три слова лучше всего описывают ваше текущее состояние?"
    )
    return ASK_OPEN_1


# --------------- ОТКРЫТЫЕ ВОПРОСЫ ---------------
async def ask_open_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["open_1"] = update.message.text
    await update.message.reply_text(
        "Что больше всего повлияло на ваше состояние сегодня?"
    )
    return ASK_OPEN_2


async def ask_open_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["open_2"] = update.message.text

    # Сохраняем результат и показываем пользователю
    await save_and_show_result(update, context)

    # Возвращаемся в главное меню
    return await start_command(update, context)


# --------------- СОХРАНЕНИЕ ДАННЫХ / ВЫВОД ---------------
async def save_and_show_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Сохраняет данные в CSV и выводит итоговую оценку/рекомендацию.
    """
    user_id = update.effective_user.id
    data = context.user_data

    try:
        # Пытаемся преобразовать ответы в целые числа
        samo_1 = int(data.get("samo_1", "0"))
        samo_2 = int(data.get("samo_2", "0"))
        act_1 = int(data.get("act_1", "0"))
        act_2 = int(data.get("act_2", "0"))
        mood_1 = int(data.get("mood_1", "0"))
        mood_2 = int(data.get("mood_2", "0"))
    except ValueError:
        await update.message.reply_text(
            "Ошибка: ответы на шкалу должны быть числами от 1 до 7.\n"
            "Попробуйте заново, введя валидные числа."
        )
        context.user_data.clear()
        return

    # Дополнительно можно проверить, что числа в диапазоне [1..7]
    for val in (samo_1, samo_2, act_1, act_2, mood_1, mood_2):
        if not (1 <= val <= 7):
            await update.message.reply_text(
                "Ошибка: ответы должны быть в диапазоне 1–7.\n"
                "Попробуйте тест заново."
            )
            context.user_data.clear()
            return

    # Считаем среднее
    samo_avg = (samo_1 + samo_2) / 2
    act_avg = (act_1 + act_2) / 2
    mood_avg = (mood_1 + mood_2) / 2

    open_1 = data.get("open_1", "")
    open_2 = data.get("open_2", "")

    # Путь к файлу CSV
    filename = f"./data/user_{user_id}.csv"
    file_exists = os.path.isfile(filename)

    # Формируем запись
    row = {
        "Дата": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ID пользователя": user_id,
        "Самочувствие (1-7)": samo_avg,
        "Активность (1-7)": act_avg,
        "Настроение (1-7)": mood_avg,
        "Открытый вопрос 1": open_1,
        "Открытый вопрос 2": open_2
    }
    df = pd.DataFrame([row])

    # Сохраняем в CSV (если файла нет — создаём заново, иначе — дописываем)
    if not file_exists:
        df.to_csv(filename, index=False, encoding="utf-8")
    else:
        df.to_csv(filename, index=False, mode="a", header=False, encoding="utf-8")

    # Выводим текст интерпретации
    samo_text = interpret_score(samo_avg, "Самочувствие")
    act_text = interpret_score(act_avg, "Активность")
    mood_text = interpret_score(mood_avg, "Настроение")

    # Простая логика общей рекомендации
    general_avg = (samo_avg + act_avg + mood_avg) / 3
    if general_avg >= 5:
        recommendation = "Общее состояние хорошее. Продолжайте в том же духе!"
    elif general_avg >= 3:
        recommendation = "Неплохо, но есть куда улучшаться. Обратите внимание на отдых и режим."
    else:
        recommendation = "Есть проблемы. Стоит пересмотреть сон, питание и снизить стресс."

    result_text = (
        f"{samo_text}\n{act_text}\n{mood_text}\n\n"
        f"Общая рекомендация: {recommendation}"
    )

    await update.message.reply_text(result_text)
    # Очищаем данные из user_data (чтобы при следующем тесте начинать с чистого листа)
    context.user_data.clear()


def interpret_score(score: float, category: str) -> str:
    """
    Простейшая интерпретация числового показателя.
    """
    score_rounded = round(score, 1)
    if score_rounded >= 5:
        return f"{category}: {score_rounded} — Отличный уровень!"
    elif score_rounded >= 3:
        return f"{category}: {score_rounded} — Средний показатель, есть пространство для улучшений."
    else:
        return f"{category}: {score_rounded} — Низковато, уделите внимание здоровью и отдыху."


def get_gemini_response(prompt_text: str) -> str:
    """
    Пример обращения к Google Gemini (Generative Language API).
    Возвращает сгенерированный текст (или None в случае ошибки).
    """
    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY не задан. Невозможно обратиться к Gemini API.")
        return None

    url = (
        "https://generativelanguage.googleapis.com/"
        "v1beta2/models/gemini-1.5-flash:generateContent"
        f"?key={GEMINI_API_KEY}"
    )
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [
            {"parts": [{"text": prompt_text}]}
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        # Структура ответа может отличаться в зависимости от версии API
        generated_text = (
            data.get("contents", [{}])[0]
            .get("parts", [{}])[0]
            .get("text", "")
        )
        return generated_text
    except Exception as e:
        logger.error("Ошибка при запросе к Gemini API: %s", e)
        return None


def main():
    """
    Точка входа в приложение. Создаём бота, регистрируем ConversationHandler.
    """
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start_command)],
        states={
            CHOOSING_ACTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, choose_action)
            ],
            ASK_SAMOCHUVSTVIE_1: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ask_samochuvstvie_1)
            ],
            ASK_SAMOCHUVSTVIE_2: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ask_samochuvstvie_2)
            ],
            ASK_ACTIVITY_1: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ask_activity_1)
            ],
            ASK_ACTIVITY_2: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ask_activity_2)
            ],
            ASK_MOOD_1: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ask_mood_1)
            ],
            ASK_MOOD_2: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ask_mood_2)
            ],
            ASK_OPEN_1: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ask_open_1)
            ],
            ASK_OPEN_2: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ask_open_2)
            ],
        },
        fallbacks=[CommandHandler("start", start_command)],
    )

    application.add_handler(conv_handler)

    # Запускаем бота (поллинг)
    application.run_polling()


if __name__ == "__main__":
    main()

