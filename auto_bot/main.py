import logging
import re
from typing import Optional, Tuple

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher.webhook import SendMessage
from aiogram.utils.executor import start_webhook
from conf import settings
from db import Plate
from tortoise import Tortoise

plate_num_regex = re.compile(r"(\w\d{3}\w{2} ?\d{2,3})")
phone_num_regex = re.compile(r"[78](\d{10})")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=settings.API_TOKEN)
dispatcher = Dispatcher(bot=bot)

dispatcher.middleware.setup(LoggingMiddleware())


START_TEXT = """
Привет! Я телеграм бот автомобилистов Саларьево Парк,

Если ты автомобилист, зарегистрируйся пожалуйста с помощью команды /reg + номер машины,
тогда я помогу другим найти твой ник в телеграме по номеру машины.
Например: /reg A111AA777 (принимается латиница, кириллица, и буквы любого регистра)

Если ты хочешь добавить чей-то номер из под стекла в базу данных, напиши /add_phone + номер машины + номер телефона.
Например: /add_phone A111AA777 (в номере авто принимается латиница, кириллица, и буквы любого регистра), номер телефона должен начинаться с 7 или 8, далее 10 цифр номера телефона

Если ты хочешь найти кого-то по номеру машины - напиши /search + номер машины.
Например: /search A111AA777 (принимается латиница, кириллица, и буквы любого регистра)

Если ты хочешь удалить свои данные из бота - напиши /delete + номер машины.
Например: /delete A111AA777 (принимается латиница, кириллица, и буквы любого регистра)

Если ты хочешь посмотреть список своих машин - напиши /my_cars.
"""


REPLACE_MAP = {
    "А": "A",
    "В": "B",
    "Е": "E",
    "К": "K",
    "М": "M",
    "Н": "H",
    "О": "O",
    "Р": "P",
    "С": "C",
    "Т": "T",
    "У": "Y",
    "Х": "X",
}


def normalize_num(text: str) -> Tuple[Optional[str], Optional[str]]:
    raw_pn = None
    raw_phone_num = None
    if plate_num := plate_num_regex.search(text):
        raw_pn = plate_num.string[plate_num.regs[0][0] : plate_num.regs[0][1]].upper()
        for i, x in REPLACE_MAP.items():
            raw_pn = raw_pn.replace(i, x)
    if phone_num := phone_num_regex.search(text):
        raw_phone_num = phone_num.string[phone_num.regs[0][0] : phone_num.regs[0][1]].upper()
        raw_phone_num = f"7{raw_phone_num[1:]}"
    return raw_pn, raw_phone_num


@dispatcher.message_handler(commands=["start"])
async def start(message: types.Message):
    return SendMessage(message.chat.id, text=START_TEXT)


@dispatcher.message_handler(commands=["my_cars"])
async def my_cars(message: types.Message):
    res = await Plate.filter(telegram_user=message.from_user.id).all()
    await message.reply("\n".join(record.plate_number for record in res))


@dispatcher.message_handler(commands=["reg"])
async def register(message: types.Message):
    plate_num, _ = normalize_num(message.text)
    if plate_num:
        if plate := await Plate.get_or_none(
            plate_number=plate_num,
        ):
            await message.reply(
                f"Номер {plate_num} уже привязан к аккаунту: [{plate.plate_number}](tg://user?id={plate.telegram_user})",
                parse_mode="Markdown",
            )
        else:
            await Plate.create(
                plate_number=plate_num, telegram_user=message.from_user.id
            )
            await message.reply(f"Номер {plate_num} привязан к вашему аккаунту.")
    else:
        await message.reply(
            "Неправильный формат ввода. Правильное использование команды: /reg A123BC123."
        )


@dispatcher.message_handler(commands=["add_phone"])
async def add_phone(message: types.Message):
    plate_num, phone_num = normalize_num(message.text)
    if plate_num and phone_num:
        if plate := await Plate.get_or_none(
            plate_number=plate_num,
        ):
            await message.reply(
                f"Номер {plate_num} уже привязан к аккаунту",
            )
            if plate.phone_number:
                await message.reply_contact(phone_number=plate.phone_number, first_name=plate.plate_number)
            elif plate.telegram_user:
                await message.reply(
                    f"[{plate.plate_number}](tg://user?id={plate.telegram_user})",
                    parse_mode="Markdown",
                )

        else:
            await Plate.create(
                plate_number=plate_num, phone_number=phone_num
            )
            await message.reply(f"Номер {plate_num} привязан к телефону {phone_num}.")
    else:
        await message.reply(
            "Неправильный формат ввода. "
            "Правильное использование команды: /add_phone A123BC123 79998881234."
        )


@dispatcher.message_handler(commands=["search"])
async def search(message: types.Message):
    plate_num, _ = normalize_num(message.text)
    if plate_num:
        plate = await Plate.get_or_none(
            plate_number=plate_num,
        )
        if not plate:
            await message.reply("Я такой номер не знаю.")

        elif plate.telegram_user:
            await message.reply(
                f"[{plate.plate_number}](tg://user?id={plate.telegram_user})",
                parse_mode="Markdown",
            )
        elif plate.phone_number:
            await message.reply_contact(phone_number=plate.phone_number, first_name=plate.plate_number)
    else:
        await message.reply(
            "Неправильный формат ввода. Правильное использование команды: /search A123BC123."
        )


@dispatcher.message_handler(commands=["delete"])
async def delete(message: types.Message):
    plate_num, _ = normalize_num(message.text)
    if plate_num:
        plate = await Plate.get_or_none(
            plate_number=plate_num,
        )
        if plate:
            await plate.delete()
            await message.reply(f"Номер {plate_num} отвязан от вашего аккаунта.")
        else:
            await message.reply("Такой номер за вами не зарегистрирован.")
    else:
        await message.reply(
            "Неправильный формат ввода. Правильное использование команды: /delete A123BC123."
        )


async def init_db():
    """"""
    await Tortoise.init(db_url=settings.DATABASE_URL, modules={"auto_bot": ["db"]})


async def on_startup(dp):
    await init_db()
    await bot.set_webhook(settings.WEBHOOK_URL)
    await bot.set_my_commands(
        commands=[
            types.BotCommand(command="/start", description="Начать."),
            types.BotCommand(
                command="/reg",
                description="Привязать номер машины к своему телеграм аккаунту.",
            ),
            types.BotCommand(
                command="/add_phone",
                description="Привязать номер машины к номеру телефона.",
            ),
            types.BotCommand(
                command="/search",
                description="Запросить пользователя Telegram по номеру машины.",
            ),
            types.BotCommand(
                command="/delete", description="Удалить свой номер из базы данных бота."
            ),
            types.BotCommand(
                command="/my_cars", description="Показать список моих машин."
            ),
        ],
    )


async def on_shutdown(dp):
    logging.warning("Shutting down..")
    await bot.delete_webhook()
    await Tortoise.close_connections()

    logging.warning("Bye!")


if __name__ == "__main__":
    start_webhook(
        dispatcher=dispatcher,
        webhook_path=settings.WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host=settings.HOST,
        port=settings.PORT,
    )
