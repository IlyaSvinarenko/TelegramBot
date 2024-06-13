import mongodb, SqlTables, main, GPT, time, logging, os
from aiogram.types import Message, InlineKeyboardMarkup, \
    InlineKeyboardButton, CallbackQuery

log_level = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(level=log_level, format='%(asctime)s %(levelname)s %(message)s')

'''//////////////// Дальше блок контекстовых меню /////////////'''


async def create_contexts_menu(message: Message):
    obj = mongodb.MongoForBotManager()
    contexts = await obj.get_contexts_data(message.chat.id)
    if GPT.current_contexts.get(str(message.chat.id)):
        del GPT.current_contexts[str(message.chat.id)]
    if len(contexts) == 0:
        inline_menu = InlineKeyboardMarkup(row_width=2, inline_keyboard=[[InlineKeyboardButton(text='Создать новый '
                                                                                                    'контекст',
                                                                                               callback_data=f'contexts createnew')]])
    else:
        buttons_names = [i[0] for i in contexts]
        inline_menu = InlineKeyboardMarkup(row_width=2, inline_keyboard=[
            [InlineKeyboardButton(text=f'{i}', callback_data=f'contexts {i}')] for i in buttons_names])
        delete_context_btn = InlineKeyboardButton(text='Удаление контекстов', callback_data='contexts delete')
        create_context_btn = InlineKeyboardButton(text='Создать новый контекст', callback_data='contexts createnew') \
            if len(await obj.get_contexts_data(message.chat.id)) <= 4 else InlineKeyboardButton(
            text='Достигнут лимит контекстов',
            callback_data='contexts createnew')
        inline_menu.add(delete_context_btn, create_context_btn)
    await message.answer('Контексты в этом чате: ', reply_markup=inline_menu)


async def callback_from_contexts_menu(call: CallbackQuery):
    obj = mongodb.MongoForBotManager()
    call_data = call.data.split()
    call_data = call_data[1::]  # Отрезаем лишнюю часть "context"
    logging.info(f"in MenuTelegram / def callback_from_contexts_menu: \n call_data == {call_data} \n callback =="
                 f" {call}")
    if call_data[0] == 'createnew':
        if len(await obj.get_contexts_data(call.message.chat.id)) < 5:

            await call.message.answer("Введите первый запрос.\n"
                                      "Название контекста будет заполнено по первым словам вашего запроса.\n"
                                      "Вы сразу окажетесь в контексте который был задан вашим запросом")
            return 1
        else:
            await call.message.answer("Достигнут лимит в 5 контекстов, сначала удалите один из контекстов")
            return 0
    elif call_data[0] == 'delete':
        await main.bot.delete_message(call.message.chat.id, call.message.message_id)
        time.sleep(1)
        await create_delete_menu(call)
    else:
        await call.message.answer(f'Выбран контекст: {call_data[0]}')
        GPT.current_contexts[str(call.message.chat.id)] = call_data[0]
    return 0


'''//////////////// Дальше блок меню удаления контекстов /////////////'''


async def create_delete_menu(call: CallbackQuery):
    chat_id = call.message.chat.id
    obj = mongodb.MongoForBotManager()
    contexts = await obj.get_contexts_data(chat_id)
    if GPT.current_contexts.get(str(chat_id)):
        del GPT.current_contexts[str(chat_id)]
    buttons_names = [i[0] for i in contexts]
    logging.info('in MenuTelegram / def create_delete_menu: \n buttons == %s', buttons_names)
    inline_menu_delete = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=f'{i}',
                                                                                     callback_data=f'delete delete {i}')] for i
                                                               in buttons_names])
    back_to_context_menu = InlineKeyboardButton(text='Вернуться к выбору контекста', callback_data='delete '
                                                                                                   'backtocontextmenu')
    inline_menu_delete.add(back_to_context_menu)
    await main.bot.send_message(chat_id, 'Выберите контекст для удаления: ', reply_markup=inline_menu_delete)


async def callback_from_delete_menu(call: CallbackQuery):
    obj = mongodb.MongoForBotManager()
    call_data = call.data.split()
    call_data = call_data[1::]  # Отрезаем лишнюю часть "delete"
    logging.info(f'in MenuTelegram / def callback_from_delete_menu: \n call_data == {call_data}')
    if call_data[0] == 'backtocontextmenu':
        await main.bot.delete_message(call.message.chat.id, call.message.message_id)
        time.sleep(1)
        await create_contexts_menu(call.message)
    elif call_data[0] == 'delete':
        print(' '.join(call_data[1::]))
        await obj.delete_context(call.message.chat.id, ' '.join(call_data[1::]))
        await main.bot.delete_message(call.message.chat.id, call.message.message_id)
        await create_delete_menu(call)



'''//////////////// Дальше блок меню функций /////////////'''


async def create_funcs_menu(message: Message):
    sql_table = SqlTables.TableManager()
    funcs = []
    for func, state in sql_table.get_all_funcs_info_in_chat(message.chat.id).items():
        funcs.append(str(func) + ' ' + str(state))
    inline_menu = InlineKeyboardMarkup(row_width=2,
                                       inline_keyboard=[
                                           [InlineKeyboardButton(text=f'{func}',
                                                                 callback_data=f'funcs {func}')
                                            ] for func in funcs])
    await message.answer('Functions  -  status', reply_markup=inline_menu)


async def callback_from_funcs_menu(call: CallbackQuery):
    """ В зависимости от того что было нажато в инлайн_меню изменяет значения в таблице funcs
    на 1 или 0 (вкл/выкл)"""
    sql_table_funcs = SqlTables.TableManager()
    call_data = call.data.split()  # [1] - func name, [2] - 1 or 0   (on/off)
    if call_data[2] == '1':
        sql_table_funcs.turn_off(call.message.chat.id, call_data[1])
    elif call_data[2] == '0':
        sql_table_funcs.turn_on(call.message.chat.id, call_data[1])
    await main.bot.delete_message(call.message.chat.id, call.message.message_id)
    time.sleep(1)
    await create_funcs_menu(call.message)

async def create_subscribe_menu(message: Message):
    """создаем меню"""

    inline_menu = InlineKeyboardMarkup(row_width=2,
                                       inline_keyboard=[
                                           [InlineKeyboardButton(text='да',
                                                                 callback_data=f'subscribe yes')],
                                            [InlineKeyboardButton(text='нет',
                                                                 callback_data='subscribe no')]])
    await message.answer(f'Хотите ли подписаться на обновления по игре {message.text}', reply_markup=inline_menu)

async def callback_from_subscribe_menu(call: CallbackQuery):
    call_data = call.data.split()
    if call_data[1] == 'yes':
        print('yes')
    elif call_data[1] == 'no':
        print('no')
