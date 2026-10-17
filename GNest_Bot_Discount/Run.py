import json
import os
import asyncio
from datetime import datetime, timezone, timedelta

from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher

import ReceivePSPrice as rec

# rec.ps_discounts()


load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN_DEMONTEST")

if not BOT_TOKEN:
    raise ValueError("❌ توکن پیدا نشد!")

CHANNEL_ID = "@game_nest_babol"

PROXY = "socks5://127.0.0.1:10808"

session = AiohttpSession(proxy=PROXY)

bot = Bot(
    token=BOT_TOKEN,
    session=session
)

dp = Dispatcher(storage=MemoryStorage())


# ---------------------------------------------------------
# ارسال لیست تخفیف‌ها
# ---------------------------------------------------------

async def send_discounts():

    STATE_FILE = "discounts_state.json"

    # بررسی انتشار قبلی
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as file:
            state = json.load(file)
    else:
        state = {}

    now = datetime.now(timezone.utc)

    last_sent = state.get("last_sent")
    message_id = state.get("message_id")

    update_previous = False

    if last_sent and message_id:
        last_sent_time = datetime.fromisoformat(last_sent)

        if now - last_sent_time < timedelta(days=7):
            update_previous = True


    DISCOUNT_FIle = "discounts.json"

    # خواندن فایل JSON
    with open(
        DISCOUNT_FIle,
        "r",
        encoding="utf-8"
    ) as file:

        games = json.load(file)

    print(f"Games loaded: {len(games)}")

    # محدودیت امن برای طول پیام
    # تلگرام محدودیت 4096 کاراکتر دارد.
    # کمی فاصله می‌گذاریم تا مطمئن باشیم.
    MAX_MESSAGE_LENGTH = 4000

    message_text = ""

    sent_messages = 0


    for index, game in enumerate(games, start=1):

        title = game.get("title")

        discount = game.get("discount")

        current_price = game.get("current_price")

        if not title:
            continue

        line = f"🎮 {title} {discount}\n{current_price}\n\n"

        # اگر اضافه کردن این بازی باعث عبور از محدودیت شود
        if len(message_text) + len(line) > MAX_MESSAGE_LENGTH:

            await bot.send_message(
                chat_id=CHANNEL_ID,
                text=message_text
            )

            sent_messages += 1

            print(
                f"Message {sent_messages} sent | "
                f"up to game {index - 1}"
            )

            # شروع پیام جدید
            message_text = ""

            # کمی مکث برای جلوگیری از Flood Limit
            await asyncio.sleep(1)

        message_text += line

    # ارسال آخرین پیام
    if message_text:

        if update_previous:

            # ویرایش پیام قبلی تخفیف‌ها
            try:
                await bot.edit_message_text(
                    chat_id=CHANNEL_ID,
                    message_id=message_id,
                    text=message_text
                )

                print("Previous discount message updated.")

            except Exception as e:
                if "message is not modified" in str(e):
                    print("Discount message has not changed.")
                else:
                    raise

            print("⏹ Going to Stop.")
            exit()

        else:

            # ارسال پیام جدید تخفیف‌ها
            msg = await bot.send_message(
                chat_id=CHANNEL_ID,
                text=message_text
            )

            message_id = msg.message_id

            print("New discount message sent.")

        last_msg = (
            "🎮 تخفیف های فعلی پلی استیشن\n\n"
            "📌 تمامی عناوین و درصدهای تخفیف درج‌شده در بالا مربوط به ریجن آمریکا US هستند؛\n\n"
            "ممکن است میزان تخفیف در ریجن‌های دیگر کمتر یا بیشتر باشد.\n\n"
            "🎮 تمامی بازی‌های فوق توسط تیم گیم‌نست، روی اکانت شخصی شما قابل خریداری هستند.\n\n"
            "📋 شما می‌توانید لیست کامل تخفیف‌ها را از طریق گزینه‌ی زیر مشاهده کنید.\n\n"
            "🔐 امکان خرید اکانت کامل بازی‌ها نیز فراهم است."
        )

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="👀 مشاهده تمامی تخفیف‌ها",
                        url="https://psprices.com/region-us/collection/all-discounts?ordering=desc&page=1&rating_logic"
                            "=or&show=games&sort=likes"
                    ),

                    InlineKeyboardButton(
                        text="💬 پشتیبانی و خرید",
                        url="https://t.me/Game_Nest_Admin"
                    )
                ]
            ]
        )

        await bot.send_message(
            chat_id=CHANNEL_ID,
            text=last_msg,
            reply_markup=keyboard
        )

        sent_messages += 1

        print(
            f"Message {sent_messages} sent | "
            f"all games completed"
        )

    # ذخیره آیدی و زمان انتشار
    state = {
        "last_sent": now.isoformat(),
        "message_id": message_id
    }

    with open(STATE_FILE, "w", encoding="utf-8") as file:
        json.dump(state, file, ensure_ascii=False, indent=4)

    print("=" * 50)
    print(f"Total games: {len(games)}")
    print(f"Total messages: {sent_messages}")
    print("=" * 50)


# ---------------------------------------------------------
# Handler
# ---------------------------------------------------------

@dp.message()
async def freetext(message: Message):

    print(message.chat.id)
    print(message.text)


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

async def main():

    try:

        print("Receiving PlayStation discounts...")

        rec.ps_discounts()



        print("Discounts received.")

        await send_discounts()

    except Exception as e:

        print(f"ERROR: {e}")

    finally:

        await bot.session.close()

        print("Bot session closed.")


if __name__ == "__main__":
    asyncio.run(main())

