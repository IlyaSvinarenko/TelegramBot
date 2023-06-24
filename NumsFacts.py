"""Факты о цифрах для бота"""
import requests

NumApiUrl = 'http://numbersapi.com/{}/{}?json'
list_of_answers = ['math', 'trivia', 'date']


def Facts_about_num(num):
    answer = ''
    for i in range(3):
        res = requests.get(NumApiUrl.format(num, list_of_answers[i]))
        if res.json()['found']:
            answer += f"-{res.json()['text']} \n\n"
        else:
            continue
    return answer

