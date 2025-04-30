import os
import logging
from telegram import Update, CallbackQuery, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    ContextTypes, ConversationHandler, CallbackContext, CallbackQueryHandler
)
from datetime import datetime, timedelta
from telegram.constants import ChatMemberStatus
from database import init_db, add_user, increase_file_count, get_file_count, increase_file_request, file_exists

TOKEN = '7413532622:AAFfd_ctt4Xb055CqQxct64anIUTHhagW4M'
CHANNEL_USERNAME = '@hottof'
CHANNEL_NAME = 'تُفِ داغ'
CHANNEL_USERNAME_SECONDARY = '@tofhot'
CHANNEL_NAME_SECONDARY = 'زاپاس تف'
ADMINS = [6387942633]

WAITING_FOR_MEDIA, WAITING_FOR_CAPTION, WAITING_FOR_ACTION, WAITING_FOR_SCHEDULE = range(4)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def handle_start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args

    from database import add_user
    add_user(user_id)

    if not args:
        # اگه بدون آرگومان بود
        if user_id in ADMINS:
            return await start(update, context)  # نمایش پنل برای ادمین
        else:
            await update.message.reply_text('به ربات خوش آمدید.')
            return

    # اگه با آرگومان فایل بود
    file_id = args[0]
    not_joined = await check_membership(user_id, context.bot)
    if not_joined:
        buttons = [
            [InlineKeyboardButton("تُفِ داغ", url=f'https://t.me/{CHANNEL_USERNAME[1:]}')],
            [InlineKeyboardButton("زاپاس تف", url=f'https://t.me/{CHANNEL_USERNAME_SECONDARY[1:]}')],
            [InlineKeyboardButton("عضو شدم", callback_data=f"check_{file_id}")]
        ]
        markup = InlineKeyboardMarkup(buttons)
        await update.message.reply_text('برای دریافت فایل، در یکی از کانال‌ها عضو شوید:', reply_markup=markup)
    else:
        await send_and_delete(file_id, update, context)

    keyboard = [['۱ سوپر', '۲ پست', '۳ آمار']]
    await update.message.reply_text('به پنل خوش آمدید.', reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return WAITING_FOR_MEDIA

async def handle_panel_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from database import get_active_user_counts
    text = update.message.text
    if text == '۱ سوپر':
        await update.message.reply_text('یک ویدیو ارسال کن.')
        return WAITING_FOR_MEDIA
    elif text == '۲ پست':
        await update.message.reply_text('یک پیام فوروارد کن.')
        return WAITING_FOR_CAPTION
    elif text == '۳ آمار':
        now = datetime.now()
        stats = get_active_user_counts()
        await update.message.reply_text(
            f'🤖 آمار شما در ساعت {now.strftime("%H:%M:%S")} و تاریخ {now.strftime("%Y/%m/%d")} به این صورت می‌باشد\n\n'
            f'👥 تعداد اعضا : {stats["total"]}\n'
            f'🕒 کاربران ساعت گذشته : {stats["hour"]}\n'
            f'☪️ کاربران ۲۴ ساعت گذشته : {stats["day"]}\n'
            f'7️⃣ کاربران هفته گذشته : {stats["week"]}\n'
            f'🌛 کاربران ماه گذشته : {stats["month"]}\n'
            f'🗂 تعداد فایل‌ها : {get_file_count()}'
        )
        return WAITING_FOR_MEDIA
    return WAITING_FOR_MEDIA

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.video:
        await update.message.reply_text('فقط ویدیو قابل قبول است.')
        return WAITING_FOR_MEDIA
    context.user_data['video'] = update.message.video.file_id
    await update.message.reply_text('حالا لطفاً کاور (عکس) را ارسال کنید.')
    return WAITING_FOR_CAPTION

async def handle_cover(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text('فقط تصویر قابل قبول است.')
        return WAITING_FOR_CAPTION
    context.user_data['cover'] = update.message.photo[-1].file_id
    await update.message.reply_text('کپشن را وارد کنید:')
    return WAITING_FOR_ACTION

async def handle_caption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['caption'] = update.message.text
    file_id = context.user_data['video']
    cover_id = context.user_data['cover']
    caption = context.user_data['caption']
    preview_caption = f'{caption}\n\n@hottof | تُفِ داغ'
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('مشاهده', url=f'https://t.me/{context.bot.username}?start={file_id}')]])
    await update.message.reply_photo(cover_id, caption=preview_caption, reply_markup=keyboard)
    context.user_data['preview_caption'] = preview_caption
    context.user_data['inline_keyboard'] = keyboard
    reply_keyboard = [['ارسال در کانال حالا', 'ارسال در آینده'], ['لغو', 'برگشت به پنل اصلی']]
    await update.message.reply_text('ارسال شود یا زمان‌بندی شود؟', reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True))
    return WAITING_FOR_SCHEDULE

async def handle_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == 'ارسال در کانال حالا':
        await send_to_channel(context)
        await update.message.reply_text('ارسال شد.', reply_markup=ReplyKeyboardRemove())
        return WAITING_FOR_MEDIA
    elif text == 'ارسال در آینده':
        await update.message.reply_text('زمان ارسال را به دقیقه وارد کنید:')
        return 100
    elif text == 'برگشت به پنل اصلی':
        return await start(update, context)
    elif text == 'لغو':
        await update.message.reply_text('لغو شد.', reply_markup=ReplyKeyboardRemove())
        return WAITING_FOR_MEDIA
    return WAITING_FOR_SCHEDULE

async def handle_timer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        minutes = int(update.message.text)
        context.job_queue.run_once(send_to_channel_job, when=timedelta(minutes=minutes), data=context.user_data.copy())
        await update.message.reply_text('زمان‌بندی شد.', reply_markup=ReplyKeyboardRemove())
        return WAITING_FOR_MEDIA
    except:
        await update.message.reply_text('عدد وارد کنید.')
        return 100

async def send_to_channel(context):
    from database import add_file_if_not_exists
    data = context.user_data
    file_id = data['video']
    add_file_if_not_exists(file_id)
    await context.bot.send_photo(chat_id=CHANNEL_USERNAME, photo=data['cover'], caption=data['preview_caption'], reply_markup=data['inline_keyboard'])

async def send_to_channel_job(context: CallbackContext):
    await send_to_channel(context)

async def check_membership(user_id: int, bot) -> list:
    not_joined = []
    for ch in [CHANNEL_USERNAME, CHANNEL_USERNAME_SECONDARY]:
        member = await bot.get_chat_member(chat_id=ch, user_id=user_id)
        if member.status not in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            not_joined.append(ch)
    return not_joined

async def handle_start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from database import add_user
    args = context.args
    if not args:
        await update.message.reply_text('برای استفاده از ربات روی لینک "مشاهده" در پست کلیک کنید.')
        return
    file_id = args[0]
    add_user(update.effective_user.id)
    not_joined = await check_membership(update.effective_user.id, context.bot)
    if not_joined:
        buttons = [
            [InlineKeyboardButton("تُفِ داغ", url=f'https://t.me/{CHANNEL_USERNAME[1:]}')],
            [InlineKeyboardButton("زاپاس تف", url=f'https://t.me/{CHANNEL_USERNAME_SECONDARY[1:]}')],
            [InlineKeyboardButton("عضو شدم", callback_data=f"check_{file_id}")]
        ]
        markup = InlineKeyboardMarkup(buttons)
        await update.message.reply_text('برای دریافت فایل، در یکی از کانال‌ها عضو شوید:', reply_markup=markup)
    else:
        await send_and_delete(file_id, update, context)

async def handle_check_membership(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    file_id = query.data.split("_", 1)[1]
    not_joined = await check_membership(user_id, context.bot)
    if not_joined:
        await query.message.delete()
        await context.bot.send_message(chat_id=user_id, text='شما هنوز در یکی از کانال‌ها عضو نشدید.')
    else:
        await query.message.delete()
        await send_and_delete(file_id, query, context)

async def send_and_delete(file_id: str, update: Update | CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
    from database import increase_file_request, add_user
    user_id = update.effective_user.id
    add_user(user_id)
    increase_file_request(file_id)
    message = await context.bot.send_video(chat_id=user_id, video=file_id)
    await context.bot.send_message(chat_id=user_id, text='این پیام پس از ۳۰ ثانیه حذف می‌شود.')
    context.job_queue.run_once(delete_msg, 30, data={'chat_id': user_id, 'msg_id': message.message_id})

async def delete_msg(context: CallbackContext):
    data = context.job.data
    await context.bot.delete_message(chat_id=data['chat_id'], message_id=data['msg_id'])

def main():
    init_db()
    app = Application.builder().token(TOKEN).build()
    conv = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT, handle_panel_choice)],
        states={
            WAITING_FOR_MEDIA: [MessageHandler(filters.VIDEO, handle_media)],
            WAITING_FOR_CAPTION: [MessageHandler(filters.PHOTO, handle_cover)],
            WAITING_FOR_ACTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_caption)],
            WAITING_FOR_SCHEDULE: [MessageHandler(filters.TEXT, handle_schedule)],
            100: [MessageHandler(filters.TEXT, handle_timer)],
        },
        fallbacks=[CommandHandler('cancel', start)]
    )

    app.add_handler(CommandHandler("start", handle_start_command))
    app.add_handler(CallbackQueryHandler(handle_check_membership, pattern=r"^check_"))
    app.add_handler(conv)

    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        webhook_url="https://kkkkk-mkfn.onrender.com/webhook"
    )

if __name__ == '__main__':
    main()
