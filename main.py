import os
import random
import requests
from dotenv import load_dotenv
from urllib import parse


def get_comics_details():
    last_comics = requests.get('https://xkcd.com/info.0.json')
    last_comics.raise_for_status()
    comics_id = random.randint(1, last_comics.json()['num'])
    random_comics = requests.get(f'https://xkcd.com/{comics_id}/info.0.json')
    random_comics.raise_for_status()
    comics_details = random_comics.json()
    unquoted_url = parse.unquote(comics_details['img'])
    filename = parse.urlparse(unquoted_url).path.rstrip('/').split('/')[-1]
    return comics_details['img'], comics_details['alt'], filename


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
    return uploaded_photo


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
    response_details = response.json()
    get_response_status(response_details)
    saved_photo = response_details['response'][0]
    return saved_photo


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
    response_details = response.json()
    get_response_status(response_details)
    return response_details


def get_response_status(response_details):
    if response_details.get('error'):
        raise requests.HTTPError(response_details['error']['error_code'])


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

    comics_link, comics_comment, filename = get_comics_details()
    download_comics(comics_link, filename)

    try:
        upload_server = get_wall_upload_server(vk_url, vk_group_id)
        uploaded_photo = upload_photo(upload_server, filename)
        saved_photo = save_wall_photo(vk_url, vk_group_id, uploaded_photo, payloads)
        post_photo(saved_photo, comics_comment, vk_url, vk_group_id, payloads)
    finally:
        os.remove(filename)
