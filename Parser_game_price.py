import requests
from bs4 import BeautifulSoup


def find_steam_game_no_async(game_name: str):
    """ Возвращает кортеж (game_link, game_name, price, discount)"""
    search_url = "https://store.steampowered.com/search/"
    params = {
        'term': game_name
    }

    response = requests.get(search_url, params=params)
    soup = BeautifulSoup(response.text, 'html.parser')
    game_link = soup.find('a', class_='search_result_row')
    if game_link:
        game_link = game_link['href']
    # game_link = soup.find('a', class_='search_result_row')['href']
    if game_link:
        game_info = get_game_info_no_async(game_name, game_link)
        return game_info
    else:
        return "Игра не найдена"


async def find_steam_game_async(game_name: str):
    """ Возвращает кортеж (game_link, game_name, price, discount)"""
    search_url = "https://store.steampowered.com/search/"
    params = {
        'term': game_name
    }

    response = requests.get(search_url, params=params)
    soup = BeautifulSoup(response.text, 'html.parser')
    game_link = soup.find('a', class_='search_result_row')['href']
    if game_link:
        game_info = get_game_info(game_name, game_link)
        return await game_info
    else:
        return "Игра не найдена"

def get_game_info_no_async(game_name, game_link):
    game_response = requests.get(game_link)
    game_soup = BeautifulSoup(game_response.text, 'html.parser')

    price = game_soup.find('div', class_='game_purchase_price')
    discount_price = game_soup.find('div', class_='discount_final_price')
    discount_percentage = game_soup.find('div', class_='discount_pct')

    if discount_price and discount_percentage:
        price = discount_price.text.strip()
        discount = discount_percentage.text.strip()
    else:
        price = price.text.strip() if price else "Цена не указана"
        discount = "Скидка отсутствует"

    return game_link, game_name, price, discount
async def get_game_info(game_name, game_link):
    game_response = requests.get(game_link)
    game_soup = BeautifulSoup(game_response.text, 'html.parser')

    price = game_soup.find('div', class_='game_purchase_price')
    discount_price = game_soup.find('div', class_='discount_final_price')
    discount_percentage = game_soup.find('div', class_='discount_pct')

    if discount_price and discount_percentage:
        price = discount_price.text.strip()
        discount = discount_percentage.text.strip()
    else:
        price = price.text.strip() if price else "Цена не указана"
        discount = "Скидка отсутствует"

    return game_link, game_name, price, discount
