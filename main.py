import SqlTables, NumsFacts, Weather, os, GPT, MenuTelegram, logging, Parser_game_price
from translate import Translator
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, CallbackQuery, ChatActions
from aiogram.utils import executor


translator = Translator(to_lang='ru')
bot_token = os.environ.get('Son_of_Ilya_bot')
bot = Bot(token=bot_token)
dp = Dispatcher(bot)

log_level = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(level=log_level, format='%(asctime)s %(levelname)s %(message)s')

in_creating_context = {}

'''/////////////// Перехватчики команд для вызовов меню и колбеков от меню //////////////////'''


@dp.message_handler(lambda message: message.text.startswith('img'))
async def make_image(message: Message):
    logging.info('in main / def make_image')
    prompt = await GPT.prompt_editor_for_img_generator(' '.join(message.text.split()[1::]))
    image_byte_arr = await GPT.get_image_byte_arr(prompt)
    await bot.send_photo(message.chat.id, photo=image_byte_arr)


@dp.message_handler(commands=['contexts'])
async def get_contexts_menu(message: Message):
    logging.info('in main / def get_contexts_menu')
    if in_creating_context.get(str(message.chat.id)):
        in_creating_context[(str(message.chat.id))] = 0
    if GPT.current_contexts.get(str(message.chat.id)):
        del GPT.current_contexts[(str(message.chat.id))]
    await MenuTelegram.create_contexts_menu(message)


@dp.callback_query_handler(lambda query: query.data.startswith('contexts'))
async def callback_from_contexts_menu(call: CallbackQuery):
    logging.info(f'in main / def callback_from_contexts_menus: \n'
                 f'callback == {call}')
    in_creating_context[str(call.message.chat.id)] = await MenuTelegram.callback_from_contexts_menu(call)


@dp.callback_query_handler(lambda query: query.data.startswith('delete'))
async def callback_from_delete_menu(call: CallbackQuery):
    logging.info(f'in main / def callback_from_delete_menu: \n'
                 f'callback == {call}')
    in_creating_context[str(call.message.chat.id)] = 0
    await MenuTelegram.callback_from_delete_menu(call)


@dp.message_handler(commands=['menu'])
async def get_funcs_menu(message: Message):
    logging.info('in main / def get_funcs_menu')
    await MenuTelegram.create_funcs_menu(message)


@dp.callback_query_handler(lambda query: query.data.startswith('funcs'))
async def callback_from_funcs_menu(call: CallbackQuery):
    logging.info(f'in main / def callback_from_funcs_menu: \n'
                 f'callback == {call}')
    await MenuTelegram.callback_from_funcs_menu(call)


@dp.message_handler(commands=['help', 'start'])
async def help(message: Message):
    logging.info('in main / def help')
    await message.answer('Commands:\n 1) /help \n 2) /menu \n 3) /contexts \n'
                         'Команда /menu открывает меню функций в чате.\n'
                         'слева в меню - название функции бота\n'
                         'справа - состояния (1-включена | 0-выключена)\n'
                         'Нажатие на функцию меняет ее состояние в данном чате\n\n'
                         'Функция table_users: Бот отслеживает и удаляет участников чата, которые были неактивны в '
                         'течении 30-ти дней\n\n'
                         'Функция nums_fact: В ответ на целое положительное число, отправленное в чат, бот пришлет 2-3 '
                         'факта связанных с этим числом\n\n'
                         'Функция weather: В ответ на отправленное в чат название населенного пункта, бот пришлет '
                         'погоду в данном населенном пункте\n\n'
                         'Функция openai включает возможности ИИ от одноименной компании для '
                         'общения в чате (модель: gpt-4)')


'''/////////////// Перехватчик обновлений добавления и удаления юзеров из чата //////////////////'''


@dp.message_handler(content_types=['new_chat_members'])
async def on_user_join(message: types.Message):
    logging.info('in main / def on_user_join')
    sql_table_funcs = SqlTables.TableManager()
    for user in message.new_chat_members:
        await bot.send_message(message.chat.id, f"Добро пожаловать на борт '{message.chat.title}', @{user.username}!"
                                                f"")
        if sql_table_funcs.is_active_func(message.chat.id, 'table_users'):
            await action_with_table_users(user_id=user['id'], chat_id=message.chat.id, username=user['username'],
                                          first_name=user['first_name'])


@dp.message_handler(content_types=['left_chat_member'])
async def on_left_chat_member(message: types.Message):
    logging.info('in main / def on_left_chat_member')
    manager = SqlTables.TableManager()
    manager.del_user(message.left_chat_member.id)
    if message.left_chat_member:
        await bot.send_message(message.chat.id, f"Интернет тебе пухом.\n"
                                                f" Пусть другие чаты будут к тебе добрее чем мы,"
                                                f" {message.left_chat_member.first_name}!")


'''/////////////// Перехватчик сообщений и функции обработки сообщений //////////////////'''


@dp.message_handler()
async def definition_func(message: Message):
    logging.info(f'in main / definition_func: \n'
                 f'message.chat.type == {message.chat.type}\n'
                 f'message.content_type == {message.content_type}\n'
                 f'message.text == {message.text}')
    """ Перехватывает все сообщения и в зависимости от того какая функция чата сейчас включена,
    передает сообщение в функии дальше"""
    sql_table_funcs = SqlTables.TableManager()
    if message.chat.type != 'private' and sql_table_funcs.is_active_func(message.chat.id, 'table_users'):
        await action_with_table_users(user_id=message.from_user.id, chat_id=message.chat.id, username=
        message.from_user.username, first_name=message.from_user.first_name)
    if message.content_type == 'text':
        if message.text.isdigit() and sql_table_funcs.is_active_func(message.chat.id, 'nums_fact'):
            await nums_facts(message)
        elif sql_table_funcs.is_active_func(message.chat.id, 'weather'):
            await get_weather(message)
        elif sql_table_funcs.is_active_func(message.chat.id, 'openai'):
            await openai_chatting(message)
        elif sql_table_funcs.is_active_func(message.chat.id, 'game_price'):
            response = await Parser_game_price.find_steam_game(message)
            await message.answer(response)

async def openai_chatting(message):
    await bot.send_chat_action(chat_id=message.chat.id, action=ChatActions.TYPING)
    logging.info(f'in main / def openai_chatting \n'
                 f'in_creating_context == {in_creating_context}')
    if in_creating_context.get(str(message.chat.id)) == 1:
        gpt_answer = await GPT.get_response(message.text, message.chat.id, in_creating_process=1)
        in_creating_context[str(message.chat.id)] = 0
        await message.answer(gpt_answer)
    else:
        gpt_answer = await GPT.get_response(message.text, message.chat.id)
        await message.answer(gpt_answer)


async def action_with_table_users(user_id, chat_id, username, first_name):
    """ Если включена:
     обновляет данные о последней активности юзеров в чате, удаляет неактивных юзеров"""
    sql_table = SqlTables.TableManager()
    if sql_table.get_user_info(user_id):
        # Порядок заполненности (get_user_info):
        # [0]-user_id, [1]-date_time_UTC, [2]-user_name, [3] date_in_seсonds, [4] - chat_id,
        # [5] - deletion_warning_time
        sql_table.update_last_aktivity(user_id, chat_id)
    else:
        sql_table.add_user(user_id, username, chat_id)
        await bot.send_message(chat_id, f'{first_name} улыбайся, тебя только что добавили в базу данных!')
    for user_id_name_chat in sql_table.find_not_active_users(chat_id):
        await bot.send_message(chat_id, f"{user_id_name_chat[1]} подлежит удалению из чата")
        await bot.send_message(chat_id, f"@{user_id_name_chat[1]}, Я УДАЛЮ ТЕБЯ ИЗ ГРУППЫ если ничего не напишешь!\nУ "
                                        f"тебя "
                                        f"есть 24 часа!")
    for user in sql_table.list_of_users_to_remove():  # [0]-id, [1]-user_name
        await bot.send_message(chat_id, f"{user[1]} Именем Господнем, я изгоняю тебя из чата!")
        await bot.kick_chat_member(chat_id, user[0])


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
        logging.info('При включенной функции weather, вероятно было введено не название населенного пункта')


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
