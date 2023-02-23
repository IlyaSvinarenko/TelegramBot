import sqlite3
import time

time_line_segment = 2592000
# == 30дней == (((((1)сек * 60)мин * 60)час * 24)день * 30)месяц == 2 592 000 сек
'''Класс для работы с базой данных в (предположительно через телеграм-бота)'''


class TableManager:
    def __init__(self):
        self.connect = sqlite3.connect('Telegram_Bot_DB.db')
        self.coursor = self.connect.cursor()

    def add_user(self, user_id, username, chat_id):
        current_time_sec = time.time()
        UTC_Current_time = time.strftime("%d/%m/%Y, %H:%M:%S", time.localtime(current_time_sec))
        if user_id == 5809889046:  # Это чтобы бот не добавлял сам себя в таблицу
            print("Ой, я пытался сам себя занести в таблицу")
            return
        try:
            self.coursor.execute("INSERT INTO users "
                                 "(user_id, date_time_UTC, user_name, date_in_seconds, chat_id, deletion_warning_time)"
                                 " VALUES (?, ?, ?, ?, ?, ?)",
                                 (user_id, UTC_Current_time, username, current_time_sec, chat_id, 0))
            print(f'user {username}  id: {user_id} added to data base\n with datetime: {UTC_Current_time}')
        except sqlite3.Error as error:
            print("Error", error)
            return False
        return self.connect.commit()

    def get_user_info(self, user_id):
        result = self.coursor.execute(f"SELECT * FROM users WHERE user_id = {user_id}")
        result = result.fetchone()
        if result is not None:
            return result
        else:
            return False

    def update_last_aktivity(self, user_id, chat_id):
        current_time_sec = time.time()
        UTC_Current_time = time.strftime("%d/%m/%Y, %H:%M:%S", time.localtime(current_time_sec))
        self.coursor.execute("UPDATE users SET "
                             "date_time_UTC = ?, date_in_seconds = ?, chat_id = ?, deletion_warning_time = 0 WHERE "
                             "user_id = ?",
                             (UTC_Current_time, current_time_sec, chat_id, user_id))
        username = self.coursor.execute(f"SELECT user_name FROM users WHERE user_id = {user_id}")
        print(f"data_time_UTC updated for user {username.fetchone()[0]} in table 'users'")
        return self.connect.commit()

    def find_not_active_users(self, chat_id):
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

    def list_of_users_to_remove(self):
        current_time_sec = time.time()

        def del_user(user_id):
            self.coursor.execute(f"DELETE FROM users WHERE user_id = {user_id}")
            return self.connect.commit()

        users_id_to_remove = self.coursor.execute(f"SELECT user_id, user_name FROM users WHERE "
                                                  f"deletion_warning_time > 0 AND {current_time_sec} >= "
                                                  f"deletion_warning_time + 86400").fetchall()         # 1 day == 86400
        # sec
        removed_users = []
        for user in users_id_to_remove:
            user_id, user_name = user[0], user[1]
            del_user(user_id)
            removed_users.append((user_id, user_name))
        return removed_users

    def clear_table(self):
        self.coursor.execute("DELETE FROM users")
        print("table 'users' cleared")
        return self.connect.commit()

    def delete_table(self):
        self.coursor.execute("DROP TABLE IF EXISTS users")
        print(" ТЫ ЗАЧЕМ ТАБЛИЦУ УДАЛИЛ!!?!?!?")

    def create_table(self):
        ''' Шаблончик таблицы users  с полями
        (user_id, date_time_UTC, user_name, date_in_seсonds, chat_id, deletion_warning_time)'''
        try:
            self.coursor.execute("""CREATE TABLE IF NOT EXISTS users (
            user_id INT NOT NULL UNIQUE,
            date_time_UTC DATETIME NOT NULL,
            user_name TEXT NOT NULL UNIQUE,
            date_in_seconds REAL NOT NULL,
            chat_id INT NOT NULL,
            deletion_warning_time INT);""")
            self.connect.commit()
        except sqlite3.Error as error:
            print("ERROR", error)


object = TableManager()
object.list_of_users_to_remove()