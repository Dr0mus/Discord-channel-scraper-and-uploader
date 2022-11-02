from tinydb import TinyDB, Query
import requests
import shutil
import os
import time

token = 'Your Token'
channel_id = 'Channel id'
upload_channel_id = 'upload channel id'

headers = {
    'Authorization': token
}
#tinydb setup
db = TinyDB('./db.json')
User = Query()

def check_id_db(attachment_idz):
    exists = db.search(User.attachment_id == attachment_idz)
    try:
        if (exists[0].get("attachment_id") == attachment_idz):
            return True
        else:
            return False
    except:
        return False

def check_folder():
    path = os.getcwd()
    path = os.path.join(path, channel_id)
    isExist = os.path.exists(path)
    if not isExist:
        os.makedirs(path)

def delete_files():
    path = os.getcwd()
    path = os.path.join(path, channel_id)
    files = os.listdir(path)
    for file in files:
        file_path = os.path.join(path, file)
        os.remove(file_path)

def get_initial_messages(channel_id):
    return requests.get(f'https://discord.com/api/v9/channels/{channel_id}/messages?limit=100', headers=headers)

def get_last_message(messages):
    return messages[-1]['id']

def get_previous_messages(channel_id, last_message_id):
    return requests.get(f'https://discord.com/api/v9/channels/{channel_id}/messages?limit=100&before={last_message_id}', headers=headers)

def download_attachments(message):
    check_folder()
    for i in message:
        for item in i['attachments']:
            if "url" in item:
                directory = os.getcwd()
                directory = os.path.join(directory, channel_id)
                filename = f'{item["id"]}.png'
                fileexists = os.path.exists(os.path.join(directory, filename))
                if fileexists:
                    print("File already downloaded " + filename)
                else:
                    if check_id_db(item["id"]) == False:
                        url = item['url']
                        r = requests.get(url,   stream=True)
                        r.raw.decode_content = True
                        with open(f'./{channel_id}/{item["id"]}.png', 'wb') as f:
                            shutil.copyfileobj(r.raw, f)
                    else:
                        print("File already uploaded " + filename)


# upload all files from a folder to discord channel
def upload_files(channel_id, upload_channel_id):
    path = os.getcwd()
    path = os.path.join(path, channel_id)
    files = os.listdir(path)
    for file in files:
        file_path = os.path.join(path, file)
        size = len(file)
        attachment_id_name = file[:size - 4]
        file = {'file': open(file_path, 'rb')}
        r = requests.post(f'https://discord.com/api/v9/channels/{upload_channel_id}/messages', headers=headers, files=file)
        print(r.status_code)
        if (r.status_code == 200):
            db.insert({"attachment_id": attachment_id_name})
        elif (r.status_code == 429):
            response = r.json()
            print("Waiting" + str(int(response["retry_after"]) + 1))
            time.sleep(int(response["retry_after"]) + 1)
        elif (r.status_code) == 419:
            print(r.json())
        elif (r.status_code) == 413:
            print(r.json())

# get all messages until there are no more messages
def get_all_messages(channel_id, upload_channel_id):
    messages = get_initial_messages(channel_id).json()
    download_attachments(messages)
    last_message_id = get_last_message(messages)
    while True:
        previous_messages = get_previous_messages(channel_id, last_message_id).json()
        download_attachments(previous_messages)
        messages.extend(previous_messages)
        #upload files from folder to discord channel and delete them
        upload_files(channel_id, upload_channel_id)
        #delete files from folder
        delete_files()
        if len(previous_messages) == 0:
                    break
        last_message_id = get_last_message(previous_messages)

if __name__ == '__main__':
    get_all_messages(channel_id, upload_channel_id)