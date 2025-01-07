# https://www.youtube.com/watch?v=XF2WVUVxAGQ
import os, base64
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from telethon import functions, types, sync, events
from telethon.tl.types import InputPeerChat, InputPeerChannel, PeerChat, PeerChannel, Photo 
import openai

API_ID = os.environ.get('API_ID')
API_HASH = os.environ.get('API_HASH')
STRING_SESSION = os.environ.get('STRING_SESSION')
STRING_SESSION = StringSession(open('.session').read()) if os.path.isfile('.session') else STRING_SESSION
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
CHAT_ID_LIST = os.environ.get('CHAT_ID_LIST').split(',')

# словарь где ключ - ид приватного чата, а значение - список словарей в формате openai
mess_init = [{"role": "system", "content": "Ты отвечаешь сообщениями длиной от 1 до 15 слов"}]
mess_init.append({"role": "system", "content": "Ты приятный парень, желающий познакомиться с красивыми девушками"})
mess_dict = {}

# https://my.telegram.org/apps 
client_tg = TelegramClient(STRING_SESSION, API_ID, API_HASH, system_version="4.16.30-vxCUSTOM").start()
with open('.session', 'w') as session_file:
    session_file.write(client_tg.session.save())
# openai
client_oa = openai.OpenAI(api_key=OPENAI_API_KEY, base_url="https://api.vsegpt.ru/v1")

@client_tg.on(events.NewMessage(incoming=True)) # chats=('chat_name')  , pattern='Привет'
async def normal_handler(event):
    chat_id = str(event.chat_id)
    if not chat_id in CHAT_ID_LIST:
        return None
    else:
        global mess_dict
        if not chat_id in mess_dict:
            mess_dict[chat_id] = mess_init
    
    mess_dict[chat_id].append({"role": "user", "content": event.message.text})
    if event.photo:
        _bytes = await client_tg.download_media(event.message.media.photo, bytes) # event.message.media.photo._bytes()
        response = client_oa.chat.completions.create(model="vis-openai/gpt-4o-mini", # https://vsegpt.ru/Docs/Models#h46-2
                                                     messages=[{"role": "user", 
                                                                "content": [{"type": "text", "text": "Что на этом изображении?"},
                                                                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64.b64encode(_bytes).decode('utf-8')}"}}]}], 
                                                         max_tokens=512)
        mess_dict[chat_id].append(response.choices[0].message.to_dict() | {'role': 'user'}) # это юзер скидывает картинку, поэтому подменим роль
               
    response = client_oa.chat.completions.create(model="openai/gpt-3.5-turbo-0125", messages=mess_dict[chat_id], temperature=0.7, n=1, max_tokens=128)
    mess_dict[chat_id].append(response.choices[0].message.to_dict()) # добавляем в историю переписки отправленный ассистентом контекст
    
    await event.reply(mess_dict[chat_id][-1]['content'])
                                   
if __name__ == '__main__':
    client_tg.run_until_disconnected()