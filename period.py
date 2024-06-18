import time, SqlTables, Parser_game_price
from datetime import datetime
import threading

def log_current_time(interval_seconds):
    while True:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(current_time)
        time.sleep(interval_seconds)
        update_all_game_info()

def update_all_game_info():
    sql_table = SqlTables.TableManager()
    # Получаем все game_link, price, discount из таблицы
    current_games_info = sql_table.get_all_game_info()
    new_game_data = []
    for game_info in current_games_info:
        link = game_info[1]
        current_price = game_info[3]
        current_discount = game_info[4]
        new_info = Parser_game_price.find_steam_game_no_async(link)
        if new_info[2] != current_price or new_info[3] != current_discount:
            new_game_data.append((link, new_info[2], new_info[3]))
        print(f" Parser_game_price.find_steam_game(link) : {game_info[2]}")
        print(f"new_game_data === {new_game_data}")
    for game in new_game_data:
        sql_table.update_one_game_info(game[0], game[1], game[2])
        print(f"data uppdated : {game[0], game[1], game[2]}")

time_thread = threading.Thread(target=log_current_time, args=(259200,)) 
time_thread.start()