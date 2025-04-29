from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, CallbackContext
from time import sleep

# توکن ربات تلگرام خود را وارد کنید
TOKEN = 'YOUR_BOT_TOKEN'
ADMIN_ID = YOUR_ADMIN_ID  # شناسه ادمین

# مرحله‌ای بودن پروسه
VIDEO_STATE = 1
COVER_STATE = 2
CAPTION_STATE = 3
SEND_STATE = 4

# ذخیره اطلاعات مراحل برای هر کاربر
user_data = {}

# توابع کمکی برای بررسی عضویت در کانال‌ها
def check_channel_membership(user_id):
    # اینجا بررسی می‌کنید که آیا کاربر عضو کانال‌هاست یا نه
    # در اینجا فقط یک شبیه‌سازی ساده انجام می‌دهیم
    return True  # برای مثال، فرض می‌کنیم که همیشه عضو هست

# تابع شروع
def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id == ADMIN_ID:
        start_admin_panel(update, context)
    else:
        update.message.reply_text("شما دسترسی به پنل ادمین ندارید.")

# پنل ادمین
def start_admin_panel(update, context):
    keyboard = [
        [InlineKeyboardButton("سوپر", callback_data='video')],
        [InlineKeyboardButton("پست", callback_data='post')],
        [InlineKeyboardButton("آمار", callback_data='statistics')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('خوش آمدید، لطفا یک گزینه را انتخاب کنید:', reply_markup=reply_markup)

# مرحله دریافت ویدیو
def handle_video(update, context):
    user_id = update.message.from_user.id
    user_data[user_id] = {"state": VIDEO_STATE}
    update.message.reply_text("لطفا ویدیو را ارسال کنید.")

# دریافت کاور
def handle_cover(update, context):
    user_id = update.message.from_user.id
    if user_data.get(user_id, {}).get("state") == VIDEO_STATE:
        user_data[user_id]["state"] = COVER_STATE
        user_data[user_id]["video"] = update.message.video.file_id
        update.message.reply_text("لطفا کاور را ارسال کنید.")

# دریافت کپشن
def handle_caption(update, context):
    user_id = update.message.from_user.id
    if user_data.get(user_id, {}).get("state") == COVER_STATE:
        user_data[user_id]["state"] = CAPTION_STATE
        user_data[user_id]["cover"] = update.message.photo[-1].file_id  # فرض می‌کنیم کاور عکس است
        update.message.reply_text("لطفا کپشن را ارسال کنید.")

# مرحله ارسال ویدیو به کانال
def handle_send(update, context):
    user_id = update.message.from_user.id
    if user_data.get(user_id, {}).get("state") == CAPTION_STATE:
        user_data[user_id]["state"] = SEND_STATE
        user_data[user_id]["caption"] = update.message.text
        video = user_data[user_id]["video"]
        cover = user_data[user_id]["cover"]
        caption = user_data[user_id]["caption"]
        
        # ارسال پیام به همراه لینک "مشاهده"
        video_link = "https://your_video_link"  # لینک ویدیو
        keyboard = [
            [InlineKeyboardButton("مشاهده", url=video_link)],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(f"ویدیو آماده است:\n{caption}\n\n@hottof | تُفِ داغ", reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        
        # ارسال به کانال
        update.message.reply_text("ویدیو به کانال @hottof ارسال شد!")

        # بررسی عضویت کاربر در کانال‌ها
        if check_channel_membership(user_id):
            update.message.reply_text("شما عضو کانال‌های مورد نظر هستید. ویدیو به شما ارسال می‌شود.")
            # ارسال ویدیو به کاربر بعد از تایید عضویت
            update.message.reply_video(video)
        else:
            update.message.reply_text("شما عضو کانال‌های @hottof یا @tofhot نیستید. لطفا عضو شوید.")
        # پاک کردن داده‌های کاربر بعد از تکمیل مراحل
        del user_data[user_id]

# مدیریت پست
def handle_post(update, context):
    update.message.reply_text("لطفا پیام فوروارد شده را ارسال کنید.")
    # فرض کنیم کاربر پیام فوروارد شده را ارسال کرده است
    sleep(2)  # شبیه‌سازی فرآیند
    update.message.reply_text("پست ارسال شد!\nکپشن: این یک نمونه پست است.\n\n@hottof | تُفِ داغ", parse_mode=ParseMode.MARKDOWN)
    # ارسال به کانال‌ها (در اینجا شبیه‌سازی می‌شود)
    update.message.reply_text("پست به کانال @hottof ارسال شد!")

# نمایش آمار ربات
def show_statistics(update, context):
    update.message.reply_text("آمار ربات:\nساعت گذشته: 10 نفر\nروز گذشته: 100 نفر\nهفته گذشته: 500 نفر\nماه گذشته: 2000 نفر")

# تابع اصلی
def main():
    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # دستورات ربات
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CallbackQueryHandler(handle_video, pattern='^video$'))
    dispatcher.add_handler(CallbackQueryHandler(handle_post, pattern='^post$'))
    dispatcher.add_handler(CallbackQueryHandler(show_statistics, pattern='^statistics$'))
    dispatcher.add_handler(MessageHandler(Filters.video, handle_video))
    dispatcher.add_handler(MessageHandler(Filters.photo, handle_cover))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_caption))

    # راه‌اندازی ربات
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
