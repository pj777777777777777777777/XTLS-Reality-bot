from aiogram import types
from aiogram.dispatcher import FSMContext

from loader import db_manager
from source.keyboard import inline
from source.utils import localizer


async def show_referral_stats(call: types.CallbackQuery, state: FSMContext):
    referral_stats = await db_manager.get_referral_stats()
    if referral_stats.top_referrers:
        unknown_username_label = (
            "без username" if call.from_user.language_code == "ru" else "no username"
        )
        top_lines = []
        for index, top_user in enumerate(referral_stats.top_referrers, start=1):
            username = f"@{top_user.username}" if top_user.username else unknown_username_label
            top_lines.append(
                f"{index}. {username} (id: <code>{top_user.user_id}</code>) — "
                f"<b>{top_user.referrals_count}</b>"
            )
        top_referrers_text = "\n".join(top_lines)
    else:
        top_referrers_text = "—"

    await call.message.edit_text(
        text=localizer.get_user_localized_text(
            user_language_code=call.from_user.language_code,
            text_localization=localizer.message.referral_stats,
        ).format(
            total_referrals=referral_stats.total_referrals,
            total_bonus_awarded=referral_stats.total_bonus_awarded,
            top_referrers=top_referrers_text,
        ),
        parse_mode=types.ParseMode.HTML,
        reply_markup=await inline.insert_button_back_to_main_menu(
            language_code=call.from_user.language_code,
        ),
    )
