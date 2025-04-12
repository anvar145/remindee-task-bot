import sqlite3
import logging

logger = logging.getLogger(__name__)

# Добавление задачи
def add_task(user_id, task, deadline):
    conn = sqlite3.connect("tasks.db")
    c = conn.cursor()
    c.execute(
        "INSERT INTO tasks (user_id, task, deadline, status) VALUES (?, ?, ?, ?)",
        (user_id, task, deadline, "pending"),
    )
    conn.commit()
    conn.close()

# Получение задач
def get_tasks(user_id):
    conn = sqlite3.connect("tasks.db")
    c = conn.cursor()
    c.execute("SELECT id, task, deadline, status FROM tasks WHERE user_id = ? ORDER BY id", (user_id,))
    tasks = c.fetchall()
    conn.close()
    return tasks

# Удаление задачи и пересчёт ID
def delete_task(task_id, user_id):
    conn = sqlite3.connect("tasks.db")
    c = conn.cursor()

    # Удаляем задачу
    c.execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id))

    # Получаем все задачи пользователя после удаления, отсортированные по ID
    c.execute("SELECT id, user_id, task, deadline, status FROM tasks WHERE user_id = ? ORDER BY id", (user_id,))
    remaining_tasks = c.fetchall()

    # Если задач больше нет, просто сохраняем изменения и выходим
    if not remaining_tasks:
        conn.commit()
        conn.close()
        return

    # Создаём временную таблицу
    c.execute(
        """CREATE TABLE temp_tasks (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            task TEXT,
            deadline TEXT,
            status TEXT
        )"""
    )

    # Переносим задачи с обновлёнными ID
    new_id = 1
    for task in remaining_tasks:
        old_id, user_id, task_text, deadline, status = task
        c.execute(
            "INSERT INTO temp_tasks (id, user_id, task, deadline, status) VALUES (?, ?, ?, ?, ?)",
            (new_id, user_id, task_text, deadline, status),
        )
        new_id += 1

    # Удаляем старую таблицу и переименовываем временную
    c.execute("DROP TABLE tasks")
    c.execute("ALTER TABLE temp_tasks RENAME TO tasks")

    conn.commit()
    conn.close()