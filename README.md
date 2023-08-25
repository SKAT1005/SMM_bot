<br/>
<p align="center">

  <h3 align="center">
SMM-bot - Телеграмм бот для продвижения социальных сетей
</h3>

  <p align="center">
   Простое и действенное решение для помощи в развитии
    <br/>
    <br/>
  </p>
</p>

## Содержание

* [О проекте](#о-проекте)
* [Стек](#стек)
* [Установка](#установка)
* [Использование](#использование)
* [Авторы](#авторы)

## О проекте

Данный бот предоставляет помогает в продвижении социальных сетей, путем накрутки подписчиков/лайков/комментариев. Для их
покупки используется сервис [smmpanel](https://smmpanel.ru/)

## Стек

Данный бот был написан на Python, испрользуя pyTelegramBotAPI, а так же pyTONPublicAPI

## Установка

1. Зарегистрируйтесь на сайте [smmpanel](https://smmpanel.ru/)  перейдите в свой профиль, скопируйте там API key и
   вставьте его в переменную smmplanet_api_key
2. Зарегистрироуйтесь на сайте [Tegro Money](https://tegro.money/), зарегистрируйте совой магазин, сгенерируйте Secret
   KEY, API KEY, сохраните их и вставьте Shop ID в переменную shp_id , Secret Key в переменную secret_keyб API KEY в
   переменную api_key
3. Создание виртуального окружения
   <br>`python -m venv venv`</br>
   <br>`python venv\Scripts\activate.bat` - для Windows;</br>
   <br>`python source venv/bin/activate` - для Linux и MacOS.</br>

4. Установите все зависимости, используя команду `pip install -r requirements.txt`
5. Далее вам нужно применить миграции и создать супер пользователя это вы можете сделать прописав данные
   комманды:
   ```
   python manage.py makemigrations
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py runserver
   ```
6. Для подключения сервисов, через которые вы хотите добавлять подписчивок, зайдите в админ-панель перейдя на ваш сайт
   введите /admin, введите логин и пароль и перейдите в раздел Type_apis, нажмите ADD TYPE_API и заполните форму. Далее
   перейдите в раздел Apis, нажмите ADD TYPE_API и заполните форму.
7. Для добавления вашего бота получите у [BotFather](https://t.me/BotFather) Токен бота зайдите в админ-панель,
   перейдите в раздел Bots, наждмите ADD BOT и в форме укажите токен вашего бота. **Галочку не ставьте**

## Использование

Запустите бота командой `python main.py`

## Авторы

* **Skat1005** - *Developer* - [Skat1005](https://github.com/SKAT1005/) - *Python Backend Developer*
