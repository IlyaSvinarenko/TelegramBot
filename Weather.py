"""Погода для бота"""
import pyowm, os
from pyowm.utils.config import get_default_config
owm = pyowm.OWM(os.environ.get('OWM_api_key'))  # Это для OpenWeatherMap
config_dict = get_default_config()  # Это для OpenWeatherMap

def get_weather(text):
    mgr = owm.weather_manager()
    observation = mgr.weather_at_place(text)
    w = observation.weather
    answer = 'В городе ' + text + ' сегодня ' + w.detailed_status + '\n'
    answer += 'Средняя температура сегодня: ' + str(w.temperature('celsius')['temp']) + ' C°' + '\n'
    answer += 'Скорость ветра (м/с): ' + str(w.wind()['speed']) + '\n'
    answer += 'Не благодари, братишка:)'
    return answer
