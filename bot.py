from aiogram.utils.callback_data import CallbackData
from aiogram import Bot, Dispatcher, executor, types
import requests
import logging
import re
import random
import os


TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

HEROKU_APP_NAME = os.getenv("HEROKU_APP_NAME")

# webhook settings
WEBHOOK_HOST = f"https://{HEROKU_APP_NAME}.herokuapp.com"
WEBHOOK_PATH = f"/webhook/{TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# webserver settings
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = os.getenv("PORT", default=8000)


async def on_startup(dispatcher: Dispatcher):
    await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)


async def on_shutdown(dispatcher: Dispatcher):
    bot.delete_webhook()


def get_links_list(page):
    result = []
    text = requests.get(f"https://midjourney.com/showcase/{page}/").text
    urls = re.findall(
        "http[s]?://cdn(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
        text,
    )

    for image_index in range(0, len(urls) + 1, 2):
        link = urls[image_index]
        result.append(link)

    return result


links = get_links_list("recent")
top_links = get_links_list("top")[1:]


image_step = CallbackData("vote", "action", "amount")


def get_keyboard(link, commmand):

    keyboard = types.InlineKeyboardMarkup(row_width=2).row(
        types.InlineKeyboardButton(
            text="⏪", callback_data=image_step.new(action="prev", amount=commmand)
        ),
        types.InlineKeyboardButton(
            text="⏩", callback_data=image_step.new(action="next", amount=commmand)
        ),
    )
    keyboard.add(types.InlineKeyboardButton(text="Download from link", url=link))
    return keyboard


@dp.message_handler(commands=["start"])
async def send_images(message: types.Message):
    await message.answer(
        text=f"Hello\! Send me */recent* to get latest images from midjourney website",
        parse_mode="MarkdownV2",
    )


@dp.message_handler(commands=["recent"])
async def send_images(message: types.Message):
    global index
    index = 1

    link = links[index]

    await bot.send_photo(
        chat_id=message.chat.id,
        photo=link,
        reply_markup=get_keyboard(link, "recent"),
    )


@dp.message_handler(commands=["top"])
async def send_images(message: types.Message):
    global index
    index = 1

    link = top_links[index]

    await bot.send_photo(
        chat_id=message.chat.id,
        photo=link,
        reply_markup=get_keyboard(link, "top"),
    )


@dp.message_handler(commands=["random"])
async def send_images(message: types.Message):

    full_list = []
    full_list.extend(links)
    full_list.extend(top_links)

    link = random.choice(full_list)

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text="Download", url=link))

    try:
        await bot.send_photo(chat_id=message.chat.id, photo=link, reply_markup=keyboard)
    except Exception:
        pass


@dp.callback_query_handler(image_step.filter(action="next"))
async def next_image_callback(query: types.CallbackQuery, callback_data: dict):
    global index
    index += 1

    if callback_data["amount"] == "top":
        link = top_links[index]
    else:
        link = links[index]

    await bot.edit_message_media(
        media=types.InputMediaPhoto(types.InputFile.from_url(link)),
        message_id=query.message.message_id,
        chat_id=query.from_user.id,
        reply_markup=get_keyboard(link, callback_data["amount"]),
    )


@dp.callback_query_handler(image_step.filter(action="prev"))
async def prev_image_callback(query: types.CallbackQuery, callback_data: dict):
    global index
    index -= 1

    if callback_data["amount"] == "top":
        link = top_links[index]
    else:
        link = links[index]

    await bot.edit_message_media(
        media=types.InputMediaPhoto(types.InputFile.from_url(link)),
        message_id=query.message.message_id,
        chat_id=query.from_user.id,
        reply_markup=get_keyboard(link, callback_data["amount"]),
    )


logging.basicConfig(level=logging.INFO)
executor.start_webhook(
    dispatcher=dp,
    webhook_path=WEBHOOK_PATH,
    skip_updates=True,
    on_startup=on_startup,
    on_shutdown=on_shutdown,
    host=WEBAPP_HOST,
    port=WEBAPP_PORT,
)
