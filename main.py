import os
import random
import requests
from dotenv import load_dotenv


def get_comics_info():
    current_comics = requests.get('https://xkcd.com/info.0.json')
    current_comics.raise_for_status()
    random_comics_id = random.randint(1, current_comics.json()['num'])
    random_comics = requests.get(f'https://xkcd.com/{random_comics_id}/info.0.json')
    random_comics.raise_for_status()
    comix_info = random_comics.json()
    filename = comix_info['img'].rsplit('/', 1)[1]
    return comix_info['img'], comix_info['alt'], filename


def download_comics(comix_link, filename):
    response = requests.get(comix_link)
    response.raise_for_status()
    with open(filename, 'wb') as file:
        file.write(response.content)


def get_wall_upload_server(url, group_id):
    url_method = f'{url}photos.getWallUploadServer'
    payloads['group_id'] = group_id
    response = requests.get(url_method, params=payloads)
    response.raise_for_status()
    if response.json().get('error', None):
        return None
    return response.json()['response']['upload_url']


def upload_photo(upload_url, photo):
    with open(photo, 'rb') as file:
        files = {'photo': file}
        response = requests.post(upload_url, files=files)
        response.raise_for_status()
    if response.json()['photo'] == '[]':
        return None
    return response.json()


def save_wall_photo(url, group_id, uploaded_photo, payloads):
    url_method = f'{url}photos.saveWallPhoto'
    payloads.update({
        'group_id': group_id,
        'photo': uploaded_photo['photo'],
        'server': uploaded_photo['server'],
        'hash': uploaded_photo['hash']
    })
    response = requests.post(url_method, params=payloads)
    response.raise_for_status()
    if response.json().get('error', None):
        return None
    return response.json()['response'][0]


def post_photo(photo, comment, url, group_id, payloads):
    url_method = f'{url}wall.post'
    payloads.update({
        'owner_id': f'-{group_id}',
        'from_group': 1,
        'message': comment,
        'attachments': f'photo{photo["owner_id"]}_{photo["id"]}'
    })
    response = requests.post(url_method, params=payloads)
    response.raise_for_status()
    return response.json()


if __name__ == '__main__':
    load_dotenv()

    vk_token = os.getenv('VK_ACCESS_TOKEN')
    vk_group_id = os.getenv('VK_GROUP_ID')
    vk_url = 'https://api.vk.com/method/'
    payloads = {
        'access_token': vk_token,
        'extended': 1,
        'v': 5.131
    }

    comics_link, comics_comment, filename = get_comics_info()
    download_comics(comics_link, filename)

    upload_server = get_wall_upload_server(vk_url, vk_group_id)
    uploaded_photo = upload_photo(upload_server, filename)
    saved_photo = save_wall_photo(vk_url, vk_group_id, uploaded_photo, payloads)
    post_photo(saved_photo, comics_comment, vk_url, vk_group_id, payloads)
    os.remove(filename)
