from aiogram import types
from aiogram.dispatcher import FSMContext

from loader import db_manager
from source.keyboard import inline
from source.middlewares import rate_limit
from source.utils import localizer

from .check_is_user_banned import is_user_banned


@rate_limit(limit=1)
@is_user_banned
async def show_referral_info(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    referrals_count = await db_manager.get_referrals_count_by_referrer(user_id=call.from_user.id)
    bot_username = call.bot.username
    referral_link = f"https://t.me/{bot_username}?start={call.from_user.id}"

    await call.message.answer(
        text=localizer.get_user_localized_text(
            user_language_code=call.from_user.language_code,
            text_localization=localizer.message.referral_info,
        ).format(
            referral_link=referral_link,
            referrals_count=referrals_count,
        ),
        parse_mode=types.ParseMode.HTML,
        reply_markup=await inline.insert_button_back_to_main_menu(
            language_code=call.from_user.language_code
        ),
    )
