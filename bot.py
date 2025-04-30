import logging
import sqlite3
import datetime
import asyncio

from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor

API_TOKEN = "YOUR_BOT_TOKEN"
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

logging.basicConfig(level=logging.INFO)

ADMIN_IDS = [123456789]  # شناسه‌های ادمین
CHANNELS = {
    "@hottof": "تُفِ داغ",
    "@tofhot": "زاپاس تف"
}
CHANNEL_POST_TARGET = "@hottof"

keyboard_main = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard_main.add(
    KeyboardButton("1 سوپر"),
    KeyboardButton("2 پست"),
    KeyboardButton("3 آمار")
)
def init_db():
    conn = sqlite3.connect("bot_data.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            first_name TEXT,
            username TEXT,
            created_at TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            file_id TEXT,
            caption TEXT,
            created_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_user(user: types.User):
    conn = sqlite3.connect("bot_data.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, first_name, username, created_at) VALUES (?, ?, ?, ?)", (
        user.id,
        user.first_name or "",
        user.username or "",
        datetime.datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()

def add_file(user_id: int, file_id: str, caption: str):
    conn = sqlite3.connect("bot_data.db")
    c = conn.cursor()
    c.execute("INSERT INTO files (user_id, file_id, caption, created_at) VALUES (?, ?, ?, ?)", (
        user_id,
        file_id,
        caption,
        datetime.datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()

class SuperState(StatesGroup):
    waiting_video = State()
    waiting_cover = State()
    waiting_caption = State()
    waiting_membership = State()

class PostState(StatesGroup):
    waiting_forward = State()
    waiting_caption = State()
    waiting_schedule = State()

@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    add_user(message.from_user)
    await message.answer("به ربات خوش آمدید!", reply_markup=keyboard_main)

@dp.message_handler(commands=["پنل"])
async def panel_handler(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    await message.answer("به پنل مدیریت خوش آمدید.", reply_markup=keyboard_main)

@dp.message_handler(lambda m: m.text == "1 سوپر")
async def handle_super(message: types.Message):
    await message.answer("لطفاً ویدیو را ارسال کنید.")
    await SuperState.waiting_video.set()

@dp.message_handler(content_types=types.ContentType.VIDEO, state=SuperState.waiting_video)
async def super_got_video(message: types.Message, state: FSMContext):
    await state.update_data(video=message.video.file_id)
    await message.answer("لطفاً کاور (عکس) را ارسال کنید.")
    await SuperState.next()

@dp.message_handler(content_types=types.ContentType.PHOTO, state=SuperState.waiting_cover)
async def super_got_cover(message: types.Message, state: FSMContext):
    await state.update_data(cover=message.photo[-1].file_id)
    await message.answer("لطفاً کپشن را وارد کنید.")
    await SuperState.next()

@dp.message_handler(state=SuperState.waiting_caption)
async def super_got_caption(message: types.Message, state: FSMContext):
    await state.update_data(caption=message.text)
    markup = InlineKeyboardMarkup()
    for ch, name in CHANNELS.items():
        markup.add(InlineKeyboardButton(name, url=f"https://t.me/{ch[1:]}"))
    markup.add(InlineKeyboardButton("عضو شدم", callback_data="verify_membership"))
    await message.answer("برای دریافت ویدیو، ابتدا در یکی از کانال‌های زیر عضو شوید:", reply_markup=markup)
    await SuperState.waiting_membership.set()

@dp.callback_query_handler(lambda c: c.data == "verify_membership", state=SuperState.waiting_membership)
async def verify_membership(call: types.CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    ok = False
    for channel in CHANNELS.keys():
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in ["member", "creator", "administrator"]:
                ok = True
                break
        except:
            continue

    if not ok:
        await call.message.delete()
        markup = InlineKeyboardMarkup()
        for ch, name in CHANNELS.items():
            markup.add(InlineKeyboardButton(name, url=f"https://t.me/{ch[1:]}"))
        markup.add(InlineKeyboardButton("عضو شدم", callback_data="verify_membership"))
        await call.message.answer("هنوز عضو نیستی، لطفاً عضو یکی از کانال‌ها شو:", reply_markup=markup)
        return

    data = await state.get_data()
    video_id = data["video"]
    cover_id = data["cover"]
    caption = data["caption"]
    tag = "@hottof | تُفِ داغ"
    view_link = f"https://t.me/{CHANNEL_POST_TARGET[1:]}"
    full_caption = f"{caption}\n\nمشاهده: {view_link}\n\n{tag}"

    await bot.send_photo(call.message.chat.id, photo=cover_id, caption=full_caption, parse_mode='HTML')
    await bot.send_video(call.message.chat.id, video=video_id)

    add_file(user_id=call.from_user.id, file_id=video_id, caption=caption)

    await asyncio.sleep(30)
    try:
        await call.message.answer("ویدیو پس از ۳۰ ثانیه حذف شد.")
    except:
        pass

    await state.finish()

@dp.message_handler(lambda m: m.text == "2 پست")
async def handle_post(message: types.Message):
    await message.answer("لطفاً یک پیام فوروارد شده از کانالی دیگر ارسال کنید.")
    await PostState.waiting_forward.set()

@dp.message_handler(lambda m: m.forward_from_chat, state=PostState.waiting_forward)
async def post_got_forward(message: types.Message, state: FSMContext):
    await state.update_data(forward=message)
    await message.answer("لطفاً کپشن دلخواه را بنویسید.")
    await PostState.next()

@dp.message_handler(state=PostState.waiting_caption)
async def post_got_caption(message: types.Message, state: FSMContext):
    data = await state.get_data()
    forwarded = data["forward"]
    caption = message.text
    tag = "@hottof | تُفِ داغ"
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("ارسال در کانال حالا", "ارسال در کانال در آینده")
    markup.add("لغو", "بازگشت به پنل اصلی")
    await message.answer("پیش‌نمایش پست شما:", reply_markup=markup)
    await message.copy_to(message.chat.id, caption=f"{caption}\n\n{tag}")
    await state.update_data(caption=caption)
    await PostState.waiting_schedule.set()

@dp.message_handler(lambda m: m.text in ["ارسال در کانال حالا", "ارسال در کانال در آینده"], state=PostState.waiting_schedule)
async def post_send_now(message: types.Message, state: FSMContext):
    data = await state.get_data()
    caption = data["caption"]
    tag = "@hottof | تُفِ داغ"
    full_caption = f"{caption}\n\n{tag}"
    fwd = data["forward"]
    await fwd.copy_to(CHANNEL_POST_TARGET, caption=full_caption)
    await message.answer("پست با موفقیت به کانال ارسال شد.", reply_markup=keyboard_main)
    await state.finish()

@dp.message_handler(lambda m: m.text == "3 آمار")
async def show_stats(message: types.Message):
    conn = sqlite3.connect("bot_data.db")
    c = conn.cursor()

    now = datetime.datetime.now()
    hour_ago = (now - datetime.timedelta(hours=1)).isoformat()
    day_ago = (now - datetime.timedelta(days=1)).isoformat()
    week_ago = (now - datetime.timedelta(weeks=1)).isoformat()
    month_ago = (now - datetime.timedelta(days=30)).isoformat()

    total_users = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    last_hour = c.execute("SELECT COUNT(*) FROM users WHERE created_at > ?", (hour_ago,)).fetchone()[0]
    last_day = c.execute("SELECT COUNT(*) FROM users WHERE created_at > ?", (day_ago,)).fetchone()[0]
    last_week = c.execute("SELECT COUNT(*) FROM users WHERE created_at > ?", (week_ago,)).fetchone()[0]
    last_month = c.execute("SELECT COUNT(*) FROM users WHERE created_at > ?", (month_ago,)).fetchone()[0]
    file_count = c.execute("SELECT COUNT(*) FROM files").fetchone()[0]

    now_str = now.strftime("%H:%M:%S")
    date_str = now.strftime("%Y/%m/%d")

    await message.answer(
        f"🤖 آمار شما در ساعت {now_str} و تاریخ {date_str} به این صورت می‌باشد\n\n"
        f"👥 تعداد اعضا : {total_users:,}\n"
        f"🕒 تعداد کاربران ساعت گذشته : {last_hour:,}\n"
        f"☪️ تعداد کاربران 24 ساعت گذشته : {last_day:,}\n"
        f"7️⃣ تعداد کاربران هفته گذشته : {last_week:,}\n"
        f"🌛 تعداد کاربران ماه گذشته : {last_month:,}\n"
        f"🗂 تعداد فایل ها : {file_count:,}"
    )
    conn.close()

@dp.message_handler(lambda m: m.text == "بازگشت به پنل اصلی", state="*")
async def back_to_main(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("بازگشت به پنل اصلی", reply_markup=keyboard_main)

@dp.message_handler()
async def fallback(message: types.Message):
    await message.answer("لطفاً یکی از گزینه‌های موجود را انتخاب کنید.", reply_markup=keyboard_main)

if __name__ == "__main__":
    init_db()
    executor.start_polling(dp, skip_updates=True)
