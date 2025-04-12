from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Главное меню
def get_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("Добавить задачу 📝", callback_data="add_task")],
        [InlineKeyboardButton("Посмотреть задачи 📋", callback_data="list_tasks")],
        [InlineKeyboardButton("Удалить задачу 🗑️", callback_data="delete_task")],
    ]
    return InlineKeyboardMarkup(keyboard)

# Клавиатура с кнопкой "Отмена"
def get_cancel_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("Отмена 🚫", callback_data="cancel")]])