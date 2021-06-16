import os
import random
import requests
from dotenv import load_dotenv
from urllib.parse import urlsplit, unquote


def get_comics_details():
    last_comics = requests.get('https://xkcd.com/info.0.json')
    last_comics.raise_for_status()
    comics_id = random.randint(1, last_comics.json()['num'])
    random_comics = requests.get(f'https://xkcd.com/{comics_id}/info.0.json')
    random_comics.raise_for_status()
    comics_details = random_comics.json()
    unquoted_url = unquote(comics_details['img'])
    filename = urlsplit(unquoted_url).path.rstrip('/').split('/')[-1]
    return comics_details['img'], comics_details['alt'], filename


def download_comics(comix_link, filename):
    response = requests.get(comix_link)
    response.raise_for_status()
    with open(filename, 'wb') as file:
        file.write(response.content)


def get_wall_upload_server(url, group_id, token, api_version):
    url_method = f'{url}photos.getWallUploadServer'
    payloads = {
        'access_token': token,
        'extended': 1,
        'group_id': group_id,
        'v': api_version
    }
    response = requests.get(url_method, params=payloads)
    response.raise_for_status()
    response_details = response.json()
    get_response_status(response_details)
    upload_server = response_details['response']['upload_url']
    return upload_server


def upload_photo(upload_url, photo):
    with open(photo, 'rb') as file:
        files = {'photo': file}
        response = requests.post(upload_url, files=files)
    response.raise_for_status()
    if response.json()['photo'] == '[]':
        return None
    uploaded_photo = response.json()
    return uploaded_photo['photo'], uploaded_photo['server'], uploaded_photo['hash']


def save_wall_photo(url, group_id, photo, server, photo_hash, token, api_version):
    url_method = f'{url}photos.saveWallPhoto'
    payloads = {
        'access_token': token,
        'extended': 1,
        'group_id': group_id,
        'photo': photo,
        'server': server,
        'hash': photo_hash,
        'v': api_version
    }
    response = requests.post(url_method, params=payloads)
    response.raise_for_status()
    response_details = response.json()
    get_response_status(response_details)
    saved_photo = response_details['response'][0]
    return saved_photo


def post_photo(photo, comment, url, group_id, token, api_version):
    url_method = f'{url}wall.post'
    payloads = {
        'access_token': token,
        'owner_id': f'-{group_id}',
        'from_group': 1,
        'message': comment,
        'attachments': f'photo{photo["owner_id"]}_{photo["id"]}',
        'v': api_version
    }
    response = requests.post(url_method, params=payloads)
    response.raise_for_status()
    response_details = response.json()
    get_response_status(response_details)
    return response_details


def get_response_status(response_details):
    if response_details.get('error'):
        raise requests.HTTPError(response_details['error']['error_code'])


if __name__ == '__main__':
    load_dotenv()

    vk_api_version = 5.131
    vk_token = os.getenv('VK_ACCESS_TOKEN')
    vk_group_id = os.getenv('VK_GROUP_ID')
    vk_url = 'https://api.vk.com/method/'

    comics_link, comics_comment, filename = get_comics_details()
    download_comics(comics_link, filename)

    try:
        upload_server = get_wall_upload_server(vk_url, vk_group_id, vk_token, vk_api_version)
        photos_object, photo_server, photo_hash = upload_photo(upload_server, filename)
        saved_photo = save_wall_photo(vk_url, vk_group_id, photos_object, photo_server, photo_hash,
                                      vk_token, vk_api_version)
        post_photo(saved_photo, comics_comment, vk_url, vk_group_id, vk_token, vk_api_version)
    finally:
        os.remove(filename)
