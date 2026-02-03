from datetime import datetime
from aiogram import types
from aiogram.dispatcher import FSMContext
from loader import dp, db_manager
from source.keyboard import inline
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

USERS_PER_PAGE = 50  # Кол-во пользователей на страницу


async def show_global_stats(call: types.CallbackQuery, state: FSMContext, page: int = 1):
    # Получаем всех разблокированных пользователей с количеством конфигов и бонусов
    query = """
        SELECT 
            u.user_id,
            u.username,
            u.subscription_end_date,
            COALESCE(b.bonus_config_count, 0) AS bonus_configs,
            COUNT(v.id) AS created_configs
        FROM users u
        LEFT JOIN vpn_configs v ON v.user_id = u.user_id
        LEFT JOIN bonus_configs_for_users b ON b.user_id = u.user_id
        WHERE u.is_banned = FALSE
        GROUP BY u.user_id, b.bonus_config_count
    """
    users_records = await db_manager._execute_query(query)

    users = []
    active_count = 0
    inactive_count = 0
    today = datetime.now().date()

    for record in users_records:
        user_id, username, subscription_end_date, bonus_configs, created_configs = record
        total_configs = created_configs + bonus_configs

        if subscription_end_date >= today:
            active_count += 1
            days_left = (subscription_end_date - today).days
            days_text = f"{days_left} день(дней)" if days_left != 1 else "1 день"
            days_sort = days_left
            status_emoji = "🟢"
        else:
            inactive_count += 1
            days_text = "истекла"
            days_sort = -1
            status_emoji = "🔴"

        users.append({
            "user_id": user_id,
            "username": username or f"user_{user_id}",
            "configs_count": total_configs,
            "days_left": days_text,
            "days_sort": days_sort,
            "status_emoji": status_emoji
        })

    # Сортировка пользователей по количеству оставшихся дней (от наименьшего к наибольшему)
    users.sort(key=lambda x: x["days_sort"])

    # Пагинация
    total_pages = (len(users) + USERS_PER_PAGE - 1) // USERS_PER_PAGE
    start_index = (page - 1) * USERS_PER_PAGE
    end_index = start_index + USERS_PER_PAGE
    users_page = users[start_index:end_index]

    # Формируем текст сообщения с кликабельными именами
    lines = [
        f"📊 Всего пользователей: {len(users)} ({active_count} с активной подпиской / {inactive_count} неактивны)\n"
        f"Страница {page}/{total_pages}\n"
    ]
    for i, user in enumerate(users_page, start=start_index + 1):
        user_link = f"<a href='tg://user?id={user['user_id']}'>{user['username']}</a>"
        lines.append(
            f"{i}. {user['status_emoji']} {user_link} - {user['configs_count']} конфиг(ов) - {user['days_left']}"
        )

    text = "\n".join(lines)

    # Генерируем inline-кнопки для пагинации
    markup = await inline.insert_button_back_to_main_menu(language_code=call.from_user.language_code)
    if total_pages > 1:
        pagination_markup = InlineKeyboardMarkup(row_width=5)
        buttons = [InlineKeyboardButton(text=str(p), callback_data=f"stats_page_{p}") for p in range(1, total_pages + 1)]
        pagination_markup.add(*buttons)
        # Добавляем кнопку "Назад" под пагинацией
        for row in markup.inline_keyboard:
            for btn in row:
                pagination_markup.add(btn)
        markup = pagination_markup

    await call.message.edit_text(
        text=text,
        parse_mode=types.ParseMode.HTML,
        reply_markup=markup
    )


# Обработчик callback для пагинации
@dp.callback_query_handler(lambda c: c.data and c.data.startswith("stats_page_"))
async def stats_pagination_handler(call: types.CallbackQuery, state: FSMContext):
    page = int(call.data.split("_")[-1])
    await show_global_stats(call, state, page=page)
