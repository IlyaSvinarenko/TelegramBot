import openai, os, mongodb, requests, logging

import io
from io import BytesIO
from aiogram import types

openai.api_key = os.environ.get("openai_api_key")

log_level = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(level=log_level, format='%(asctime)s %(levelname)s %(message)s')

current_contexts = {}


async def get_response(message_text, chat_id, in_creating_process=0):
    obj = mongodb.MongoForBotManager()
    global current_contexts
    for key, val in current_contexts.items():
        print(str(key), '  :  ', str(val))
    if in_creating_process:
        messages = [{'role': 'user', 'content': message_text}]
        new_context = await obj.create_context_in_collection(str(chat_id), messages)
        current_contexts[str(chat_id)] = new_context
        answer = await get_answer(messages)
        await obj.update_context(str(chat_id), new_context, {'role': 'assistant', 'content': answer})
        return answer

    current_context = current_contexts.get(str(chat_id))
    if current_context is None:
        return "Похоже включена функция openai\n" \
               "Чтобы продолжить выберите контекст\n" \
               "в меню /contexts\n" \
               "Либо отключите эту функцию в /menu"

    await obj.update_context(str(chat_id), current_context, {'role': 'user', 'content': message_text})
    messages = await obj.get_context(chat_id, current_contexts[str(chat_id)])
    answer = await get_answer(messages)
    await obj.update_context(str(chat_id), current_context, {'role': 'assistant', 'content': answer})
    return answer



async def get_answer(messages):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.5,
        )
        answer = response['choices'][0]['message']['content']
        return answer
    except openai.error.OpenAIError as error:
        logging.info(f'В def create_delete_menu \n {error.error}')


async def get_image_byte_arr(message):
    try:
        response = openai.Image.create(
            prompt=f"{message}",
            n=1,
            size="1024x1024"
        )
        url = response['data'][0]['url']

        print(url)

        response = requests.get(url)
        response.raise_for_status()  # Raise an exception if the GET request was unsuccessful

        image_byte_arr = io.BytesIO(response.content)
        return types.InputFile(image_byte_arr, filename='image.png')

    except openai.error.OpenAIError as error:
        logging.info(f'В def create_delete_menu \n {error.error}')


async def prompt_editor_for_img_generator(base_prompt):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Help me to make a query for DALL-E 3, I will give you a simple query, and you have to make such a prompt that the final quote will be better, better, more aesthetic, more beautiful."},
            {"role": "user", "content": f"{base_prompt}"}
        ]
    )
    new_prompt = response['choices'][0]['message']['content']
    print(response)
    print(new_prompt)
    return new_prompt

