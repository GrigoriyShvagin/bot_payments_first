import asyncio
import logging
import sys
import datetime
import sqlite3
import calendar

from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.types.message import ContentType
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import FSInputFile, Message
from aiogram.utils.markdown import hbold

connection=sqlite3.connect('users_database.db')

cursor = connection.cursor()

# Создаем таблицу Users
cursor.execute("CREATE TABLE IF NOT EXISTS Users(userid INTEGER UNIQUE,"
               "date TEXT)")

def add_months(sourcedate, months):
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year, month)[1])
    return str(datetime.date(year, month, day))


# log
logging.basicConfig(level=logging.INFO)

# init


PRICE = types.LabeledPrice(label="Подписка на 1 месяц", amount=500*100)
bot = Bot(token, parse_mode=ParseMode.HTML)
dp = Dispatcher()
users_list=[]


async def periodic():
    user_id = ""
    while True:
        now = datetime.datetime.now()
        current_time = now.strftime("%Y-%m-%d")
        users_list_query = "SELECT * FROM Users"
        cursor.execute(users_list_query)
        users_list = cursor.fetchall()
        print(users_list)
        for user in users_list:
            user_id=user[0]
            user_data=user[1]
            if user_data == current_time:
                cursor.execute(f"DELETE FROM Users WHERE userid=?",(user_id,))
                await bot.send_message(user_id,f"Здравствуйте, Ваша подписка истекла, если хотите продлить ее, нажмите на кнопку Подписка ")
                await bot.ban_chat_member(chat_id_channel,user_id)
                await bot.ban_chat_member(chat_id_group,user_id)
        await asyncio.sleep(180)

@dp.chat_join_request()
async def join_request(update: types.ChatJoinRequest):
    user_id=str(update.from_user.id)
    users_list_query = "SELECT * FROM Users"
    cursor.execute(users_list_query)
    users_list = cursor.fetchall()
    send_message=0
    for user in users_list:
        if user[0]==user_id:
            date_end=user[1]
            send_message=1
            await update.approve()
            await bot.send_message(user_id,f"Ваша заявка навступление была одобрена! окончание подписки: {date_end}")
    if send_message==0:
        await update.decline()
        await bot.send_message(user_id,
                               "Вас нет в базе оплативших пользователей... Если Вы оплачивали подписку, пожалуйста, напишите /help")


# echo bot
@dp.message(Command("po"))
async def command_start_handler(message: Message) -> None:

    message_send=0
    now = datetime.datetime.now()
    current_time = now.strftime("%d-%m-%Y")
    user_id=str(message.from_user.id)
    users_list_query="SELECT * FROM Users"
    cursor.execute(users_list_query)
    users_list=cursor.fetchall()
    for user in users_list:
        if user[0]==user_id:
            message_send=1
    if message_send==1:
        await message.answer(f"{hbold(message.from_user.full_name)}, Вы уже есть в списке, если бот не кидал Вам ссылку на канал, пожалуйста, напишите команду /help")
    else:
        await bot.unban_chat_member(chat_id_channel, user_id)
        await bot.unban_chat_member(chat_id_group, user_id)
        date_sub_end=add_months(datetime.datetime.now(),0)
        cursor.execute('INSERT INTO Users (userid, date) VALUES (?, ?)', (f'{user_id}', f'{date_sub_end}'))

    cursor.execute("DELETE FROM 'Users'")
    connection.commit()

@dp.message(Command('buy'))
async def command_buy_handler(message:Message):
    if payments_token.split(':')[1]=="TEST":
        await message.answer("Тестовый платеж")
    await bot.send_invoice(chat_id=message.chat.id,title="Подписка на бота",
                           description="Активация подписки на бота на 1 месяц",
                           provider_token=payments_token,
                           currency="rub",
                           photo_url="https://www.aroged.com/wp-content/uploads/2022/06/Telegram-has-a-premium-subscription.jpg",
                           photo_width=416,
                           photo_height=234,
                           photo_size=416,
                           is_flexible=False,
                           prices= [PRICE],
                           start_parameter="one-month-subscription",
                           payload="test-invoice-payload")


@dp.pre_checkout_query()
async def pre_checkout_query(pre_checkout_q: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)

@dp.message(F.successful_payment)
async def sucessfull_payment(message:Message):

    message_send = 0
    now = datetime.datetime.now()
    current_time = now.strftime("%d-%m-%Y")
    user_id = str(message.from_user.id)
    users_list_query = "SELECT * FROM Users"
    cursor.execute(users_list_query)
    users_list = cursor.fetchall()
    print(users_list)
    for user in users_list:
        if user[0] == user_id:
            message_send = 1
            print(user[0])
    if message_send == 1:
        await message.answer(
            f"{hbold(message.from_user.full_name)}, Вы уже есть в списке, если бот не добавил Вас на канал, пожалуйста, напишите команду /help")
    else:
        await bot.unban_chat_member(chat_id_channel, user_id)
        await bot.unban_chat_member(chat_id_group, user_id)
        date_sub_end = add_months(datetime.datetime.now(), 0)
        cursor.execute('INSERT INTO Users (userid, date) VALUES (?, ?)', (f'{user_id}', f'{date_sub_end}'))
        await message.answer(f"Вы успешно оформили подписку на Канал!")
    print(users_list)

async def main() -> None:
    bot = Bot(token, parse_mode=ParseMode.HTML)
    task1 = asyncio.create_task(periodic())
    await dp.start_polling(bot)
    await task1

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())