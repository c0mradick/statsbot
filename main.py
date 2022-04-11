import asyncio
import logging

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher
from foobardb import FoobarDB
from config import TOKEN, ADTEXT, CHAT_ID, ADMINS, DELAY
logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
safe_mode = False

db = FoobarDB("./database.db")
usersdb = FoobarDB("./users.db")

loop = asyncio.get_event_loop()

async def delay_message():
    await bot.send_message(chat_id=CHAT_ID, text=ADTEXT)
    when_to_call = loop.time() + DELAY
    loop.call_at(when_to_call, my_callback)

def my_callback():
    asyncio.ensure_future(delay_message())

# async def hello_throttled(*args, **kwargs):
#     message = args[0]
#     await message.reply("Команду можно использовать только раз в 10с")

@dp.message_handler(commands=["say"])
async def say(message: types.Message):
    if message.from_user.id in ADMINS:
        await message.answer(message.text.replace('/say ', ''))
        await message.delete()

@dp.message_handler(commands=["start", "info"])
async def info(message: types.Message):
    await message.reply("Версия бота сделана пользователем @C0mRaDick\nBot version created by @C0mRaDick")

@dp.message_handler(commands=["stats"])
@dp.throttled(rate=10)
async def stats(message: types.Message):
    if message.chat.id != CHAT_ID:
        return
    if db.get(str(message.from_user.id)):
        msgs = db.get(str(message.from_user.id))
    else:
        msgs = 0
    await message.reply(f"Ваш профиль пользователя:\nИмя: {message.from_user.full_name}\nUser ID: {message.from_user.id}\nНаписано сообщений: {msgs}")

@dp.message_handler(commands=["top"])
@dp.throttled(rate=10)
async def top(message: types.Message):
    if message.chat.id != CHAT_ID:
        return
    data = db.unload()
    data = sorted(data.items(), key=lambda x: x[1], reverse=True)
    text = ""
    if len(data) > 5:
        data = data[:5]
    i = 0
    for dataitem in data:
        i += 1
        text += f"\n{i}) {usersdb.get(str(dataitem[0]))} ({dataitem[0]}) - {dataitem[1]}"
    await message.reply(text)

@dp.message_handler()
@dp.throttled(rate=1)
async def counter(message: types.Message):
    if message.chat.id != CHAT_ID or len(message.text) < 6:
        return
    if db.get(str(message.from_user.id)):
        db.set(message.from_user.id, db.get(str(message.from_user.id))+1)
        db.dumpdb()
    else:
        usersdb.set(message.from_user.id, message.from_user.full_name)
        usersdb.dumpdb()
        db.set(message.from_user.id, 1)
        db.dumpdb()
    if message.from_user.id == ADMINS[0]:
        global safe_mode
        if message.text == "SAFE OFF":
            safe_mode = False
            await message.delete()
            return
        elif message.text == "SAFE ON":
            safe_mode = True
            await message.delete()
            return
        if safe_mode:
            await message.answer(message.text)
            await message.delete()

if __name__ == "__main__":
    my_callback()
    executor.start_polling(dp, skip_updates=True)