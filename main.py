import os
import logging
from telegram import Update, CallbackQuery, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    ContextTypes, ConversationHandler, CallbackContext, JobQueue
)
from datetime import datetime, timedelta
from collections import defaultdict

TOKEN = '7413532622:AAFfd_ctt4Xb055CqQxct64anIUTHhagW4M'
CHANNEL_USERNAME = '@hottof'
CHANNEL_NAME = 'تُفِ داغ'
CHANNEL_USERNAME_SECONDARY = '@tofhot'
CHANNEL_NAME_SECONDARY = 'زاپاس تف'
ADMINS = [6387942633]

WAITING_FOR_MEDIA, WAITING_FOR_CAPTION, WAITING_FOR_ACTION, WAITING_FOR_SCHEDULE = range(4)
user_stats = defaultdict(list)
file_counter = {'count': 0}
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
application = Application.builder().token(TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_stats[user_id].append(datetime.now())
    if update.effective_user.id not in ADMINS:
        await update.message.reply_text('به ربات خوش آمدید.')
        return ConversationHandler.END
    keyboard = [['۱ سوپر', '۲ پست', '۳ آمار']]
    await update.message.reply_text('به پنل خوش آمدید.', reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return WAITING_FOR_MEDIA

async def handle_panel_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == '۱ سوپر':
        await update.message.reply_text('یک ویدیو ارسال کن.')
        return WAITING_FOR_MEDIA
    if text == '۲ پست':
        await update.message.reply_text('یک پیام فوروارد کن.')
        return WAITING_FOR_CAPTION
    if text == '۳ آمار':
        now = datetime.now()
        one_hour = sum(1 for u in user_stats if any((now - t).total_seconds() <= 3600 for t in user_stats[u]))
        one_day = sum(1 for u in user_stats if any((now - t).total_seconds() <= 86400 for t in user_stats[u]))
        one_week = sum(1 for u in user_stats if any((now - t).total_seconds() <= 604800 for t in user_stats[u]))
        one_month = sum(1 for u in user_stats if any((now - t).total_seconds() <= 2592000 for t in user_stats[u]))
        await update.message.reply_text(
            f'🤖 آمار شما در ساعت {now.strftime("%H:%M:%S")} و تاریخ {now.strftime("%Y/%m/%d")} به این صورت می‌باشد\n\n'
            f'👥 تعداد اعضا : {len(user_stats)}\n'
            f'🕒 کاربران ساعت گذشته : {one_hour}\n'
            f'☪️ کاربران ۲۴ ساعت گذشته : {one_day}\n'
            f'7️⃣ کاربران هفته گذشته : {one_week}\n'
            f'🌛 کاربران ماه گذشته : {one_month}\n'
            f'🗂 تعداد فایل‌ها : {file_counter["count"]}'
        )
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
    final_caption = f'{caption}\n\nمشاهده'
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('مشاهده', url=f'https://t.me/{context.bot.username}?start={file_id}')]])
    preview_caption = f'{caption}\n\n@hottof | تُفِ داغ'
    await update.message.reply_photo(cover_id, caption=preview_caption, reply_markup=keyboard)
    reply_keyboard = [['ارسال در کانال حالا', 'ارسال در آینده'], ['لغو', 'برگشت به پنل اصلی']]
    context.user_data['preview_caption'] = preview_caption
    context.user_data['inline_keyboard'] = keyboard
    return WAITING_FOR_SCHEDULE

async def handle_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == 'ارسال در کانال حالا':
        await send_to_channel(context)
        await update.message.reply_text('ارسال شد.', reply_markup=ReplyKeyboardRemove())
        return WAITING_FOR_MEDIA
    if text == 'ارسال در آینده':
        await update.message.reply_text('زمان ارسال را به دقیقه وارد کنید:')
        return 100
    if text == 'برگشت به پنل اصلی':
        return await start(update, context)
    if text == 'لغو':
        await update.message.reply_text('لغو شد.', reply_markup=ReplyKeyboardRemove())
        return WAITING_FOR_MEDIA
    return WAITING_FOR_SCHEDULE

async def handle_timer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        minutes = int(update.message.text)
        context.job_queue.run_once(
            send_to_channel_job, when=timedelta(minutes=minutes), data=context.user_data.copy()
        )
        await update.message.reply_text('زمان‌بندی شد.', reply_markup=ReplyKeyboardRemove())
        return WAITING_FOR_MEDIA
    except:
        await update.message.reply_text('عدد وارد کنید.')
        return 100

async def send_to_channel(context):
    data = context.user_data
    await context.bot.send_photo(
        chat_id=CHANNEL_USERNAME,
        photo=data['cover'],
        caption=data['preview_caption'],
        reply_markup=data['inline_keyboard']
    )
    file_counter['count'] += 1

async def send_to_channel_job(context: CallbackContext):
    data = context.job.data
    await context.bot.send_photo(
        chat_id=CHANNEL_USERNAME,
        photo=data['cover'],
        caption=data['preview_caption'],
        reply_markup=data['inline_keyboard']
    )
    file_counter['count'] += 1

from telegram.constants import ChatMemberStatus
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

async def check_membership(user_id: int, bot) -> list:
    not_joined = []
    for ch in [CHANNEL_USERNAME, CHANNEL_USERNAME_SECONDARY]:
        member = await bot.get_chat_member(chat_id=ch, user_id=user_id)
        if member.status not in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            not_joined.append(ch)
    return not_joined

async def handle_start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text('برای استفاده از ربات روی لینک "مشاهده" در پست کلیک کنید.')
        return

    file_id = args[0]
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
    user_id = update.effective_user.id
    message = await context.bot.send_video(chat_id=user_id, video=file_id)
    await context.bot.send_message(chat_id=user_id, text='این پیام پس از ۳۰ ثانیه حذف می‌شود.')
    context.job_queue.run_once(delete_msg, 30, data={'chat_id': user_id, 'msg_id': message.message_id})

from telegram import CallbackQuery
from datetime import datetime
from collections import defaultdict

stats = defaultdict(list)
file_counter = {'count': 0}

async def delete_msg(context: CallbackContext):
    data = context.job.data
    await context.bot.delete_message(chat_id=data['chat_id'], message_id=data['msg_id'])

async def handle_user_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now()
    uid = update.effective_user.id
    stats['all'].append((uid, now))

    hour_ago = now - timedelta(hours=1)
    day_ago = now - timedelta(days=1)
    week_ago = now - timedelta(weeks=1)
    month_ago = now - timedelta(days=30)

    count = lambda delta: len([t for u, t in stats['all'] if t >= delta])

    text = f'''🤖 آمار شما در ساعت {now.strftime('%H:%M:%S')} و تاریخ {now.strftime('%Y/%m/%d')} به این صورت می‌باشد:

👥 تعداد اعضا : {len(set(u for u, _ in stats['all'])):,}
🕒 تعداد کاربران ساعت گذشته : {count(hour_ago):,}
☪️ تعداد کاربران 24 ساعت گذشته : {count(day_ago):,}
7️⃣ تعداد کاربران هفته گذشته : {count(week_ago):,}
🌛 تعداد کاربران ماه گذشته : {count(month_ago):,}
🗂 تعداد فایل ها : {file_counter['count']:,}
'''
    await update.message.reply_text(text)

def main():
    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^(سوپر)$'), handle_panel_choice)],
        states={
            1: [MessageHandler(filters.VIDEO, super_get_video)],
            2: [MessageHandler(filters.PHOTO, super_get_cover)],
            3: [MessageHandler(filters.TEXT & ~filters.COMMAND, super_get_caption)],
            4: [MessageHandler(filters.TEXT, handle_schedule)],
            100: [MessageHandler(filters.TEXT, handle_timer)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    app.add_handler(conv)
    app.add_handler(CommandHandler("start", handle_start_command))
    app.add_handler(CallbackQueryHandler(handle_check_membership, pattern=r"^check_"))
    app.add_handler(MessageHandler(filters.Regex('^(پست)$'), handle_media))
    app.add_handler(MessageHandler(filters.Regex('^(آمار)$'), handle_user_stats))
    app.add_handler(MessageHandler(filters.TEXT, start))

    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        webhook_url="https://ooooo-fiwm.onrender.com/"
    )

if __name__ == '__main__':
    main()
