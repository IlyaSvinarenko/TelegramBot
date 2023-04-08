import asyncio
from motor.motor_asyncio import AsyncIOMotorClient


class MongoForBotManager:
    def __init__(self):
        self.uri = "mongodb://mongodb-container:27017"
        self.db = "chats_id"

    async def create_collection_chat_id(self, chat_id):
        '''collection name is (chat_id)
        it must to contained documents like ({context_name : context_text})'''
        client = AsyncIOMotorClient(self.uri)
        chats_id_db = client.get_database(self.db)
        collection = await chats_id_db.create_collection(chat_id)
        client.close()

    async def create_context_in_collection(self, chat_id: str, list_of_dialog_dicts: list[dict]):
        client = AsyncIOMotorClient(self.uri)
        collection = client[self.db][f"{chat_id}"]
        context_name = ' '.join(list_of_dialog_dicts[-1]['content'].split()[0:3:])
        document = {context_name: list_of_dialog_dicts}
        result = await collection.insert_one(document)
        client.close()
        return context_name

    async def delete_collection_chat_id(self, chat_id):
        '''delete collection by name'''
        client = AsyncIOMotorClient(self.uri)
        chats_id_db = client.get_database(self.db)
        collection = chats_id_db.get_collection(chat_id)
        await collection.drop()
        client.close()

    async def delete_context(self, chat_id, context_name):
        client = AsyncIOMotorClient(self.uri)
        collection = client[f"{self.db}"][f"{chat_id}"]
        result = await collection.delete_one({f'{context_name}': {'$exists': True}})
        client.close()
        return

    async def update_context(self, chat_id, context_name, dialog_dict):
        client = AsyncIOMotorClient(self.uri)
        collection = client[f"{self.db}"][f"{chat_id}"]
        documents = await collection.find_one({context_name: {'$exists': True}})
        if len(documents[context_name]) > 7:
            documents[context_name] = documents[context_name][2::]
            await collection.update_one({context_name: {'$exists': True}},
                                        {'$set': {context_name: documents[context_name]}})
        result = await collection.update_one({context_name: {'$exists': True}},
                                             {'$addToSet': {context_name: dialog_dict}})
        client.close()
        return

    async def get_all_collections(self):
        client = AsyncIOMotorClient(self.uri)
        chats_id_db = client.get_database(self.db)
        col_name_list = await chats_id_db.list_collection_names()
        client.close()
        return col_name_list

    async def get_contexts_data(self, chat_id):
        client = AsyncIOMotorClient(self.uri)
        collection = client[f"{self.db}"][f"{chat_id}"]
        contexts_names = []
        contexts_text = []
        async for document in collection.find():
            for key, value in document.items():
                if key == '_id':
                    continue
                else:
                    contexts_names.append(key)
                    contexts_text.append(value)
        client.close()
        return list(zip(contexts_names, contexts_text))

    async def get_context(self, chat_id, context_name):
        client = AsyncIOMotorClient(self.uri)
        collection = client[f"{self.db}"][f"{chat_id}"]
        document = await collection.find_one({context_name: {'$exists': True}})
        client.close()
        return document[context_name]

# obj = MongoForBotManager()
# print(asyncio.run(obj.get_all_collections()))
# data = asyncio.run(obj.get_contexts_data('-1001730972277'))
# print(len(data))
#
# asyncio.run(obj.update_context('-1001730972277','test tes', {'qwe':'qweqwe', 'rrrrrrrrr': "ttttt"}))
# print(asyncio.run(obj.get_contexts_data('-1001730972277')))
# asyncio.run(obj.delete_collection_chat_id('-1001730972277'))
