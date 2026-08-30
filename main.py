import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
)

from config import BOT_TOKEN, ADMIN_CHANNEL_ID, CARD_NUMBER, CARD_HOLDER
from database import init_db, get_session, User

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# States for ConversationHandler
(
    FULL_NAME,
    PHONE,
    NATIONAL_ID,
    UNIVERSITY,
    MAJOR,
    MARITAL_STATUS,
    RECEIPT,
) = range(7)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation and asks for the user's full name."""
    user = update.message.from_user
    
    session = get_session()
    # Remove any incomplete registrations for this user
    session.query(User).filter_by(telegram_id=user.id, status="started").delete()
    db_user = User(telegram_id=user.id, status="started")
    session.add(db_user)
    session.commit()
    session.close()

    await update.message.reply_text(
        "سلام! برای ثبت‌نام در رویداد روز طراحی صنعتی هنرهای زیبا دانشگاه تهران، لطفا اطلاعات خود را وارد کنید.\n\n"
        "در هر مرحله برای لغو می‌توانید از دستور /cancel استفاده کنید.\n\n"
        "لطفا نام و نام خانوادگی فرد شرکت‌کننده را وارد کنید:",
        reply_markup=ReplyKeyboardRemove(),
    )
    return FULL_NAME


async def full_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    text = update.message.text

    session = get_session()
    user = session.query(User).filter_by(telegram_id=user_id, status="started").first()
    user.full_name = text
    session.commit()
    session.close()

    await update.message.reply_text("لطفا شماره تماس شرکت‌کننده را وارد کنید:")
    return PHONE


async def phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    text = update.message.text

    session = get_session()
    user = session.query(User).filter_by(telegram_id=user_id, status="started").first()
    user.phone = text
    session.commit()
    session.close()

    await update.message.reply_text("لطفا کدملی شرکت‌کننده را وارد کنید:")
    return NATIONAL_ID


async def national_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    text = update.message.text

    session = get_session()
    user = session.query(User).filter_by(telegram_id=user_id, status="started").first()
    user.national_id = text
    session.commit()
    session.close()

    await update.message.reply_text("لطفا نام دانشگاه شرکت‌کننده را وارد کنید:")
    return UNIVERSITY


async def university(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    text = update.message.text

    session = get_session()
    user = session.query(User).filter_by(telegram_id=user_id, status="started").first()
    user.university = text
    session.commit()
    session.close()

    await update.message.reply_text("لطفا رشته تحصیلی شرکت‌کننده را وارد کنید:")
    return MAJOR


async def major(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    text = update.message.text

    session = get_session()
    user = session.query(User).filter_by(telegram_id=user_id, status="started").first()
    user.major = text
    session.commit()
    session.close()

    reply_keyboard = [["مجرد", "متاهل"]]
    await update.message.reply_text(
        "لطفا وضعیت تاهل شرکت‌کننده را انتخاب کنید:",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, resize_keyboard=True
        ),
    )
    return MARITAL_STATUS


async def marital_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    text = update.message.text

    session = get_session()
    user = session.query(User).filter_by(telegram_id=user_id, status="started").first()
    user.marital_status = text
    session.commit()
    session.close()

    msg = (
        f"اطلاعات با موفقیت دریافت شد.\n\n"
        f"جهت نهایی کردن ثبت‌نام، لطفا مبلغ مورد نظر را به شماره کارت زیر واریز نمایید:\n"
        f"💳 `{CARD_NUMBER}`\n"
        f"👤 به نام: {CARD_HOLDER}\n\n"
        f"سپس عکس یا اسکرین‌شات رسید واریز را در همین چت ارسال کنید."
    )
    await update.message.reply_text(msg, parse_mode='Markdown', reply_markup=ReplyKeyboardRemove())
    return RECEIPT


async def receipt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    photo_file_id = update.message.photo[-1].file_id

    session = get_session()
    user = session.query(User).filter_by(telegram_id=user_id, status="started").first()
    user.receipt_file_id = photo_file_id
    user.status = "pending"
    session.commit()

    # Inform the user
    await update.message.reply_text(
        "رسید شما دریافت شد و برای ادمین‌ها ارسال گردید. "
        "پس از بررسی، نتیجه از طریق همین ربات به شما اعلام خواهد شد.\n"
        "جهت ثبت‌نام فرد دیگر، مجددا /start را بفرستید."
    )

    # Send to admin channel
    admin_text = (
        f"📩 **درخواست ثبت‌نام جدید**\n\n"
        f"👤 نام شرکت‌کننده: {user.full_name}\n"
        f"📞 تماس: {user.phone}\n"
        f"🆔 کدملی: {user.national_id}\n"
        f"🎓 دانشگاه: {user.university}\n"
        f"📚 رشته: {user.major}\n"
        f"💍 وضعیت تاهل: {user.marital_status}\n\n"
        f"آیدی عددی تلگرام: `{user_id}`"
    )

    keyboard = [
        [
            InlineKeyboardButton("✅ تایید", callback_data=f"accept_{user.id}"),
            InlineKeyboardButton("❌ رد", callback_data=f"reject_{user.id}"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if ADMIN_CHANNEL_ID:
        try:
            await context.bot.send_photo(
                chat_id=ADMIN_CHANNEL_ID,
                photo=photo_file_id,
                caption=admin_text,
                parse_mode="Markdown",
                reply_markup=reply_markup,
            )
        except Exception as e:
            logger.error(f"Failed to send message to admin channel: {e}")

    session.close()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "ثبت‌نام لغو شد. هر زمان خواستید می‌توانید با /start مجددا شروع کنید.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Checks the user's registration status."""
    user_id = update.message.from_user.id
    session = get_session()
    users = session.query(User).filter_by(telegram_id=user_id).all()
    session.close()

    if not users:
        await update.message.reply_text("شما هنوز هیچ ثبت‌نامی انجام نداده‌اید. برای شروع از /start استفاده کنید.")
        return

    msg = "وضعیت ثبت‌نام‌های شما:\n\n"
    has_completed_registrations = False

    for u in users:
        if u.status == "started":
            continue
        has_completed_registrations = True
        msg += f"👤 **{u.full_name}**\n"
        if u.status == "pending":
            msg += "وضعیت: ⏳ در حال بررسی رسید\n\n"
        elif u.status == "approved":
            msg += f"وضعیت: ✅ تایید شده\n🎫 کد بلیط: `{u.ticket_code}`\n\n"
        elif u.status == "rejected":
            msg += "وضعیت: ❌ رد شده\n\n"
    
    if not has_completed_registrations:
        msg = "شما ثبت‌نام تکمیلی ندارید. جهت ثبت‌نام جدید از /start شروع کنید."

    await update.message.reply_text(msg, parse_mode="Markdown")


async def post_init(application: Application) -> None:
    """Set the bot commands menu."""
    await application.bot.set_my_commands([
        BotCommand("start", "شروع ثبت‌نام جدید"),
        BotCommand("status", "پیگیری وضعیت ثبت‌نام‌ها و دریافت کد"),
        BotCommand("cancel", "لغو عملیات فعلی")
    ])


async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates message text."""
    query = update.callback_query
    await query.answer()

    data = query.data
    action, db_id_str = data.split("_")
    db_id = int(db_id_str)

    session = get_session()
    user = session.query(User).filter_by(id=db_id).first()

    if not user:
        await query.edit_message_caption(caption="❌ کاربر در دیتابیس یافت نشد.")
        session.close()
        return

    if user.status != "pending":
        await query.edit_message_caption(caption=f"{query.message.caption}\n\n⚠️ این درخواست قبلا بررسی شده است (وضعیت فعلی: {user.status})")
        session.close()
        return

    telegram_user_id = user.telegram_id

    if action == "accept":
        user.status = "approved"
        ticket_code = user.generate_ticket()
        session.commit()
        
        # Notify User
        try:
            user_msg = (
                f"🎉 ثبت‌نام برای **{user.full_name}** با موفقیت تایید شد!\n\n"
                f"🎫 کد پیگیری/بلیط: `{ticket_code}`\n"
                f"لطفا این کد را نزد خود نگه دارید."
            )
            await context.bot.send_message(chat_id=telegram_user_id, text=user_msg, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Failed to notify user {telegram_user_id}: {e}")

        # Update Admin Message
        new_caption = query.message.caption + f"\n\n✅ **تایید شد**\nکد بلیط: {ticket_code}"
        await query.edit_message_caption(caption=new_caption, parse_mode="Markdown", reply_markup=None)

    elif action == "reject":
        user.status = "rejected"
        session.commit()

        # Notify User
        try:
            user_msg = f"❌ متاسفانه رسید پرداختی برای **{user.full_name}** تایید نشد و ثبت‌نام لغو گردید. در صورت نیاز با پشتیبانی تماس بگیرید."
            await context.bot.send_message(chat_id=telegram_user_id, text=user_msg, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Failed to notify user {telegram_user_id}: {e}")

        # Update Admin Message
        new_caption = query.message.caption + "\n\n❌ **رد شد**"
        await query.edit_message_caption(caption=new_caption, parse_mode="Markdown", reply_markup=None)

    session.close()


def main() -> None:
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN is not set in .env")
        return

    init_db()

    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            FULL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, full_name)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, phone)],
            NATIONAL_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, national_id)],
            UNIVERSITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, university)],
            MAJOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, major)],
            MARITAL_STATUS: [MessageHandler(filters.TEXT & ~filters.COMMAND, marital_status)],
            RECEIPT: [MessageHandler(filters.PHOTO, receipt)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CallbackQueryHandler(admin_callback, pattern="^(accept|reject)_"))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
