import SqlManagerTableUsers, NumsFacts, Weather, time, os
from translate import Translator
from aiogram import Bot, Dispatcher
from aiogram.filters import Command, Text
from aiogram.types import Message, ContentType
from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, \
    InlineKeyboardButton, CallbackQuery
translator = Translator(to_lang='ru')
bot_token = os.environ.get('Son_of_Ilya_bot')
bot = Bot(token=bot_token)
dp = Dispatcher()

@dp.message(Command(commands=['help', 'start']))
async def help(message: Message):
    await message.answer(bot.id)
    await message.answer('Команда /menu открывает меню функций в чате.\n'
                         'слева в меню - название функции бота\n'
                         'справа - состояния (1-включена | 0-выключена)\n'
                         'Нажатие на функцию меняет ее состояние в данном чате\n\n'
                         'Функция table_users: Бот отслеживает и удаляет участников чата, которые были неактивны в '
                         'течении 30-ти дней\n\n'
                         'Функция nums_fact: В ответ на целое положительное число, отправленное в чат, бот пришлет 2-3 '
                         'факта связанных с этим числом\n\n'
                         'Функция weather: В ответ на отправленное в чат название населенного пункта, бот пришлет '
                         'погоду в данном населенном пункте\n\n')


@dp.message(Command(commands=['menu']))
async def menu(message: Message):
    sql_table = SqlManagerTableUsers.TableManager()
    funcs = []
    for func, state in sql_table.get_all_funcs_info_in_chat(message.chat.id).items():
        funcs.append(str(func) + ' ' + str(state))
    inline_menu = InlineKeyboardMarkup(row_width=2,
                                       inline_keyboard=[
                                           [InlineKeyboardButton(text=f'{func}',
                                                                 callback_data=f'{func}')
                                            ] for func in funcs])
    await message.answer('Functions  -  status', reply_markup=inline_menu)


@dp.callback_query(lambda call: call)
async def callback_from_menu(call: CallbackQuery):
    """ В зависимости от того что было нажато в инлайн_меню изменяет значения в таблице funcs
    на 1 или 0 (вкл/выкл)"""
    sql_table_funcs = SqlManagerTableUsers.TableManager()
    call_data = call.data.split()  # [0] - func name, [1] - 1 or 0   (on/off)
    if call_data[1] == '1':
        sql_table_funcs.turn_off(call.message.chat.id, call_data[0])
    elif call_data[1] == '0':
        sql_table_funcs.turn_on(call.message.chat.id, call_data[0])
    await bot.delete_message(call.message.chat.id, call.message.message_id)
    time.sleep(1)
    await menu(call.message)


@dp.message()
async def definition_func(message: Message):
    """ Перехватывает все сообщения и в зависимости от того какая функция чата сейчас включена,
    передает сообщение в вункии дальше"""
    sql_table_funcs = SqlManagerTableUsers.TableManager()
    if message.chat.type != 'private' and sql_table_funcs.is_active_func(message.chat.id, 'table_users'):
        await action_with_table_users(message)
    if message.text.isdigit() and sql_table_funcs.is_active_func(message.chat.id, 'nums_fact'):
        await nums_facts(message)
    if sql_table_funcs.is_active_func(message.chat.id, 'weather'):
        await get_weather(message)


async def action_with_table_users(message: Message):
    """ Если включена:
     обновляет данные о последней активности юзеров в чате, удаляет неактивных юзеров"""
    sql_table = SqlManagerTableUsers.TableManager()
    if sql_table.get_user_info(message.from_user.id):
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


async def nums_facts(message: Message):
    """ Если включена:
    Если сообщение состоит из целого положительного числа: отвечает на такое сообщение интересными фактами об этом числе"""
    try:
        await bot.send_message(message.chat.id, translator.translate(NumsFacts.Facts_about_num(message.text)))
    except:
        await bot.send_message(message.chat.id, 'Кажется что-то пошло не так')


async def get_weather(message: Message):
    """ Если включена:
    отвечает на сообщение погодой в целевом городе,
    если текст сообщения не название города, то отвечает недоумением"""
    try:
        await bot.send_message(message.chat.id, Weather.get_weather(message.text))
    except:
        print('При включенной функции weather, вероятно было введено не название населенного пункта')

if __name__ == '__main__':
    dp.run_polling(bot)