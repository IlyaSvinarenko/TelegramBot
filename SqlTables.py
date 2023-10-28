import sqlite3, os, logging
import time

log_level = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(level=log_level, format='%(asctime)s %(levelname)s %(message)s')


dataclass_chat_funcs: dict[dict] = dict()

bot_id: int = os.environ.get('Son_of_Ilya_bot_id')  # Нужно для того чтобы бот сам себя случайно не добавлял в
# таблицу users

time_line_segment = 2592000
# == 30дней == (((((1)сек * 60)мин * 60)час * 24)день * 30)месяц == 2 592 000 сек


'''Класс для работы с базой данных в (предположительно через телеграм-бота)'''


class TableManager:
    def __init__(self):
        self.connect = sqlite3.connect('Telegram_Bot_DB.db')
        self.coursor = self.connect.cursor()

    """/////////////////////////// Дальше универсальный блок для таблиц users и funcs ///////////////////////////////"""

    def delete_table(self, table_name):
        self.coursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        logging.info(" ТЫ ЗАЧЕМ ТАБЛИЦУ УДАЛИЛ!!?!?!?")

    def clear_table(self, table_name):
        self.coursor.execute(f"DELETE FROM {table_name}")
        logging.info(f"table {table_name} cleared")
        return self.connect.commit()

    """/////////////////////////// Дальше блок по таблице users ///////////////////////////////"""

    def add_user(self, user_id, username, chat_id):
        current_time_sec = time.time()
        UTC_Current_time = time.strftime("%d/%m/%Y, %H:%M:%S", time.localtime(current_time_sec))
        if user_id == bot_id:  # Это чтобы бот не добавлял сам себя в таблицу
            logging.info("Ой, я пытался сам себя занести в таблицу")
            return
        try:
            self.coursor.execute("INSERT INTO users "
                                 "(user_id, date_time_UTC, user_name, date_in_seconds, chat_id, deletion_warning_time)"
                                 " VALUES (?, ?, ?, ?, ?, ?)",
                                 (user_id, UTC_Current_time, username, current_time_sec, chat_id, 0))
            logging.info(f'user {username}  id: {user_id} added to data base\n with datetime: {UTC_Current_time}')
        except sqlite3.Error as error:
            logging.info("Error", error)
            return False
        return self.connect.commit()

    def get_user_info(self, user_id):
        result = self.coursor.execute(f"SELECT * FROM users WHERE user_id = {user_id}")
        result = result.fetchone()
        if result is None:
            return False
        else:
            return result

    def update_last_aktivity(self, user_id, chat_id):
        """ Думаю по названию понятно что происходит """
        current_time_sec = time.time()
        UTC_Current_time = time.strftime("%d/%m/%Y, %H:%M:%S", time.localtime(current_time_sec))
        self.coursor.execute("UPDATE users SET "
                             "date_time_UTC = ?, date_in_seconds = ?, chat_id = ?, deletion_warning_time = 0 WHERE "
                             "user_id = ?",
                             (UTC_Current_time, current_time_sec, chat_id, user_id))
        username = self.coursor.execute(f"SELECT user_name FROM users WHERE user_id = {user_id}")
        logging.info(f"data_time_UTC updated for user {username.fetchone()[0]} in table 'users'")
        return self.connect.commit()

    def find_not_active_users(self, chat_id):
        """ Находит юзеров в таблице users у которых дата последней активности старее 30-ти дней,
        задает таким юзерам deletion_warning_time == текущему времени,
        и возвращает сет из кортежей (user_id, user_name, chat_id)
        чтобы в чате произошло уведомление о не активности таких юзеров"""
        set_of_users_id_name_chat = set()
        current_time_sec = time.time()
        rows = self.coursor.execute(f'SELECT * FROM users WHERE chat_id = {chat_id}').fetchall()
        for row in rows:
            user_id, user_name, last_activity, deletion_warning = row[0], row[2], row[3], row[5]
            if (last_activity + time_line_segment < current_time_sec) and deletion_warning == 0:
                self.coursor.execute(f"UPDATE users SET deletion_warning_time = {current_time_sec}")
                self.connect.commit()
                set_of_users_id_name_chat.add((user_id, user_name, chat_id))
        return set_of_users_id_name_chat

    def del_user(self, user_id):
        self.coursor.execute(f"DELETE FROM users WHERE user_id = {user_id}")
        return self.connect.commit()

    def list_of_users_to_remove(self):
        """ Проверяет таблицу users на наличие юзеров у которых
        время_предупреждения_об_удалении(deletion_warning_time) старее одного дня,
        К каждому такому юзеру применяет удаление их данных из таблицы.
        И возвращает список из кортежей (user_id, user_name) для дальнейшего удаления из чата"""
        current_time_sec = time.time()

        def del_user(user_id):
            self.coursor.execute(f"DELETE FROM users WHERE user_id = {user_id}")
            return self.connect.commit()

        users_id_to_remove = self.coursor.execute(f"SELECT user_id, user_name FROM users WHERE "
                                                  f"deletion_warning_time > 0 AND {current_time_sec} >= "
                                                  f"deletion_warning_time + 86400").fetchall()  # 1 day == 86400 sec
        removed_users = []
        for user in users_id_to_remove:
            user_id, user_name = user[0], user[1]
            del_user(user_id)
            removed_users.append((user_id, user_name))
        return removed_users

    def create_table_users(self):
        ''' Шаблончик таблицы users  с полями
        (user_id, date_time_UTC, user_name, date_in_seсonds, chat_id, deletion_warning_time)'''
        try:
            self.coursor.execute("""CREATE TABLE IF NOT EXISTS users (
            user_id INT NOT NULL UNIQUE,
            date_time_UTC DATETIME NOT NULL,
            user_name TEXT NOT NULL UNIQUE,
            date_in_seconds REAL NOT NULL,
            chat_id INT NOT NULL,
            deletion_warning_time REAL);""")
            self.connect.commit()
        except sqlite3.Error as error:
            logging.info("ERROR", error)

    """/////////////////////////// Дальше блок по таблице funcs ///////////////////////////////"""

    def create_table_funcs(self):
        '''шаблон для создания таблицы funcs с полями:
        (chat_id, table_users, weather, nums_fact, openai)'''
        try:
            self.coursor.execute("""CREATE TABLE IF NOT EXISTS funcs (
            chat_id INT UNIQUE,
            table_users INT NOT NULL DEFAULT 0,
            weather INT NOT NULL DEFAULT 0,
            nums_fact INT NOT NULL DEFAULT 0,
            openai INT NOT NULL DEFAULT 0);""")
            self.connect.commit()
        except sqlite3.Error as error:
            logging.info('Error:', error)

    def turn_on(self, chat_id, func):
        """ Задает значение == 1 в поле func, где чат_ай-ди == chat_id
        Этим самым записывает состояние функции в чате как включенной"""
        if self.coursor.execute(f"SELECT chat_id FROM funcs"
                                f" WHERE chat_id = {chat_id}").fetchone() == None:
            self.coursor.execute("INSERT INTO funcs (chat_id) VALUES (?)", (chat_id,))
        self.coursor.execute(f"UPDATE funcs SET {func} = 1 WHERE chat_id = {chat_id}")
        self.connect.commit()
        logging.info(f"{func} - 0n   chat: {chat_id}")

    def turn_off(self, chat_id, func):
        """ Задает значение == 0 в поле func, где чат_ай-ди == chat_id
        Этим самым записывает состояние функции в чате как выключенной"""
        try:
            self.coursor.execute(f"UPDATE funcs SET {func} = 0 WHERE chat_id = {chat_id}")
        except sqlite3.Error as error:
            logging.info('Error:', error)
        self.connect.commit()
        logging.info(f'{func} - Off   chat: {chat_id}')

    def is_active_func(self, cat_id, func):
        """ Возвращает 1, если функция func в чате cat_id включена,
        Возвращает False если функция func в чате cat_id выключена"""
        try:
            is_active = self.coursor.execute(f"SELECT {func} FROM funcs WHERE chat_id = {cat_id}").fetchone()[0]
            self.connect.commit()
            return is_active
        except:
            self.connect.commit()
            return False

    def get_all_funcs_info_in_chat(self, chat_id):
        logging.info(' in sql get_all_funcs_info_in_chat: ')
        """Возвращает словарь в котором (ключ = название функции, значение = 1 или 0)
        Если значение == 1 --> значит функция в чате(chat_id) включена
        Если значение == 0 --> значит функция в чате(chat_id) ВЫключена"""
        info_about_chat_funcs = {}
        functions_names = []
        description = self.coursor.execute(f"SELECT * FROM funcs WHERE chat_id = {chat_id}").description
        if self.coursor.execute(f"SELECT chat_id FROM funcs"
                                f" WHERE chat_id = {chat_id}").fetchone() == None:
            self.coursor.execute("INSERT INTO funcs (chat_id) VALUES (?)", (chat_id,))
            self.connect.commit()
        for column in description[1::]:
            functions_names.append(column[0])
        for name in functions_names:
            info_about_chat_funcs[name] = \
                self.coursor.execute(f"SELECT {name} FROM funcs WHERE chat_id = {chat_id}").fetchone()[0]
        logging.info('columns: %s', info_about_chat_funcs)
        return info_about_chat_funcs

    def add_func_column(self, func_name):
        try:
            """ Это для упрощенного добавления колонок в таблицу funcs"""
            self.coursor.execute(f"ALTER TABLE funcs "
                                 f"ADD {func_name} INTEGER NOT NULL DEFAULT 0")
            self.connect.commit()
        except Exception as error:
            logging.info(str(error))


# object = TableManager()
# object.create_table_funcs()
# object.create_table_users()
# object.add_func_column('openai')