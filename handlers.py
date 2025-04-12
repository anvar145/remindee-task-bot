# /start, /restart и button_handler
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from bot.keyboards import get_main_keyboard, get_cancel_keyboard
from bot.tasks import get_tasks, add_task, delete_task
from datetime import datetime

# Логгер
logger = logging.getLogger(__name__)

# Состояния для диалога
TASK_TEXT, TASK_DEADLINE = range(2)

# Удаление старого меню и отправка нового
async def update_main_menu(context: ContextTypes.DEFAULT_TYPE, chat_id: int, text: str):
    # Удаляем старое главное меню, если оно существует
    if "main_message_id" in context.user_data:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=context.user_data["main_message_id"])
            logger.info(f"Удалено старое главное меню с ID {context.user_data['main_message_id']}")
        except Exception as e:
            logger.warning(f"Не удалось удалить старое главное меню: {e}")
    # Удаляем промежуточное сообщение с "Отмена", если оно есть
    if "cancel_message_id" in context.user_data:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=context.user_data["cancel_message_id"])
            logger.info(f"Удалено промежуточное сообщение с ID {context.user_data['cancel_message_id']}")
        except Exception as e:
            logger.warning(f"Не удалось удалить промежуточное сообщение: {e}")
        context.user_data.pop("cancel_message_id", None)
    # Отправляем новое меню и обновляем ID
    new_message = await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=get_main_keyboard())
    context.user_data["main_message_id"] = new_message.message_id
    logger.info(f"Новое главное меню отправлено с ID {new_message.message_id}")

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update_main_menu(context, update.effective_chat.id,
                           "Привет! 😊 Я твой помощник по задачам. Что хочешь сделать?")

# Команда /restart
async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat_id = update.effective_chat.id

    # Удаляем старые сообщения, если есть
    if "main_message_id" in context.user_data:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=context.user_data["main_message_id"])
        except Exception as e:
            logger.warning(f"Не удалось удалить main_message: {e}")
        context.user_data.pop("main_message_id", None)

    if "cancel_message_id" in context.user_data:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=context.user_data["cancel_message_id"])
        except Exception as e:
            logger.warning(f"Не удалось удалить cancel_message: {e}")
        context.user_data.pop("cancel_message_id", None)

    context.user_data.clear()
    await update_main_menu(context, chat_id, "Бот перезапущен. Что хочешь сделать? 🤖")
    return ConversationHandler.END

# Обработчик кнопок
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if not query:
        return ConversationHandler.END
    await query.answer()
    chat_id = update.effective_chat.id
    callback_data = query.data

    # Логируем нажатие кнопки
    logger.info(f"Нажата кнопка с callback_data: {callback_data}")

    if callback_data == "add_task":
        # Удаляем старое сообщение с "Отмена", если оно есть
        if "cancel_message_id" in context.user_data:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=context.user_data["cancel_message_id"])
                logger.info(f"Удалено промежуточное сообщение с ID {context.user_data['cancel_message_id']}")
            except Exception as e:
                logger.warning(f"Не удалось удалить промежуточное сообщение: {e}")
            context.user_data.pop("cancel_message_id", None)
        # Отправляем новое сообщение
        message = await context.bot.send_message(
            chat_id=chat_id,
            text="Отлично! Напиши, какую задачу ты хочешь добавить. Например: 'Сделать отчет'.",
            reply_markup=get_cancel_keyboard(),
        )
        context.user_data["cancel_message_id"] = message.message_id
        return TASK_TEXT
    elif callback_data == "list_tasks":
        user_id = query.from_user.id
        tasks = get_tasks(user_id)
        if not tasks:
            await update_main_menu(context, chat_id, "У тебя пока нет задач! 😌 Хочешь добавить новую?")
        else:
            response = "Твои задачи:\n\n"
            for task in tasks:
                task_id, task_text, deadline, status = task
                # Преобразуем дедлайн в ДД.ММ.ГГГГ ЧЧ:ММ для отображения
                deadline_dt = datetime.strptime(deadline, "%Y-%m-%d %H:%M")
                deadline_formatted = deadline_dt.strftime("%d.%m.%Y %H:%M")
                response += f"🆔 {task_id} | {task_text}\n⏰ Дедлайн: {deadline_formatted}\n📌 Статус: {status}\n\n"
            await update_main_menu(context, chat_id, response)
        return ConversationHandler.END
    elif callback_data == "delete_task":
        user_id = query.from_user.id
        tasks = get_tasks(user_id)
        if not tasks:
            await update_main_menu(context, chat_id, "У тебя нет задач для удаления! 😌 Хочешь добавить новую?")
            return ConversationHandler.END
        # Удаляем старое сообщение с "Отмена"
        if "cancel_message_id" in context.user_data:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=context.user_data["cancel_message_id"])
                logger.info(f"Удалено промежуточное сообщение с ID {context.user_data['cancel_message_id']}")
            except Exception as e:
                logger.warning(f"Не удалось удалить промежуточное сообщение: {e}")
            context.user_data.pop("cancel_message_id", None)
        # Отправляем новое сообщение
        response = "Выбери задачу для удаления (укажи ID):\n\n"
        for task in tasks:
            task_id, task_text, deadline, status = task
            # Преобразуем дедлайн в ДД.ММ.ГГГГ ЧЧ:ММ для отображения
            deadline_dt = datetime.strptime(deadline, "%Y-%m-%d %H:%M")
            deadline_formatted = deadline_dt.strftime("%d.%m.%Y %H:%M")
            response += f"🆔 {task_id} | {task_text} | Дедлайн: {deadline_formatted}\n"
        message = await context.bot.send_message(chat_id=chat_id, text=response, reply_markup=get_cancel_keyboard())
        context.user_data["cancel_message_id"] = message.message_id
        context.user_data["delete_mode"] = True
        return ConversationHandler.END
    elif callback_data == "cancel":
        await update_main_menu(context, chat_id, "Действие отменено. Что хочешь сделать?")
        context.user_data["delete_mode"] = False
        return ConversationHandler.END
    else:
        logger.warning(f"Неизвестный callback_data: {callback_data}")
        return ConversationHandler.END

# Обработчик ввода текста задачи
async def task_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["task_text"] = update.message.text
    chat_id = update.effective_chat.id
    # Удаляем старое сообщение с "Отмена"
    if "cancel_message_id" in context.user_data:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=context.user_data["cancel_message_id"])
            logger.info(f"Удалено промежуточное сообщение с ID {context.user_data['cancel_message_id']}")
        except Exception as e:
            logger.warning(f"Не удалось удалить промежуточное сообщение: {e}")
        context.user_data.pop("cancel_message_id", None)
    # Отправляем новое сообщение
    message = await context.bot.send_message(
        chat_id=chat_id,
        text="Супер! Теперь укажи дедлайн в формате ДД.ММ.ГГГГ ЧЧ:ММ, например: 15.04.2025 14:00",
        reply_markup=get_cancel_keyboard(),
    )
    context.user_data["cancel_message_id"] = message.message_id
    return TASK_DEADLINE

# Обработчик ввода дедлайна
async def task_deadline(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    deadline_str = update.message.text
    chat_id = update.effective_chat.id

    try:
        # Парсим дату в формате ДД.ММ.ГГГГ ЧЧ:ММ
        deadline = datetime.strptime(deadline_str, "%d.%m.%Y %H:%M")
        # Преобразуем дату в формат для хранения (ГГГГ-ММ-ДД ЧЧ:ММ)
        deadline_formatted = deadline.strftime("%Y-%m-%d %H:%M")
        task = context.user_data["task_text"]
        add_task(user_id, task, deadline_formatted)
        await update_main_menu(context, chat_id, f"Задача '{task}' добавлена с дедлайном {deadline_str}! 🎉 Что дальше?")
        return ConversationHandler.END
    except ValueError:
        # Удаляем старое сообщение с "Отмена"
        if "cancel_message_id" in context.user_data:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=context.user_data["cancel_message_id"])
                logger.info(f"Удалено промежуточное сообщение с ID {context.user_data['cancel_message_id']}")
            except Exception as e:
                logger.warning(f"Не удалось удалить промежуточное сообщение: {e}")
            context.user_data.pop("cancel_message_id", None)
        # Отправляем новое сообщение
        message = await context.bot.send_message(
            chat_id=chat_id,
            text="Кажется, формат дедлайна неверный. 😔 Попробуй снова: ДД.ММ.ГГГГ ЧЧ:ММ",
            reply_markup=get_cancel_keyboard(),
        )
        context.user_data["cancel_message_id"] = message.message_id
        return TASK_DEADLINE
    except Exception as e:
        logger.error(f"Ошибка при добавлении задачи: {e}")
        # Удаляем старое сообщение с "Отмена"
        if "cancel_message_id" in context.user_data:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=context.user_data["cancel_message_id"])
                logger.info(f"Удалено промежуточное сообщение с ID {context.user_data['cancel_message_id']}")
            except Exception as e:
                logger.warning(f"Не удалось удалить промежуточное сообщение: {e}")
            context.user_data.pop("cancel_message_id", None)
        # Отправляем новое сообщение
        message = await context.bot.send_message(
            chat_id=chat_id,
            text="Ой, что-то пошло не так. 😢 Попробуй еще раз!",
            reply_markup=get_cancel_keyboard(),
        )
        context.user_data["cancel_message_id"] = message.message_id
        return TASK_DEADLINE

# Обработчик удаления задачи
async def delete_task_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.user_data.get("delete_mode"):
        return
    user_id = update.message.from_user.id
    chat_id = update.effective_chat.id

    try:
        task_id = int(update.message.text)
        tasks = get_tasks(user_id)
        if any(task[0] == task_id for task in tasks):
            delete_task(task_id, user_id)
            await update_main_menu(context, chat_id, f"Задача с ID {task_id} удалена! ✅ Что дальше?")
        else:
            # Удаляем старое сообщение с "Отмена"
            if "cancel_message_id" in context.user_data:
                try:
                    await context.bot.delete_message(chat_id=chat_id, message_id=context.user_data["cancel_message_id"])
                    logger.info(f"Удалено промежуточное сообщение с ID {context.user_data['cancel_message_id']}")
                except Exception as e:
                    logger.warning(f"Не удалось удалить промежуточное сообщение: {e}")
                context.user_data.pop("cancel_message_id", None)
            # Отправляем новое сообщение
            message = await context.bot.send_message(
                chat_id=chat_id,
                text="Такого ID нет. 😔 Проверь список задач и попробуй снова.",
                reply_markup=get_cancel_keyboard(),
            )
            context.user_data["cancel_message_id"] = message.message_id
    except ValueError:
        # Удаляем старое сообщение с "Отмена"
        if "cancel_message_id" in context.user_data:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=context.user_data["cancel_message_id"])
                logger.info(f"Удалено промежуточное сообщение с ID {context.user_data['cancel_message_id']}")
            except Exception as e:
                logger.warning(f"Не удалось удалить промежуточное сообщение: {e}")
            context.user_data.pop("cancel_message_id", None)
        # Отправляем новое сообщение
        message = await context.bot.send_message(
            chat_id=chat_id,
            text="Пожалуйста, укажи ID задачи числом. Например: 1",
            reply_markup=get_cancel_keyboard(),
        )
        context.user_data["cancel_message_id"] = message.message_id
    except Exception as e:
        logger.error(f"Ошибка при удалении задачи: {e}")
        # Удаляем старое сообщение с "Отмена"
        if "cancel_message_id" in context.user_data:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=context.user_data["cancel_message_id"])
                logger.info(f"Удалено промежуточное сообщение с ID {context.user_data['cancel_message_id']}")
            except Exception as e:
                logger.warning(f"Не удалось удалить промежуточное сообщение: {e}")
            context.user_data.pop("cancel_message_id", None)
        # Отправляем новое сообщение
        message = await context.bot.send_message(
            chat_id=chat_id,
            text="Ой, что-то пошло не так. 😢 Попробуй еще раз!",
            reply_markup=get_cancel_keyboard(),
        )
        context.user_data["cancel_message_id"] = message.message_id
    else:
        context.user_data["delete_mode"] = False