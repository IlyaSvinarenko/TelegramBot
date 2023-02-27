import SqlManagerTableUsers, NumsFacts, Weather
from translate import Translator
from aiogram import Bot, Dispatcher
from aiogram.filters import Command, Text
from aiogram.types import Message, ContentType
from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, \
    InlineKeyboardButton, CallbackQuery

translator = Translator(to_lang='ru')
bot_token =
bot = Bot(token=bot_token)
dp = Dispatcher()


# OWNER_ID =
@dp.message(Command(commands=['menu']))
async def menu(message: Message):
    """ Создает инлайн_меню, кнопки вида 'Имя_функции - Включена/выключена'  """
    sql_table = SqlManagerTableUsers.TableManager()
    funcs_on = []
    funcs_off = []
    for func, state in sql_table.get_all_funcs_info_in_chat(message.chat.id).items():
        if state:
            funcs_on.append(func)
        else:
            funcs_off.append(func)
    inline_menu = InlineKeyboardMarkup(row_width=2,
                                       inline_keyboard=[
                                           [InlineKeyboardButton(text=f'{func_on} - On',
                                                                 callback_data=f'{func_on} on')
                                            for func_on in funcs_on],
                                           [InlineKeyboardButton(text=f'{func_off} - Off',
                                                                 callback_data=f'{func_off} off')
                                            for func_off in funcs_off]])
    await message.answer('Functions  -  status', reply_markup=inline_menu)


@dp.callback_query(lambda call: call)
async def callback_from_menu(call: CallbackQuery):
    """ В зависимости от того что было нажато в инлайн_меню изменяет значения в таблице funcs
    на 1 или 0 (вкл/выкл)"""
    sql_table_funcs = SqlManagerTableUsers.TableManager()
    call_data = call.data.split()  # [0] - func name, [1] - on or off
    if call_data[1] == 'on':
        sql_table_funcs.turn_off(call.message.chat.id, call_data[0])
    elif call_data[1] == 'off':
        sql_table_funcs.turn_on(call.message.chat.id, call_data[0])


@dp.message()
async def definition_func(message: Message):
    """ Перехватывает все сообщения и в зависимости от того какая функция чата сейчас включена,
    передает сообщение в вункии дальше"""
    sql_table_funcs = SqlManagerTableUsers.TableManager()
    if message.chat.type != 'private' and sql_table_funcs.is_active_func(message.chat.id, 'table_users'):
        await action_with_table_users(message)
    elif message.text.isdigit() and sql_table_funcs.is_active_func(message.chat.id, 'nums_fact'):
        await nums_facts(message)
    elif sql_table_funcs.is_active_func(message.chat.id, 'weather'):
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
        await bot.send_message(message.chat.id, 'Я ждал название города, кажется что-то пошло не так')


dp.run_polling(bot)
