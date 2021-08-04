import os
import random
import time
from os.path import splitext
from pathlib import Path
from urllib.parse import urlparse
from urllib.parse import unquote

import requests
from dotenv import load_dotenv


def get_total_comics_number():
    xkcd_url = 'http://xkcd.com/info.0.json'
    response = requests.get(xkcd_url)
    response.raise_for_status()
    total_comics_number = response.json()['num']
    return total_comics_number


def get_comics_parameters(random_comics_number):
    url = f'http://xkcd.com/{random_comics_number}/info.0.json'
    response = requests.get(url)
    response.raise_for_status()
    comics = response.json()
    comics_url = comics['img']
    comics_name = comics['title']
    comics_text = comics['alt']
    return comics_url, comics_name, comics_text


def open_pics_list(path_publication_list):
    try:
        with open(path_publication_list, 'r', encoding='utf8') as f:
            posted_pics = f.read().splitlines()
    except FileNotFoundError:
        posted_pics = []
    return posted_pics


def download_image(image_url, image_name, folder):
    root, image_format = splitext(unquote(urlparse(image_url).path))
    response = requests.get(image_url)
    response.raise_for_status()
    file_path = f'{folder}/{image_name}{image_format}'
    with open(file_path, 'wb') as file:
        file.write(response.content)
    return file_path


def get_upload_url(url, vk_group_id, vk_token, vk_api_version):
    method = 'photos.getWallUploadServer'
    method_url = '{}{}'.format(url, method)
    payload = {
        'group_id': vk_group_id,
        'access_token': vk_token,
        'v': vk_api_version,
    }
    response = requests.get(method_url, params=payload)
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
    method_url = '{}{}'.format(url, method)
    payload = {
        'group_id': group_id,
        'server': server,
        'photo': photo,
        'hash': photo_hash,
        'caption': text,
        'access_token': vk_token,
        'v': vk_api_version,
    }
    response = requests.post(method_url, data=payload)
    response.raise_for_status()
    image_characteristics = response.json()
    check_error(image_characteristics)
    owner_id = image_characteristics['response'][0]['owner_id']
    photo_id = image_characteristics['response'][0]['id']
    return owner_id, photo_id


def upload_photo_on_wall(url, vk_group_id, owner_id, photo_id, vk_token,
                         vk_api_version):
    method = 'wall.post'
    from_group = 1
    friends_only = 0
    method_url = '{}{}'.format(url, method)
    corrected_group_id = f'-{vk_group_id}'
    payload = {
        'photo_id': photo_id,
        'owner_id': corrected_group_id,
        'from_group': from_group,
        'friends_only': friends_only,
        'attachments': f'photo{owner_id}_{photo_id}',
        'access_token': vk_token,
        'v': vk_api_version,
    }
    response = requests.post(method_url, data=payload)
    response.raise_for_status()
    post_id = response.json()
    check_error(post_id)


def save_pics_list(pics, path_publication_list):
    with open(path_publication_list, 'w') as file:
        file.write('\n'.join(str(pic) for pic in pics))


def check_error(answer):
    if answer.get('error'):
        error_massage = answer['error']['error_msg']
        raise requests.HTTPError(error_massage)


def publish_photos(total_comics_number, vk_group_id, vk_token,
                   path_publication_list):
    xkcd_folder = 'xkcd'
    vk_api_version = '5.131'
    file_path = ''
    Path(xkcd_folder).mkdir(parents=True, exist_ok=True)
    timeout = 24 * 60 * 60
    posted_pics = open_pics_list(path_publication_list)
    while True:
        random_comics_number = random.randint(1, total_comics_number)
        comics_url, comics_name, comics_text = get_comics_parameters(
            random_comics_number)
        if comics_name in posted_pics:
            continue
        file_path = download_image(comics_url, comics_name, xkcd_folder)
        vk_url = 'https://api.vk.com/method/'
        upload_url = get_upload_url(vk_url, vk_group_id, vk_token,
                                    vk_api_version)
        photo_parameters = upload_photo(upload_url, file_path)
        server = photo_parameters['server']
        photo = photo_parameters['photo']
        photo_hash = photo_parameters['hash']
        owner_id, photo_id = save_photo(vk_url, server, photo,
                                        photo_hash, comics_text,
                                        vk_token, vk_group_id,
                                        vk_api_version)
        upload_photo_on_wall(vk_url, vk_group_id, owner_id,
                             photo_id,
                             vk_token, vk_api_version)
        posted_pics.append(comics_name)
        save_pics_list(posted_pics, path_publication_list)
        os.remove(file_path)
        time.sleep(timeout)


if __name__ == '__main__':
    load_dotenv()

    vk_token = os.getenv('VK_TOKEN')
    vk_group_id = os.getenv('VK_GROUP_ID')

    path_publication_list = 'publication_list.txt'
    total_comics_number = get_total_comics_number()
    publish_photos(total_comics_number, vk_group_id, vk_token,
                   path_publication_list)
