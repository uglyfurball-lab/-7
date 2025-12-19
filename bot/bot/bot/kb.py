from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from typing import Dict, Any
import asyncio


class ProductPagination:
    def __init__(self):
        self.products = [
            {"id": 1, "name": "Предъявы сверху", "price": 4800, "description": "Порез на собаке", "image": "https://avatars.yandex.net/get-music-content/16450533/bf9db8e0.a.39729616-1/m1000x1000"},
            {"id": 2, "name": "Инцидент с конем", "price": 15000, "description": "Валентин Дядька", "image": "https://images.genius.com/96e0581a3a7c3dc8e2c6f599f8b68d12.300x300x1.png"},
            {"id": 3, "name": "Разговоры с бомжихами", "price": 4200, "description": "Шумные и угрожающие выходки", "image": "https://i.scdn.co/image/ab67616d0000b273c6a9025b22860050a6faacfb"},
            {"id": 4, "name": "Шиношантаж", "price": 2300, "description": "Овсянкин", "image": "https://avatars.yandex.net/get-music-content/9867886/664c1331.a.27009366-1/300x300"},
        ]
        self.user_positions: Dict[int, int] = {}

    def get_product_keyboard(self, current_index: int, user_id: int) -> InlineKeyboardMarkup:
        """Создает клавиатуру для навигации по товарам"""
        total_products = len(self.products)
        self.user_positions[user_id] = current_index

        # Основные кнопки навигации
        navigation_buttons = []

        if current_index > 0:
            navigation_buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"prev_{current_index}"))
        else:
            navigation_buttons.append(InlineKeyboardButton(text="•", callback_data="no_action"))

        navigation_buttons.append(InlineKeyboardButton(
            text=f"{current_index + 1}/{total_products}",
            callback_data="page_info"
        ))

        if current_index < total_products - 1:
            navigation_buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"next_{current_index}"))
        else:
            navigation_buttons.append(InlineKeyboardButton(text="•", callback_data="no_action"))

        # Дополнительные кнопки
        action_buttons = [
            InlineKeyboardButton(text="🛒 Забронировать", callback_data=f"buy_{self.products[current_index]['id']}"),
            InlineKeyboardButton(text="⭐ В избранное", callback_data=f"favorite_{self.products[current_index]['id']}")
        ]

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            navigation_buttons,
            action_buttons,
            [InlineKeyboardButton(text="🏠 Главная", callback_data="main_menu")]
        ])

        return keyboard

    def format_product_message(self, product: Dict[str, Any], current_index: int) -> str:
        """Форматирует сообщение с информацией о товаре"""
        total_products = len(self.products)
        return (
            f"🏷 <b>{product['name']}</b>\n"
            f"💰 Цена: <b>{product['price']} руб.</b>\n"
            f"📝 {product['description']}\n"
            f"\n📄 Страница <b>{current_index + 1}</b> из <b>{total_products}</b>"
        )


# Создаем экземпляр пагинатора
product_pagination = ProductPagination()


async def start_command(message: types.Message, bot: Bot):
    """Обработчик команды /start"""
    await show_product(bot, message.chat.id, message.from_user.id)


async def show_product(bot: Bot, chat_id: int, user_id: int, product_index: int = 0):
    """Показывает товар с навигацией"""
    products = product_pagination.products

    if product_index >= len(products):
        product_index = 0

    product = products[product_index]
    message_text = product_pagination.format_product_message(product, product_index)
    keyboard = product_pagination.get_product_keyboard(product_index, user_id)

    # Если есть изображение, отправляем с фото
    if product.get('image'):
        await bot.send_photo(
            chat_id=chat_id,
            photo=product['image'],
            caption=message_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    else:
        await bot.send_message(
            chat_id=chat_id,
            text=message_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )


async def handle_product_navigation(callback: types.CallbackQuery, bot: Bot):
    """Обработчик навигации по товарам"""
    user_id = callback.from_user.id
    data = callback.data

    try:
        if data.startswith("prev_"):
            current_index = int(data.split("_")[1])
            new_index = current_index - 1
            if new_index >= 0:
                await update_product_message(callback, new_index)
            else:
                await callback.answer("Это первый товар!")

        elif data.startswith("next_"):
            current_index = int(data.split("_")[1])
            new_index = current_index + 1
            if new_index < len(product_pagination.products):
                await update_product_message(callback, new_index)
            else:
                await callback.answer("Это последний товар!")

        elif data.startswith("buy_"):
            product_id = int(data.split("_")[1])
            await callback.answer(f"Товар {product_id} добавлен в корзину!")

        elif data.startswith("favorite_"):
            product_id = int(data.split("_")[1])
            await callback.answer(f"Товар {product_id} добавлен в избранное!")

        elif data == "main_menu":
            await callback.message.delete()
            await show_product(bot, callback.message.chat.id, user_id)

        elif data == "no_action":
            await callback.answer()

        else:
            await callback.answer("Неизвестная команда")

    except Exception as e:
        await callback.answer("Произошла ошибка, попробуйте снова")
        print(f"Error: {e}")


async def update_product_message(callback: types.CallbackQuery, product_index: int):
    """Обновляет сообщение с товаром"""
    product = product_pagination.products[product_index]
    message_text = product_pagination.format_product_message(product, product_index)
    keyboard = product_pagination.get_product_keyboard(product_index, callback.from_user.id)

    try:
        await callback.message.edit_text(
            text=message_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    except Exception as e:
        # Если не удалось отредактировать сообщение (например, из-за изменения типа контента)
        await callback.message.delete()
        await show_product(callback.bot, callback.message.chat.id, callback.from_user.id, product_index)

