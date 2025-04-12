import logging
from telegram.ext import Application, CommandHandler, ConversationHandler
from bot.handlers import start, restart, button_handler, task_text, task_deadline, delete_task_handler
from bot.reminders import check_deadlines
from bot.database import init_db

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния для диалога
TASK_TEXT, TASK_DEADLINE = range(2)

def main() -> None:
    # Инициализация базы данных
    init_db()

    # Инициализация бота
    application = Application.builder().token("YOUR_BOT_TOKEN").build()

    if application.job_queue is None:
        logger.error("JobQueue не инициализирован! Установите 'python-telegram-bot[job-queue]'")
        return

    # Определяем ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("restart", restart),
        ],
        states={
            TASK_TEXT: [button_handler, task_text],
            TASK_DEADLINE: [button_handler, task_deadline],
        },
        fallbacks=[button_handler],
        per_message=False,
    )

    # Добавляем обработчики
    application.add_handler(conv_handler)
    application.add_handler(delete_task_handler)

    # Настройка периодической проверки дедлайнов
    application.job_queue.run_repeating(check_deadlines, interval=60, first=10)

    # Запуск бота
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()