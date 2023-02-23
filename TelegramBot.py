import SqlManagerTableUsers
from aiogram import Bot, Dispatcher
from aiogram.filters import Command, Text
from aiogram.types import Message, ContentType
from translate import Translator
import time

translator = Translator(to_lang='ru')
bot_token =
bot = Bot(token=manager_of_world_bot_token)
dp = Dispatcher()
bot_id =
OWNER_ID =


@dp.message()
async def action_with_table_users(message: Message):
    if message.chat.type != 'private':
        sql_table = SqlManagerTableUsers.TableManager()
        if sql_table.get_user_info(message.from_user.id) != False:
            # Порядок заполненности (get_user_info):
            # [0]-user_id, [1]-date_time_UTC, [2]-user_name, [3] date_in_seсonds, [4] - chat_id,
            # [5] - deletion_warning_time
            sql_table.update_last_aktivity(message.from_user.id, message.chat.id)
        else:
            sql_table.add_user(message.from_user.id, message.from_user.username, message.chat.id)
            await message.answer(f'{message.from_user.first_name} улыбайся, тебя только что добавили в базу данных!')
        for user_id_name_chat in sql_table.find_not_active_users(message.chat.id):
            await message.answer(f"{user_id_name_chat[1]} подлежит удалению из чата")
            await message.answer(f"@{user_id_name_chat[1]}, Я УДАЛЮ ТЕБЯ ИЗ ГРУППЫ если ничего не напишешь!\nУ тебя "
                                 f"есть 24 часа!")
        for user in sql_table.list_of_users_to_remove():  # [0]-id, [1]-user_name
            await bot.send_message(message.chat.id, f"{user[1]} Именем Господнем, я изгоняю тебя из чата!")
            await bot.kick_chat_member(message.chat.id, user[0])


dp.run_polling(bot)
