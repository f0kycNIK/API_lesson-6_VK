import os
import random
import time
from os.path import splitext
from pathlib import Path
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv


def get_comics_number(url):
    response = requests.get(url)
    response.raise_for_status()
    comics_number = response.json()['num']
    return comics_number


def get_image_parameters(url):
    response = requests.get(url)
    response.raise_for_status()
    comics = response.json()
    image_url = comics['img']
    image_name = comics['title']
    image_text = comics['alt']
    return image_url, image_name, image_text


def open_pics_list():
    try:
        with open('publication list.txt', 'r', encoding='utf8') as f:
            posted_pics = f.read().splitlines()
    except FileNotFoundError:
        posted_pics = []
    return posted_pics


def download_image(image_url, image_name, folder):
    root, image_format = splitext(urlparse(image_url).path)
    response = requests.get(image_url)
    response.raise_for_status()
    file_path = f'{folder}/{image_name}{image_format}'
    with open(file_path, 'wb') as file:
        file.write(response.content)
    return file_path


def get_upload_url(url, vk_group_id, vk_token, vk_api_version):
    method = 'photos.getWallUploadServer'
    new_url = url + method
    payload = {
        'group_id': vk_group_id,
        'access_token': vk_token,
        'v': vk_api_version,
    }
    response = requests.get(new_url, params=payload)
    response.raise_for_status()
    album_params = response.json()
    check_error(album_params)
    upload_url = album_params['response']['upload_url']
    return upload_url


def upload_photo(url, image_path):
    with open(image_path, 'rb') as image:
        files = {
            'photo': image,
        }
        response = requests.post(url, files=files)
    response.raise_for_status()
    photo_parameters = response.json()
    check_error(photo_parameters)
    return photo_parameters


def save_photo(url, server, photo, photo_hash, text, vk_token, group_id,
               vk_api_version):
    method = 'photos.saveWallPhoto'
    new_url = url + method
    payload = {
        'group_id': group_id,
        'server': server,
        'photo': photo,
        'hash': photo_hash,
        'caption': text,
        'access_token': vk_token,
        'v': vk_api_version,
    }
    response = requests.post(new_url, data=payload)
    response.raise_for_status()
    image_characteristics = response.json()
    check_error(image_characteristics)
    owner_id = image_characteristics['response'][0]['owner_id']
    photo_id = image_characteristics['response'][0]['id']
    return owner_id, photo_id


def publish_photo_on_wall(url, vk_group_id, owner_id, photo_id, vk_token,
                          vk_api_version):
    method = 'wall.post'
    from_group = 1
    friends_only = 0
    new_url = url + method
    modify_group_id = f'-{vk_group_id}'
    payload = {
        'photo_id': photo_id,
        'owner_id': modify_group_id,
        'from_group': from_group,
        'friends_only': friends_only,
        'attachments': f'photo{owner_id}_{photo_id}',
        'access_token': vk_token,
        'v': vk_api_version,
    }
    response = requests.post(new_url, data=payload)
    response.raise_for_status()
    post_id = response.json()
    check_error(post_id)


def save_pics_list(pics):
    file_name = 'publication list.txt'
    with open(file_name, 'w') as file:
        file.write('\n'.join(str(pic) for pic in pics))


def check_error(answer):
    error_massage = ''
    if isinstance(answer, dict):
        try:
            error_massage = answer['error']['error_msg']
        except KeyError:
            pass
        if error_massage:
            raise Exception(error_massage)


def publication_photo(comics_number, vk_group_id, vk_token):
    xkcd_folder = 'xkcd'
    vk_api_version = '5.131'
    Path(xkcd_folder).mkdir(parents=True, exist_ok=True)
    timeout = 24 * 60 * 60
    posted_pics = open_pics_list()
    while True:
        random_comics_number = random.randint(1, comics_number)
        image_url, image_name, image_text = get_image_parameters(
            f'http://xkcd.com/{random_comics_number}/info.0.json')
        if image_name not in posted_pics:
            try:
                file_path = download_image(image_url, image_name, xkcd_folder)
                vk_url = 'https://api.vk.com/method/'
                upload_url = get_upload_url(vk_url, vk_group_id, vk_token,
                                            vk_api_version)
                photo_parameters = upload_photo(upload_url, file_path)
                server = photo_parameters['server']
                photo = photo_parameters['photo']
                photo_hash = photo_parameters['hash']
                owner_id, photo_id = save_photo(vk_url, server, photo, photo_hash,
                                                image_text, vk_token,
                                                vk_group_id, vk_api_version)
                publish_photo_on_wall(vk_url, vk_group_id, owner_id,
                                      photo_id,
                                      vk_token, vk_api_version)
                posted_pics.append(image_name)
                save_pics_list(posted_pics)
            finally:
                os.remove(file_path)
        time.sleep(timeout)


if __name__ == '__main__':
    load_dotenv()

    vk_token = os.getenv('VK_TOKEN')
    vk_group_id = os.getenv('VK_GROUP_ID')

    comics_number = get_comics_number('http://xkcd.com/info.0.json')
    publication_photo(comics_number, vk_group_id, vk_token)
