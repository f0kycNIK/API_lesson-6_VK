# Comics publisher

The program download comics from the <http://xkcd.com> in random order and 
post them on the <https://vk.com/>  community wall.

## How to install

Variables `vk_group_id` and `vk_tokken` store data for autorization in 
[vk.com](https://vk.com) and pull in from the `.env` file.

```python
vk_token = os.getenv('VK_TOKEN')
vk_group_id = os.getenv('VK_GROUP_ID')
```
The `.env` file is located in the root directory.
```
├── .env
└── main.py
```

In the `.env` file, keys are written follows:

```python
VK_TOKEN=[vk token]
VK_GROUP_ID=[vk group id]
```

Python3 must already be installed. Then use pip (or pip3 if you have
conflict with Python3) to install dependencies:

```python
pip install -r requirements.txt
```
The program is started by the command:

```python
./python main.py
```
Comics are temporarily downloaded to the `xkcd` folder, at the end of the 
publication, the comic is entered into the list of publications, the 
identifier is the name of the comic. Once published, the comic will be removed 
from the `xkcd`.

## Project Goals

The code is written for educational purposes on online-course for 
web-developers [dvmn.org](https://dvmn.org).