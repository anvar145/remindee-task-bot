import sqlite3
import logging
from telegram.ext import ContextTypes
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Функция проверки дедлайнов
async def check_deadlines(context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect("tasks.db")
    c = conn.cursor()
    now = datetime.now()
    c.execute("SELECT user_id, task, deadline FROM tasks WHERE status = 'pending'")
    tasks = c.fetchall()

    for user_id, task, deadline_str in tasks:
        try:
            deadline = datetime.strptime(deadline_str, "%Y-%m-%d %H:%M")
            if now >= deadline - timedelta(minutes=10) and now < deadline:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"⏰ Напоминание: задача '{task}' должна быть выполнена к {deadline_str}!",
                )
                c.execute(
                    "UPDATE tasks SET status = 'notified' WHERE user_id = ? AND task = ?",
                    (user_id, task),
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Ошибка при проверке дедлайна: {e}")

    conn.close()