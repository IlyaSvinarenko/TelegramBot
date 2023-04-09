import mongodb, SqlTables, main, GPT, time, logging, os
from aiogram.types import Message, InlineKeyboardMarkup, \
    InlineKeyboardButton, CallbackQuery

log_level = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(level=log_level, format='%(asctime)s %(levelname)s %(message)s')


'''//////////////// Дальше блок контекстовых меню /////////////'''


async def contexts_menu(message: Message):
    obj = mongodb.MongoForBotManager()
    contexts = await obj.get_contexts_data(str(message.chat.id))
    try:
        del GPT.current_contexts[str(message.chat.id)]
    except:
        pass
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
            if len(await obj.get_contexts_data(message.chat.id)) <= 4 else InlineKeyboardButton(text='Достигнут лимит контекстов',
                                                                                               callback_data='contexts createnew')
        inline_menu.add(delete_context_btn, create_context_btn)
    await message.answer('Контексты в этом чате: ', reply_markup=inline_menu)


async def create_delete_menu(message: Message):
    obj = mongodb.MongoForBotManager()
    contexts = await obj.get_contexts_data(str(message.chat.id))
    if GPT.current_contexts.get(str(message.chat.id)):
        del GPT.current_contexts[str(message.chat.id)]
    buttons_names = [i[0] for i in contexts]
    logging.info('columns: %s', buttons_names)
    inline_menu = InlineKeyboardMarkup(row_width=2, inline_keyboard=[
        [InlineKeyboardButton(text=f'{i}', callback_data=f'contexts delete {i}')] for i in buttons_names])
    back_to_context_menu = InlineKeyboardButton(text='Вернуться к выбору контекста', callback_data='contexts '
                                                                                                  'backtocontextmenu')
    inline_menu.add(back_to_context_menu)

    await main.bot.send_message(message.chat.id, 'Выберите контекст для удаления: ', reply_markup=inline_menu)


async def callback_from_contexts_menu(call: CallbackQuery):
    obj = mongodb.MongoForBotManager()
    call_text = call.data[9::]  # Отрезаем лишнюю часть текста "menu2 "
    if call_text == 'createnew':
        if len(await obj.get_contexts_data(call.message.chat.id)) < 5:

            await call.message.answer("Введите первый запрос.\n"
                                      "Название контекста будет заполнено по первым словам вашего запроса.\n"
                                      "Вы сразу окажетесь в контексте который был задан вашим запросом")
            return 1
        else:
            await call.message.answer("Достигнут лимит в 5 контекстов, сначала удалите один из контекстов")
            return 0
    elif call_text == 'delete':
        await main.bot.delete_message(call.message.chat.id, call.message.message_id)
        time.sleep(1)
        await create_delete_menu(call.message)
    elif call_text == 'backtocontextmenu':
        await main.bot.delete_message(call.message.chat.id, call.message.message_id)
        time.sleep(1)
        await contexts_menu(call.message)
    elif call_text.split()[0] == 'delete':
        await obj.delete_context(call.message.chat.id, ' '.join(call_text.split()[1::]))
        await main.bot.delete_message(call.message.chat.id, call.message.message_id)
        time.sleep(1)
        await create_delete_menu(call.message)
    else:
        await call.message.answer(f'Выбран контекст: {call_text}')
        GPT.current_contexts[str(call.message.chat.id)] = call_text
    return 0

'''//////////////// Дальше блок меню функций /////////////'''


async def funcs_menu(message: Message):
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
    await funcs_menu(call.message)
