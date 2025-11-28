import asyncio
from aiogram import Router, F, Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import logging
from aiogram.enums import ParseMode
from db import Database

API_TOKEN = '7661300607:AAH7rk985DaZqUWJ2JZR1imnwQO8ACbVDlg'

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)
db = Database()


# Состояния для ввода данных
class UserRegistration(StatesGroup):
    waiting_for_first_name = State()
    waiting_for_last_name = State()
    waiting_for_email = State()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Начало регистрации - запрашиваем имя"""
    await message.answer(
        "Добро пожаловать! Пройдите регистрацию.\n\n"
        "Ваше имя:"
    )
    await state.set_state(UserRegistration.waiting_for_first_name)


@router.message(UserRegistration.waiting_for_first_name)
async def process_first_name(message: Message, state: FSMContext):
    """Получили имя, запрашиваем фамилию"""
    first_name = message.text.strip()
    await state.update_data(first_name=first_name)
    await message.answer(
        f"Имя «{first_name}» сохранено!\n\n"
        "Ваша фамилия:"
    )
    await state.set_state(UserRegistration.waiting_for_last_name)


@router.message(UserRegistration.waiting_for_last_name)
async def process_last_name(message: Message, state: FSMContext):
    """Получили фамилию, запрашиваем email"""
    last_name = message.text.strip()
    await state.update_data(last_name=last_name)
    await message.answer(
        "Фамилия сохранена!\n\n"
        "Ваш email:"
    )
    await state.set_state(UserRegistration.waiting_for_email)


@router.message(UserRegistration.waiting_for_email)
async def process_email(message: Message, state: FSMContext):
    """Получили email, сохраняем все данные"""
    try:
        email = message.text.strip()
        logging.info(f"Получен email: {email}")

        # Проверяем email
        if "@" not in email or "." not in email:
            await message.answer(
                "Это не похоже на email. Попробуй еще раз:\n"
                "Пример: vasha_pochta@mail.ru"
            )
            return

        # Достаем все сохраненные данные
        user_data = await state.get_data()
        logging.info(f"Данные из state: {user_data}")

        # Добавляем проверку на наличие данных
        if not user_data.get('first_name') or not user_data.get('last_name'):
            await message.answer(
                "Произошла ошибка: данные не найдены. "
                "Пожалуйста, начните регистрацию заново с /start"
            )
            await state.clear()
            return

        # Сохраняем пользователя в базу данных
        logging.info(f"Пытаемся сохранить пользователя {message.from_user.id} в БД")
        success = await db.add_user(
            user_id=message.from_user.id,
            first_name=user_data['first_name'],
            last_name=user_data['last_name'],
            email=email
        )
        logging.info(f"Результат сохранения: {success}")

        if success:
            result_text = (
                "✅ Регистрация завершена!\n\n"
                f"Имя: {user_data['first_name']}\n"
                f"Фамилия: {user_data['last_name']}\n"
                f"Email: {email}\n\n"
                "Используйте /profile чтобы посмотреть свой профиль"
            )
        else:
            result_text = "Произошла ошибка при сохранении данных."

        await message.answer(result_text)
        await state.clear()

    except Exception as e:
        logging.error(f"Критическая ошибка в process_email: {e}", exc_info=True)
        await message.answer("Произошла ошибка. Попробуйте начать заново с /start")
        await state.clear()


@router.message(Command("profile"))
async def cmd_profile(message: Message):
    """Показать профиль пользователя"""
    user_data = await db.get_user(message.from_user.id)

    if not user_data:
        await message.answer(
            "Вы еще не зарегистрированы!\n"
            "Напишите /start чтобы начать регистрацию"
        )
        return

    profile_text = (
        "Ваш профиль:\n\n"
        f"Имя: {user_data['first_name']}\n"
        f"Фамилия: {user_data['last_name']}\n"
        f"Email: {user_data['email']}\n"
        f"ID: {user_data['user_id']}\n"
        f"Дата регистрации: {user_data['created_at']}"
    )

    await message.answer(profile_text)


@router.message(Command("update"))
async def cmd_update(message: Message):
    """Обновить данные"""
    await message.answer(
        "Чтобы обновить данные, просто пройдите регистрацию заново:\n"
        "Напишите /start"
    )


# Добавляем обработчик для всех остальных сообщений
@router.message()
async def handle_other_messages(message: Message):
    await message.answer("Используйте /start для регистрации")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())