import openai, os, mongodb

openai.api_key = os.environ.get('openai_api_key')

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
               "в меню /contexts"
    await obj.update_context(str(chat_id), current_context, {'role': 'user', 'content': message_text})
    messages = await obj.get_context(chat_id, current_contexts[str(chat_id)])
    answer = await get_answer(messages)
    await obj.update_context(str(chat_id), current_context, {'role': 'assistant', 'content': answer})
    return answer


async def get_answer(messages):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages,
            temperature=0.5,
        )
        answer = response['choices'][0]['message']['content']
        return answer
    except Exception as error:
        print('ERROR: ', error)
        return f"Error: {error}"
