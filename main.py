import logging
import re
import qrcode
import io
import pandas as pd
import os
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

from config import BOT_TOKEN, ADMIN_CHANNEL_ID, CARD_NUMBER, CARD_HOLDER, ADMIN_USER_IDS, SUPPORT_ID
from database import init_db, get_session, User, Workshop, user_workshops, Setting

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

(
    FULL_NAME, PHONE, NATIONAL_ID, UNIVERSITY, MAJOR, WORKSHOP, RECEIPT,
    AW_NAME, AW_CAPACITY, AW_DATE, AW_TIME, AW_PRICE, AW_LIMIT
) = range(13)

def unify_numbers(text: str) -> str:
    if not text: return text
    persian_to_eng = str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789')
    arabic_to_eng = str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')
    return text.translate(persian_to_eng).translate(arabic_to_eng)

def is_valid_national_id(nid: str) -> bool:
    if not re.match(r'^\d{10}$', nid):
        return False
    check = int(nid[9])
    s = sum(int(nid[x]) * (10 - x) for x in range(9)) % 11
    return check == s if s < 2 else check + s == 11

async def generate_workshop_keyboard(user_id: int, session) -> InlineKeyboardMarkup:
    user = session.query(User).filter_by(telegram_id=user_id, status="started").first()
    workshops = session.query(Workshop).filter_by(is_open=True).all()
    keyboard = []
    
    selected_ids = [w.id for w in user.workshops]
    
    for w in workshops:
        current_count = session.query(user_workshops).filter_by(workshop_id=w.id).count()
        is_full = current_count >= w.capacity
        
        status_icon = "✅ " if w.id in selected_ids else ""
        label_prefix = "[رزرو] " if is_full and w.id not in selected_ids else ""
        
        text = f"{status_icon}{label_prefix}{w.name} | {w.date} | {w.time} ({current_count}/{w.capacity})"
        keyboard.append([InlineKeyboardButton(text, callback_data=f"ws_toggle_{w.id}")])
    
    keyboard.append([InlineKeyboardButton("➡️ تایید و ادامه", callback_data="ws_done")])
    return InlineKeyboardMarkup(keyboard)

# --- USER REGISTRATION FLOW ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    session = get_session()
    
    total_approved_pending = session.query(User).filter(User.status.in_(["pending", "approved"])).count()
    limit_setting = session.query(Setting).filter_by(key="total_capacity").first()
    
    if limit_setting:
        max_capacity = int(limit_setting.value)
        if total_approved_pending >= max_capacity:
            await update.message.reply_text(
                "ظرفیت رویداد در حال حاضر تکمیل شده است. به زودی ظرفیت جدید ایجاد خواهد شد، لطفاً چند ساعت دیگر مجدداً بررسی کنید.",
                reply_markup=ReplyKeyboardRemove()
            )
            session.close()
            return ConversationHandler.END

    user = update.message.from_user
    session.query(User).filter_by(telegram_id=user.id, status="started").delete()
    db_user = User(telegram_id=user.id, status="started")
    session.add(db_user)
    session.commit()
    session.close()

    await update.message.reply_text(
        "سلام! برای ثبت‌نام در رویداد روز طراحی صنعتی هنرهای زیبا دانشگاه تهران، لطفا اطلاعات خود را وارد کنید.\n\n"
        "لطفا نام و نام خانوادگی فرد شرکت‌کننده را وارد کنید:",
        reply_markup=ReplyKeyboardRemove(),
    )
    return FULL_NAME

async def full_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    session = get_session()
    user = session.query(User).filter_by(telegram_id=user_id, status="started").first()
    user.full_name = update.message.text
    session.commit()
    session.close()
    await update.message.reply_text("لطفا شماره تماس شرکت‌کننده را وارد کنید (مانند 09123456789):")
    return PHONE

async def phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    cleaned_phone = unify_numbers(update.message.text)
    if not re.match(r'^09\d{9}$', cleaned_phone):
        await update.message.reply_text("شماره تماس نامعتبر است. لطفا یک شماره صحیح وارد کنید:")
        return PHONE

    user_id = update.message.from_user.id
    session = get_session()
    user = session.query(User).filter_by(telegram_id=user_id, status="started").first()
    user.phone = cleaned_phone
    session.commit()
    session.close()
    await update.message.reply_text("لطفا کدملی شرکت‌کننده را وارد کنید:")
    return NATIONAL_ID

async def national_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    cleaned_nid = unify_numbers(update.message.text)
    if not is_valid_national_id(cleaned_nid):
        await update.message.reply_text("کدملی نامعتبر است. لطفا مجددا وارد کنید:")
        return NATIONAL_ID

    user_id = update.message.from_user.id
    session = get_session()
    user = session.query(User).filter_by(telegram_id=user_id, status="started").first()
    user.national_id = cleaned_nid
    session.commit()
    session.close()
    await update.message.reply_text("لطفا نام دانشگاه شرکت‌کننده را وارد کنید:")
    return UNIVERSITY

async def university(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    session = get_session()
    user = session.query(User).filter_by(telegram_id=user_id, status="started").first()
    user.university = update.message.text
    session.commit()
    session.close()
    await update.message.reply_text("لطفا رشته تحصیلی شرکت‌کننده را وارد کنید:")
    return MAJOR

async def major(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    session = get_session()
    user = session.query(User).filter_by(telegram_id=user_id, status="started").first()
    user.major = update.message.text
    session.commit()
    
    markup = await generate_workshop_keyboard(user_id, session)
    session.close()

    msg = (
        "اطلاعات ثبت شد.\n"
        "لطفا کارگاه‌های مورد نظر خود را انتخاب کنید (می‌توانید چند مورد را انتخاب کنید):\n\n"
        "⚠️ توجه: شما باید ۴۵ الی ۶۰ دقیقه قبل از شروع کارگاه برای پذیرش حضور داشته باشید، در غیر این صورت ظرفیت شما به شخص دیگری واگذار خواهد شد.\n\n"
        f"☎️ در صورت بروز مشکل به آیدی {SUPPORT_ID} پیام دهید."
    )
    
    await update.message.reply_text(msg, reply_markup=markup)
    return WORKSHOP

async def workshop_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    session = get_session()
    user = session.query(User).filter_by(telegram_id=user_id, status="started").first()

    if data == "ws_done":
        if not user.workshops:
            await query.answer("شما باید حداقل یک کارگاه را انتخاب کنید!", show_alert=True)
            session.close()
            return WORKSHOP
        
        setting = session.query(Setting).filter_by(key="ticket_price").first()
        price = setting.value if setting else "300,000"
        
        msg = (
            f"جهت نهایی کردن ثبت‌نام، لطفا مبلغ ({price} تومان) را به کارت زیر واریز نمایید:\n"
            f"💳 `{CARD_NUMBER}`\n👤 به نام: {CARD_HOLDER}\n\n"
            f"سپس عکس یا اسکرین‌شات رسید را بفرستید."
        )
        await query.edit_message_text(text=msg, parse_mode='Markdown')
        session.close()
        return RECEIPT

    if data.startswith("ws_toggle_"):
        ws_id = int(data.split("_")[2])
        w = session.query(Workshop).get(ws_id)
        
        if w in user.workshops:
            user.workshops.remove(w)
        else:
            conflict = any(ew.date == w.date and ew.time == w.time for ew in user.workshops)
            if conflict:
                await query.answer("تداخل زمانی! نمی‌توانید دو کارگاه همزمان انتخاب کنید.", show_alert=True)
            else:
                user.workshops.append(w)
        
        session.commit()
        markup = await generate_workshop_keyboard(user_id, session)
        await query.edit_message_reply_markup(reply_markup=markup)
        
    session.close()
    return WORKSHOP

async def receipt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    photo_file_id = update.message.photo[-1].file_id
    
    session = get_session()
    user = session.query(User).filter_by(telegram_id=user_id, status="started").first()
    user.receipt_file_id = photo_file_id
    user.status = "pending"
    session.commit()

    await update.message.reply_text("رسید شما دریافت شد. نتیجه پس از بررسی ادمین اعلام می‌شود.")

    workshops_text = "\n".join([f"- {w.name} ({w.date} {w.time})" for w in user.workshops])
    
    admin_text = (
        f"📩 **درخواست ثبت‌نام جدید**\n\n"
        f"👤 نام: {user.full_name}\n"
        f"📞 تماس: {user.phone}\n"
        f"🆔 کدملی: {user.national_id}\n"
        f"🎓 دانشگاه: {user.university}\n"
        f"📚 رشته: {user.major}\n"
        f"🛠 **کارگاه‌های انتخابی:**\n{workshops_text}\n\n"
        f"آیدی تلگرام: `{user_id}`"
    )

    keyboard = [
        [InlineKeyboardButton("✅ تایید", callback_data=f"accept_{user.id}"), InlineKeyboardButton("❌ رد", callback_data=f"reject_{user.id}")]
    ]
    
    if ADMIN_CHANNEL_ID:
        try:
            await context.bot.send_photo(
                chat_id=ADMIN_CHANNEL_ID, photo=photo_file_id, caption=admin_text,
                parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            logger.error(f"Admin channel send error: {e}")

    session.close()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("عملیات لغو شد.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# --- ADMIN FEATURES ---

async def admin_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if str(user_id) not in ADMIN_USER_IDS: return
    
    keyboard = [
        [InlineKeyboardButton("📊 آمار لحظه‌ای", callback_data="dash_stats")],
        [InlineKeyboardButton("📥 خروجی اکسل", callback_data="dash_export")],
        [InlineKeyboardButton("🛠 مدیریت کارگاه‌ها", callback_data="dash_workshops")],
        [InlineKeyboardButton("🏷 تغییر قیمت ثبت‌نام", callback_data="dash_price")],
        [InlineKeyboardButton("👥 تغییر ظرفیت کل رویداد", callback_data="dash_limit")]
    ]
    await update.message.reply_text("🎛️ **پنل مدیریت ربات**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def perform_export(chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
    session = get_session()
    query = "SELECT id, telegram_id, full_name, phone, national_id, university, major, status, ticket_code FROM users WHERE status != 'started'"
    df = pd.read_sql_query(query, session.bind)
    
    users = session.query(User).filter(User.status != 'started').all()
    user_ws_map = {u.id: " | ".join([w.name for w in u.workshops]) for u in users}
    df['workshops'] = df['id'].map(user_ws_map)
    session.close()

    df = df.rename(columns={
        'id': 'ردیف', 'telegram_id': 'آیدی تلگرام', 'full_name': 'نام و نام خانوادگی',
        'phone': 'شماره تماس', 'national_id': 'کد ملی', 'university': 'دانشگاه',
        'major': 'رشته تحصیلی', 'workshops': 'کارگاه‌ها', 'status': 'وضعیت ثبت‌نام', 'ticket_code': 'کد بلیط'
    })
    
    df['وضعیت ثبت‌نام'] = df['وضعیت ثبت‌نام'].map({'pending':'در بررسی', 'approved':'تایید شده', 'rejected':'رد شده'}).fillna(df['وضعیت ثبت‌نام'])

    df.to_excel("registrations.xlsx", index=False)
    with open("registrations.xlsx", "rb") as f:
        await context.bot.send_document(chat_id=chat_id, document=f, caption="📥 خروجی اکسل ثبت‌نام‌ها")
    os.remove("registrations.xlsx")

async def dashboard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if str(query.from_user.id) not in ADMIN_USER_IDS:
        await query.answer("شما دسترسی ندارید.", show_alert=True)
        return
    await query.answer()
    data = query.data

    if data == "dash_stats":
        session = get_session()
        total_approved = session.query(User).filter_by(status="approved").count()
        setting = session.query(Setting).filter_by(key="ticket_price").first()
        price = int(unify_numbers(setting.value)) if setting else 300000
        
        session.close()
        await query.edit_message_text(f"📊 **آمار قطعی:** `{total_approved}` نفر\nمبلغ تخمینی: `{total_approved * price}` تومان", parse_mode="Markdown")
    elif data == "dash_export":
        await query.edit_message_text("⏳ در حال تولید فایل اکسل...")
        await perform_export(query.message.chat_id, context)
    elif data == "dash_workshops":
        keyboard = [
            [InlineKeyboardButton("➕ افزودن کارگاه", callback_data="dash_add_ws")],
            [InlineKeyboardButton("📋 لیست کارگاه‌ها", callback_data="dash_list_ws")],
        ]
        await query.edit_message_text("مدیریت کارگاه‌ها:", reply_markup=InlineKeyboardMarkup(keyboard))
    elif data == "dash_list_ws":
        session = get_session()
        workshops = session.query(Workshop).all()
        keyboard = []
        for w in workshops:
            status = "✅" if w.is_open else "❌"
            keyboard.append([InlineKeyboardButton(f"{status} {w.name}", callback_data=f"mws_{w.id}")])
        session.close()
        await query.edit_message_text("لیست کارگاه‌ها (برای مدیریت کلیک کنید):", reply_markup=InlineKeyboardMarkup(keyboard))
    elif data.startswith("mws_toggle_"):
        ws_id = int(data.split("_")[2])
        session = get_session()
        w = session.query(Workshop).get(ws_id)
        w.is_open = not w.is_open
        session.commit()
        session.close()
        await query.edit_message_text("وضعیت کارگاه تغییر کرد.")
    elif data.startswith("mws_delete_"):
        ws_id = int(data.split("_")[2])
        session = get_session()
        w = session.query(Workshop).get(ws_id)
        session.delete(w)
        session.commit()
        session.close()
        await query.edit_message_text("کارگاه حذف شد.")
    elif data.startswith("mws_"):
        ws_id = int(data.split("_")[1])
        session = get_session()
        w = session.query(Workshop).get(ws_id)
        keyboard = [
            [InlineKeyboardButton("باز/بسته کردن ثبت‌نام", callback_data=f"mws_toggle_{w.id}")],
            [InlineKeyboardButton("حذف کارگاه", callback_data=f"mws_delete_{w.id}")],
            [InlineKeyboardButton("بازگشت", callback_data="dash_list_ws")]
        ]
        await query.edit_message_text(f"کارگاه {w.name}\nظرفیت: {w.capacity}\nزمان: {w.date} {w.time}", reply_markup=InlineKeyboardMarkup(keyboard))
        session.close()

# --- ADMIN CONVERSATION FLOW (PRICE & WORKSHOPS) ---
async def admin_add_ws_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("نام کارگاه را وارد کنید:")
    return AW_NAME

async def admin_add_ws_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['aw_name'] = update.message.text
    await update.message.reply_text("ظرفیت کارگاه را وارد کنید (فقط عدد):")
    return AW_CAPACITY

async def admin_add_ws_capacity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    cap_str = unify_numbers(update.message.text)
    if not cap_str.isdigit():
        await update.message.reply_text("لطفا فقط عدد وارد کنید:")
        return AW_CAPACITY
        
    context.user_data['aw_capacity'] = int(cap_str)
    await update.message.reply_text("تاریخ کارگاه را وارد کنید (مثال: 1405/06/30):")
    return AW_DATE

async def admin_add_ws_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['aw_date'] = update.message.text
    await update.message.reply_text("زمان کارگاه را وارد کنید (مثال: 13:00-15:00):")
    return AW_TIME

async def admin_add_ws_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    time_str = update.message.text
    session = get_session()
    w = Workshop(
        name=context.user_data['aw_name'],
        capacity=context.user_data['aw_capacity'],
        date=context.user_data['aw_date'],
        time=time_str
    )
    session.add(w)
    session.commit()
    session.close()
    await update.message.reply_text("✅ کارگاه با موفقیت اضافه شد!")
    return ConversationHandler.END

async def admin_price_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("لطفا مبلغ جدید ثبت‌نام را (مثلا 400000) وارد کنید:")
    return AW_PRICE

async def admin_price_save(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    price_str = unify_numbers(update.message.text)
    session = get_session()
    setting = session.query(Setting).filter_by(key="ticket_price").first()
    if not setting:
        setting = Setting(key="ticket_price", value=price_str)
        session.add(setting)
    else:
        setting.value = price_str
    session.commit()
    session.close()
    await update.message.reply_text(f"✅ قیمت با موفقیت به {price_str} تومان تغییر یافت.")
    return ConversationHandler.END

async def admin_limit_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("لطفا ظرفیت کل رویداد را وارد کنید (مثلا 100):")
    return AW_LIMIT

async def admin_limit_save(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    limit_str = unify_numbers(update.message.text)
    if not limit_str.isdigit():
        await update.message.reply_text("لطفا فقط عدد وارد کنید:")
        return AW_LIMIT
        
    session = get_session()
    setting = session.query(Setting).filter_by(key="total_capacity").first()
    if not setting:
        setting = Setting(key="total_capacity", value=limit_str)
        session.add(setting)
    else:
        setting.value = limit_str
    session.commit()
    session.close()
    await update.message.reply_text(f"✅ ظرفیت کل رویداد با موفقیت به {limit_str} نفر تغییر یافت.")
    return ConversationHandler.END

# --- CORE & INITS ---

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    session = get_session()
    users = session.query(User).filter_by(telegram_id=user_id).all()
    
    if not users or all(u.status == "started" for u in users):
        await update.message.reply_text("شما هنوز هیچ ثبت‌نامی ندارید. از /start شروع کنید.")
        session.close()
        return

    msg = "وضعیت ثبت‌نام‌های شما:\n\n"
    for u in users:
        if u.status == "started": continue
        msg += f"👤 **{u.full_name}**\n"
        ws_list = "، ".join([w.name for w in u.workshops])
        msg += f"🛠 کارگاه‌ها: {ws_list}\n"
        if u.status == "pending": msg += "وضعیت: ⏳ در حال بررسی رسید\n\n"
        elif u.status == "approved": msg += f"وضعیت: ✅ تایید شده\n🎫 کد بلیط: `{u.ticket_code}`\n\n"
        elif u.status == "rejected": msg += "وضعیت: ❌ رد شده\n\n"
    session.close()
    await update.message.reply_text(msg, parse_mode="Markdown")

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data
    action, db_id = data.split("_")[0], int(data.split("_")[1])
    
    session = get_session()
    user = session.query(User).filter_by(id=db_id).first()
    
    if action == "accept":
        user.status = "approved"
        code = user.generate_ticket()
        session.commit()
        
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(code)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        bio = io.BytesIO()
        bio.name = 'ticket.png'
        img.save(bio, 'PNG')
        bio.seek(0)
        
        await context.bot.send_photo(chat_id=user.telegram_id, photo=bio, caption=f"🎉 تایید شد!\n🎫 کد بلیط: `{code}`", parse_mode="Markdown")
        await query.edit_message_caption(caption=query.message.caption + f"\n\n✅ تایید شد\nکد: {code}")
        
    elif action == "reject":
        user.status = "rejected"
        session.commit()
        await context.bot.send_message(chat_id=user.telegram_id, text="❌ متاسفانه رسید شما تایید نشد.")
        await query.edit_message_caption(caption=query.message.caption + "\n\n❌ رد شد")
    
    session.close()

def main() -> None:
    init_db()
    application = Application.builder().token(BOT_TOKEN).build()

    user_conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            FULL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, full_name)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, phone)],
            NATIONAL_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, national_id)],
            UNIVERSITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, university)],
            MAJOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, major)],
            WORKSHOP: [CallbackQueryHandler(workshop_selection, pattern="^ws_")],
            RECEIPT: [MessageHandler(filters.PHOTO, receipt)],
        },
        fallbacks=[CommandHandler("cancel", cancel), CommandHandler("start", start)],
    )
    
    admin_ws_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(admin_add_ws_start, pattern="^dash_add_ws$"),
            CallbackQueryHandler(admin_price_start, pattern="^dash_price$"),
            CallbackQueryHandler(admin_limit_start, pattern="^dash_limit$")
        ],
        states={
            AW_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_ws_name)],
            AW_CAPACITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_ws_capacity)],
            AW_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_ws_date)],
            AW_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_ws_time)],
            AW_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_price_save)],
            AW_LIMIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_limit_save)],
        },
        fallbacks=[CommandHandler("cancel", cancel), CommandHandler("start", start)],
    )

    application.add_handler(user_conv)
    application.add_handler(admin_ws_conv)
    application.add_handler(CommandHandler("status", status_cmd))
    application.add_handler(CommandHandler("admin", admin_dashboard))
    application.add_handler(CallbackQueryHandler(dashboard_callback, pattern="^(dash_|mws_)"))
    application.add_handler(CallbackQueryHandler(admin_callback, pattern="^(accept|reject)_"))

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
