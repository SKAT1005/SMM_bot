import hashlib
import hmac
import json
import random
from datetime import datetime
from multiprocessing import Process
from time import sleep, time
import os
import django
from captcha.image import ImageCaptcha

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SMM_bot.settings')
django.setup()
import requests
import telebot
import urllib3
from telebot import types
from Models.models import User, Category, Product, Orders, FAQ, Message, Receipts, GroupAndChennel, Type_API, API

BOT_TOKEN = 'BOT_TOKEN'
bot = telebot.TeleBot(BOT_TOKEN)
shop_id = 'shop_id'
api_key = 'api_key'
secret_key = 'secret_key'
smmplanet_api_key = 'smmplanet_api_key'


@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    bot.delete_message(chat_id=user_id, message_id=message.id)
    if not User.objects.filter(user_id=user_id):
        create_user(message=message, user_id=user_id)

    if 'M' in message.text:
        receipt_name = message.text.split()[1]
        receipt = Receipts.objects.get(name=receipt_name)
        capcha(user_id=user_id, receipt=receipt)
    else:
        chat_id = message.chat.id
        main_menu(chat_id)


def update_services():
    while True:
        if datetime.now().hour == 4:
            data = {
                'key': smmplanet_api_key,
                'action': 'services',
            }
            url = 'https://smmpanel.ru/api/v1'
            response = requests.post(url, data=data)
            services = json.loads(response.text)
            products = Product.objects.all()
            products_list = []
            type_api = Type_API.objects.get(API_url=url)
            api = API.objects.get(type=type_api)
            for service in services:
                a = True
                service_id = int(service['service'])
                price = float(service['rate']) * 10
                min_summ = int(service['min'])
                max_summ = int(service['max'])
                category = service['category'].split()[0]
                subcategory = service['category'].split()[1]
                name = service['name']
                description = service['desc']
                for product in products:
                    if product.servis_id == service_id:
                        products_list.append(product)
                        a = False
                        product.price = price
                        product.min_summ = min_summ
                        product.max_summ = max_summ
                        product.category.category.name = category
                        product.category.name = subcategory
                        product.name = name
                        product.description = description
                        product.save()
                        break
                if a:
                    product_subcategory = Category.objects.filter(name=subcategory)
                    if not product_subcategory:
                        product_category = Category.objects.filter(name=category)
                        if not product_category:
                            product_category = Category.objects.create(
                                name=category
                            )
                        product_subcategory = Category.objects.create(
                            parents=product_category,
                            name=subcategory
                        )
                    Product.objects.create(
                        api=api,
                        servis_id=service_id,
                        category=product_subcategory,
                        min_summ=min_summ,
                        max_summ=max_summ,
                        name=name,
                        description=description,
                        price=price,
                    )
            for product in products:
                if product not in products_list:
                    product.delete()


def check_deposits():
    while True:
        users = User.objects.filter(pay_balanse=True)
        for user in users:
            data = {
                'shop_id': shop_id,
                'nonce': int(time()),
                'payment_id': user.user_id
            }

            body = json.dumps(data)
            sign = hmac.new(api_key.encode(), body.encode(), hashlib.sha256).hexdigest()

            headers = {
                'Authorization': 'Bearer ' + sign,
                'Content-Type': 'application/json'
            }

            url = 'https://tegro.money/api/order/'

            response = requests.post(url, data=body, headers=headers)

            todos = json.loads(response.text)
            if todos['type'] == 'success':
                data = todos['data']
                id = data['id']
                status = data['status']
                if status == 1 and user.last_pay_id != id:
                    user.balance += data['amount']
                    user.pay_balanse = False
                    user.last_pay_id = id
                    user.save()
                    bot.send_message(chat_id=user.user_id, text='Ваш баланс успешно пополнен')


def send_order(order):
    url = order.product.api.type.API_url
    data = {
        'key': order.product.api.API_key,
        'action': 'add',
        'service': order.product.servis_id,
        'link': order.link,
        'quantity': order.quantity
    }
    response = requests.post(url, data=data)
    order_id = json.loads(response.text)['order']
    order.order_id = order_id
    order.save()


def check_order_status():
    status_tuple = {
        'Pending': 'В работе',
        'Processing': 'В работе',
        'In progress': 'В работе',
        'Partial': 'В работе',
        'Completed': 'Выполнен',
        'Cancelled': 'Отменён',
    }
    while True:
        orders = Orders.objects.filter(status__in=['Новый', 'В работе'])
        for order in orders:
            data = {
                'key': order.product.api.API_key,
                'action': 'status',
                'order': order.order_id
            }
            url = order.product.api.type.API_url
            response = requests.post(url, data=data)
            status = json.loads(response.text)['status']
            order.status = status_tuple[status]
            order.save()


def send_message():
    while True:
        messages = Message.objects.all()
        users = User.objects.all()
        if messages:
            for message in messages:
                for user in users:
                    chat_id = user.user_id
                    try:
                        bot.send_message(chat_id=chat_id, text=message.message, )
                        bot.send_photo(chat_id=chat_id, photo=message.photo)
                    except Exception:
                        pass
                message.delete()


def pagination(markup, page, pagination_start, pagination_end, counter, category=None):
    if pagination_start == 0 and pagination_end < counter:
        next_page = types.InlineKeyboardButton('Следующая страница',
                                               callback_data=f'next_page|{page}|{pagination_start}|{pagination_end}|{category}')
        markup.add(next_page)
    elif pagination_start > 0 and pagination_end >= counter:
        last_page = types.InlineKeyboardButton('Предыдущая страница',
                                               callback_data=f'last_page|{page}|{pagination_start}|{pagination_end}|{category}')
        markup.add(last_page)
    elif pagination_start > 0 and pagination_end < counter:
        next_page = types.InlineKeyboardButton('Следующая страница',
                                               callback_data=f'next_page|{page}|{pagination_start}|{pagination_end}|{category}')
        last_page = types.InlineKeyboardButton('Предыдущая страница',
                                               callback_data=f'last_page|{page}|{pagination_start}|{pagination_end}|{category}')
        markup.add(last_page, next_page)


def main_menu(chat_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    button1 = types.InlineKeyboardButton('🔥Создать новый заказ', callback_data='category')
    button2 = types.InlineKeyboardButton('📋Мои заказы', callback_data='my_order')
    button3 = types.InlineKeyboardButton('🏦Мой баланс', callback_data='balance')
    button4 = types.InlineKeyboardButton('💸Заработать', callback_data='earn')
    button5 = types.InlineKeyboardButton('⛑Помощь', callback_data='help')
    button6 = types.InlineKeyboardButton('💡FAQ', callback_data='faq')
    button7 = types.InlineKeyboardButton('🧾Чеки', callback_data='receipts')
    markup.add(button1, button2, button3, button4, button5, button6, button7)
    bot.send_message(chat_id, 'Главное меню', reply_markup=markup, parse_mode="MarkdownV2")


def categorys(chat_id, pagination_start=0, pagination_end=10):
    categorys = Category.objects.filter(parents=None)[pagination_start:pagination_end]
    markup = types.InlineKeyboardMarkup(row_width=2)
    for category in categorys:
        new_category_markup = types.InlineKeyboardButton(f'{category.name}',
                                                         callback_data=f'subcategories|{category.id}')
        markup.add(new_category_markup)
    pagination(markup=markup, page='category', pagination_start=pagination_start, pagination_end=pagination_end,
               counter=Category.objects.filter(parents=None).count())
    menu = types.InlineKeyboardButton('Главное меню', callback_data='menu')
    markup.add(menu)
    bot.send_message(chat_id, 'Выберите категорию', reply_markup=markup)


def subcategories(chat_id, parent, pagination_start=0, pagination_end=10):
    subcategories = Category.objects.filter(parents=parent)[pagination_start:pagination_end]
    markup = types.InlineKeyboardMarkup(row_width=2)
    for category in subcategories:
        new_category_markup = types.InlineKeyboardButton(f'{category.name}', callback_data=f'product|{category.id}')
        markup.add(new_category_markup)
    pagination(markup=markup, page='subcategories', pagination_start=pagination_start, pagination_end=pagination_end,
               counter=Category.objects.filter(parents=parent).count(), category=parent.id)
    menu = types.InlineKeyboardButton('Главное меню', callback_data='menu')
    markup.add(menu)
    bot.send_message(chat_id, 'Выберите категорию', reply_markup=markup)


def products(chat_id, category, pagination_start=0, pagination_end=10):
    products = Product.objects.filter(category=category)[pagination_start:pagination_end]
    markup = types.InlineKeyboardMarkup(row_width=2)
    for product in products:
        new_category_markup = types.InlineKeyboardButton(f'{product.name}: {product.price}',
                                                         callback_data=f'new_order|{product.id}')
        markup.add(new_category_markup)
    pagination(markup=markup, page='product', pagination_start=pagination_start, pagination_end=pagination_end,
               counter=Product.objects.filter(category=category).count(), category=category.id)
    menu = types.InlineKeyboardButton('Главное меню', callback_data='menu')
    markup.add(menu)
    bot.send_message(chat_id, 'Выберите товар', reply_markup=markup)


def new_order_step_three(message, chat_id, product, message_id, number):
    link = message.text
    a = True
    user = User.objects.get(user_id=message.from_user.id)
    total_price = product.price * number
    try:
        resp = urllib3.request("GET", link)
        if resp.status != 200 or '/t.me/+' in link:
            raise Exception
    except Exception:
        a = False
        error_message = '❌Указан неверный адрес или ссылка на закрытую группу/профиль/канал❌'
        new_order_step_two(message=message, chat_id=chat_id, product=product, message_id=message_id,
                           error_message=error_message, number=number)
    if a:
        bot.delete_message(chat_id=chat_id, message_id=message.id)
        bot.delete_message(chat_id=chat_id, message_id=message_id)
        if user.balance >= total_price:
            if user.inviting_user:
                user.inviting_user.balance += total_price * 0.12
                user.inviting_user.save()
                if user.inviting_user.inviting_user:
                    user.inviting_user.inviting_user.balance += total_price * 0.04
                    user.inviting_user.inviting_user.save()
            order = Orders.objects.create(
                product=product,
                price=total_price,
                quantity=number,
                link=link,
                status='Новый'
            )
            user.balance -= total_price
            user.orders.add(order)
            user.save()
            send_order(order)
            msg = bot.send_message(chat_id=chat_id, text='Спасибо, ваш заказ принят и находится в статусе: 🆕Новый '
                                                         f'ID заказа: {order.id}\n'
                                                         'Ожидайте начала выполнения. Наблюдать за заказами и их статусами Вы можете в разделе:\n'
                                                         '📋Мои заказы')
            sleep(4)
            bot.delete_message(chat_id=chat_id, message_id=msg.id)
            main_menu(chat_id)
        else:
            amount = total_price - user.balance
            msg = bot.send_message(chat_id=chat_id,
                                   text=f'Недостаточно средств на балансе. Пополните ваш баланс на  {a}RUB.\n')
            sleep(2)
            replenish_balance(message=msg, chat_id=chat_id, message_id=msg.id, user=user, amount=amount)


def new_order_step_two(message, chat_id, product, message_id, error_message='', number=False):
    a = True
    bot.delete_message(chat_id=chat_id, message_id=message.id)
    if not number:
        try:
            number = int(message.text)
            if product.min_summ > number or product.max_summ < number:
                raise ValueError
        except ValueError:
            a = False
            bot.delete_message(chat_id, message_id)
            error_message = f'❌Введите число от {product.min_summ} до {product.max_summ}❌'
            new_order_step_one(chat_id=chat_id, product_id=product.id, error_message=error_message)

    if a:
        bot.delete_message(chat_id=chat_id, message_id=message_id)
        msg = bot.send_message(chat_id,
                               f'{error_message}\n'
                               f'🔥 Заказ услуги: {product.name}\n'
                               f'‍♂️ {product.description}\n'
                               f'💳 Цена - {product.price} RUB. за одну единицу (Подписчик, лайк, репост)\n'
                               f'👇 Введите адрес целевой страницы (ссылка на фото, профиль, видео)\n')
        bot.register_next_step_handler(msg, new_order_step_three, chat_id, product, msg.id, number)


def new_order_step_one(chat_id, product_id, error_message=''):
    product = Product.objects.get(id=product_id)
    msg = bot.send_message(chat_id,
                           f'{error_message}\n'
                           f'🔥 Заказ услуги: {product.name}\n'
                           f'💁‍♂️ {product.description}\n'
                           f'💳 Цена - {product.price} RUB. за одну единицу (Подписчик, лайк, репост)\n'
                           f'👇 Введите количество для заказа от {product.min_summ} до {product.max_summ}\n')
    bot.register_next_step_handler(msg, new_order_step_two, chat_id, product, msg.id)


def my_order(chat_id, user, pagination_start=0, pagination_end=10):
    orders = user.orders.all()[pagination_start:pagination_end]
    markup = types.InlineKeyboardMarkup(row_width=2)
    text = ''
    status_message = {
        'Новый': '🆕',
        'В работе': '🔄',
        'Выполнен': '✅',
        'Отменён': '❌'
    }
    for order in orders:
        text += f'{status_message[order.status]}{order.product.name} {order.quantity}шт {order.price}RUB Номер заказа:{order.order_id}\n'
    pagination(markup=markup, page='orders', pagination_start=pagination_start, pagination_end=pagination_end,
               counter=user.orders.count())
    menu = types.InlineKeyboardButton('Главное меню', callback_data='menu')
    markup.add(menu)
    if orders.count() > 0:
        bot.send_message(chat_id=chat_id, text=text, reply_markup=markup)

    else:
        bot.send_message(chat_id=chat_id, text='Ваш список заказов пока что пуст', reply_markup=markup)


def replenish_balance(message, chat_id, message_id, user, amount=False):
    a = True
    bot.delete_message(chat_id=chat_id, message_id=message_id)
    if not amount:
        try:
            amount = int(message.text)
            if amount < 1:
                raise Exception
        except Exception:
            a = False
            error_message = "❌Введите число, которое больше 1❌"
            balance(chat_id=chat_id, user=user, error_message=error_message)
    if a:
        text = 'Перейдите по ссылке для пополнения:'
        markup = types.InlineKeyboardMarkup(row_width=2)
        menu = types.InlineKeyboardButton('Главное меню', callback_data='menu')
        secret = secret_key
        data = {
            'shop_id': shop_id,
            'amount': amount,
            'currency': 'RUB',
            'order_id': f'{user.user_id}'
        }
        sorted_data = dict(sorted(data.items()))
        query_string = '&'.join([f"{key}={value}" for key, value in sorted_data.items()])
        str_to_sign = f"{query_string}{secret}"
        sign = hashlib.md5(str_to_sign.encode()).hexdigest()
        url = f"https://tegro.money/pay/?{query_string}&sign={sign}"
        tegro = types.InlineKeyboardButton('💳Банковские карты', url=url)
        markup.add(tegro, menu)
        user.pay_balanse = True
        user.save()
        bot.send_message(chat_id=chat_id, text=text, reply_markup=markup)


def balance(chat_id, user, error_message=''):
    text = f'{error_message}' \
           f'Ваш баланс: {user.balance} RUB.' \
           '💳 Вы можете пополнить баланс, указав сумму пополнения в рублях 👇:'
    markup = types.InlineKeyboardMarkup(row_width=2)
    menu = types.InlineKeyboardButton('Главное меню', callback_data='menu')
    markup.add(menu)
    msg = bot.send_message(chat_id=chat_id, text=text, reply_markup=markup)
    bot.register_next_step_handler(msg, replenish_balance, chat_id, msg.id, user)


def earn(chat_id, user):
    markup = types.InlineKeyboardMarkup(row_width=2)
    button = types.InlineKeyboardButton('Главное меню', callback_data='menu')
    markup.add(button)
    bot.send_message(chat_id=chat_id,
                     text='🤝 Партнерская программа\n\n'
                          '🏆 Вознаграждения по реферальной программе разделены на два уровня:\n'
                          '├  За пользователей которые присоединились по Вашей ссылке \-\ рефералы 1 уровня\n'
                          '└  За пользователей которые присоединились по по ссылкам Ваших рефералов \-\ рефералы 2 уровня\n'
                          '🤑 Сколько можно заработать?\n'
                          '├  За реферала 1 уровня: 12%\n'
                          '└  За реферала 2 уровня: 4%\n\n'
                          '🥇 Статистика:\n'
                          f'├  Всего заработано: {user.money_earned}₽\n'
                          f'└  Лично приглашенных: {user.invited_users.count()}\n\n'
                          '🎁 Бонус за регистрацию:\n'
                          '└  За каждого пользователя который активировал бот по вашей реферальной ссылке вы так же получаете 5 рублей\.\ \n\n'
                          '⤵️ Ваша реферальная ссылка:\n'
                          f'├ `https://t.me/{bot.get_me().username}?start={user.user_id}`',
                     reply_markup=markup,
                     parse_mode="MarkdownV2")


def faq(chat_id, answer):
    markup = types.InlineKeyboardMarkup(row_width=2)
    faq = FAQ.objects.all()
    for faq in faq:
        button = types.InlineKeyboardButton(f'{faq.question}', callback_data=f'faq|{faq.id}')
        markup.add(button)
    menu = types.InlineKeyboardButton('Главное меню', callback_data='menu')
    markup.add(menu)
    bot.send_message(chat_id=chat_id, text=answer, reply_markup=markup)


@bot.message_handler(content_types=['new_chat_members', 'text'])
def connect_group_or_channel_to_user(message):
    if message.chat.type == 'supergroup' or message.forward_from_chat:
        user_chat_id = message.from_user.id
        group_or_channel_id = message.chat.id
        chat_name = message.chat.title
        if message.forward_from_chat:
            group_or_channel_id = message.forward_from_chat.id
            chat_name = message.forward_from_chat.title
        invite_link = bot.create_chat_invite_link(group_or_channel_id)
        user = User.objects.get(user_id=user_chat_id)
        group_or_channel = GroupAndChennel.objects.filter(chat_id=group_or_channel_id)
        if not group_or_channel:
            group_or_channel = GroupAndChennel.objects.create(
                name=chat_name,
                chat_id=group_or_channel_id,
                invite_link=invite_link.invite_link
            )
        if not group_or_channel in user.channel_and_group.all():
            user.channel_and_group.add(group_or_channel)
        bot.send_message(chat_id=user_chat_id,
                         text='Бот успешно добавлен в списко ваших чатов, теперь вам нужно прикреить его к чеку')
        sleep(4)
        all_receipts(chat_id=user_chat_id, user=user)


def add_group_or_channel_in_receipt(chat_id, receipt, group_or_channel):
    if receipt.group_or_channels.count() == 3:
        msg = bot.send_message(chat_id=chat_id, text='К одному чеку ожно подключить не более 3 чатов/групп')
        bot.delete_message(chat_id=chat_id, message_id=msg.id)
        connect(chat_id=chat_id, receipt=receipt, user=receipt.user)
    else:
        receipt.group_or_channels.add(group_or_channel)
        msg = bot.send_message(chat_id=chat_id, text='Канал успешно подключен')
        sleep(3)
        bot.delete_message(chat_id=chat_id, message_id=msg.id)
        connect(chat_id=chat_id, receipt=receipt, user=receipt.user)


def connect(chat_id, receipt, user):
    bot_name = bot.get_me().username
    all_group_and_channel = user.channel_and_group.all()
    text = 'Чтобы подключить канал, выполните эти действия:\n' \
           'Добавьте нашего бота в качестве администратора вашего канала или группы.\n\n ' \
           'Если вы добавили бота в канал, то перешлите сообщение из вашего канала в этот чат\n\n' \
           'Если он добавлен то вам нужно выберать название группы/канала, которую хотите подключить.'
    markup = types.InlineKeyboardMarkup(row_width=1)
    add_in_channel = types.InlineKeyboardButton('Добавить в канал',
                                                url=f'http://t.me/{bot_name}?startchannel&admin=change_info+delete_messages+invite_users')
    add_in_group = types.InlineKeyboardButton('Добавить в группу',
                                              url=f'http://t.me/{bot_name}?startgroup&admin=change_info+delete_messages+invite_users')
    back_to_recept = types.InlineKeyboardButton('Назад к чеку', callback_data=f'detail_recept|{receipt.name}')
    markup.add(add_in_channel, add_in_group, back_to_recept)
    for group_or_channel in all_group_and_channel:
        add_group_or_channel = types.InlineKeyboardButton(f'{group_or_channel.name}',
                                                          callback_data=f'add_group_or_channel|{group_or_channel.id}|{receipt.id}')
        markup.add(add_group_or_channel)
    bot.send_message(chat_id=chat_id, text=text, reply_markup=markup)


def add_checking_subscription(chat_id, reciept):
    text = 'Здесь вы можете настроить проверку подписки. Только подписчики подключённых ' \
           'каналов и групп смогут активировать чек. Вы можете подключить до 3-х каналов или групп.'
    markup = types.InlineKeyboardMarkup(row_width=1)
    connect = types.InlineKeyboardButton('Подключить канал', callback_data=f'connect|{reciept.name}')
    back_to_recept = types.InlineKeyboardButton('Назад к чеку', callback_data=f'detail_recept|{reciept.name}')
    markup.add(connect, back_to_recept)
    for group_or_channel in reciept.group_or_channels.all():
        markup_grouo_or_channel = types.InlineKeyboardButton(group_or_channel.name,
                                                             callback_data=f'GOC|{group_or_channel.id}|{reciept.id}')
        markup.add(markup_grouo_or_channel)
    bot.send_message(chat_id=chat_id, text=text, reply_markup=markup)


def detail_group_or_channel(chat_id, receipt, group_or_channel):
    text = f'Здесь вы можете настроить проверку подписки для канала *{group_or_channel.name}* ' \
           f'\.\ Включите «Заявки на вступление», чтобы новые подписчики могли ' \
           f'присоединиться к каналу только после одобрения заявки администраторами'
    markup = types.InlineKeyboardMarkup(row_width=1)
    disconnect = types.InlineKeyboardButton('Отключить', callback_data=f'disconnect|{receipt.id}|{group_or_channel.id}')
    back_to_recept = types.InlineKeyboardButton('Назад к чеку', callback_data=f'detail_recept|{receipt.name}')
    markup.add(disconnect, back_to_recept)
    bot.send_message(chat_id=chat_id, text=text, reply_markup=markup, parse_mode="MarkdownV2")


def disconnect_group_or_channel(chat_id, receipt, group_or_channel):
    receipt.group_or_channels.remove(group_or_channel)
    receipt.save()
    msg = bot.send_message(chat_id=chat_id, text='Канал/группа успешно отключена от вашего чека')
    sleep(3)
    bot.delete_message(chat_id=chat_id, message_id=msg.id)
    detail_recept(chat_id=chat_id, receipt=receipt)


def create_receipts_step_two(message, chat_id, user, message_id, max_activate, number):
    a = True
    bot.delete_message(chat_id=chat_id, message_id=message_id)
    try:
        activates = int(message.text)
        if activates < 1 or activates > max_activate:
            raise TypeError
    except Exception:
        a = False
        error_message = f'❌Введите число от 1 до {max_activate}❌'
        create_receipts_step_one_check(message=message, chat_id=chat_id, user=user,
                                       message_id=message_id,
                                       error_message=error_message, number=number)

    if a:
        reciept = Receipts.objects.create(
            user=user,
            name=f'M{int(time())}',
            price=number,
            number=activates
        )
        detail_recept(chat_id=chat_id, receipt=reciept)


def create_receipts_step_one_check(message, chat_id, user, message_id, error_message='', number=False):
    a = True
    bot.delete_message(chat_id=chat_id, message_id=message_id)
    if not number:
        try:
            number = int(message.text)
            if number < 1 and number > user.balance:
                raise TypeError
        except Exception:
            a = False
            error_message = f'❌Введите число от 1 до {user.balance}❌'
            create_receipts_step_one(chat_id=chat_id, user=user, error_message=error_message)
    if a:
        markup = types.InlineKeyboardMarkup(row_width=1)
        menu = types.InlineKeyboardButton('Главное меню', callback_data='menu')
        markup.add(menu)
        max_activate = user.balance // number
        text = f'{error_message}\n' \
               'Сколько пользователей смогут активировать этот чек?\n\n' \
               f'Максимум: {max_activate}\n' \
               f'Минимум: 1\n\n' \
               'Введите количество активаций:'
        msg = bot.send_message(chat_id=chat_id, text=text, reply_markup=markup)
        bot.register_next_step_handler(msg, create_receipts_step_two, chat_id, user, msg.id,
                                       max_activate, number)


def create_receipts_step_one(chat_id, user, error_message=''):
    text = f'{error_message}' \
           f'Сколько RUB Вы хотите отправить пользователю с помощью чека?\n\n' \
           f'Максимум: {user.balance}RUB\n' \
           f'Минимум: 1 RUB\n\n' \
           f'Введите сумму чека в RUB'
    markup = types.InlineKeyboardMarkup(row_width=1)
    back = types.InlineKeyboardButton('Назад', callback_data='receipts')
    menu = types.InlineKeyboardButton('Главное меню', callback_data='menu')
    markup.add(back, menu)
    msg = bot.send_message(chat_id=chat_id, text=text, reply_markup=markup)
    bot.register_next_step_handler(msg, create_receipts_step_one_check, chat_id, user, msg.id)


def receipts(chat_id):
    text = 'Здесь вы можете создать чек для мгновенной отправки криптовалюты любому пользователю.'
    markup = types.InlineKeyboardMarkup(row_width=1)
    personal = types.InlineKeyboardButton('Создать чек', callback_data='create_receipt')
    all_receipts = types.InlineKeyboardButton('Активные чеки', callback_data='all_receipts')
    menu = types.InlineKeyboardButton('Главное меню', callback_data='menu')
    markup.add(personal, all_receipts, menu)
    bot.send_message(chat_id=chat_id, text=text, reply_markup=markup)


def all_receipts(chat_id, user):
    receipts = Receipts.objects.filter(user=user)
    markup = types.InlineKeyboardMarkup(row_width=1)
    for receipt in receipts:
        add_receipt = types.InlineKeyboardButton(f'{receipt.price} RUB', callback_data=f'detail_recept|{receipt.name}')
        markup.add(add_receipt)
    back_receipts = types.InlineKeyboardButton('Назад к чекам', callback_data='back_receipts')
    markup.add(back_receipts)
    bot.send_message(chat_id=chat_id, text='Здесь вы можете управлять своими созданными чеками.', reply_markup=markup)


def detail_recept(chat_id, receipt):
    price = str(receipt.price).replace('.', ',')
    bot_name = bot.get_me().username
    receipt_name = receipt.name
    text = f'Чек\n\n' \
           f'Сумма: {price} RUB\n\n' \
           'Любой может активировать этот чек\n\n' \
           'Скопируйте ссылку, чтобы поделиться чеком:\n' \
           f'`https://t.me/{bot_name}?start={receipt_name}`\n\n' \
           f'⚠️ Никогда не делайте скриншот вашего чека и не отправляйте его никому\!\ Ссылку на чек могут использовать мошенники, чтобы получить доступ к вашим средствам '
    markup = types.InlineKeyboardMarkup(row_width=1)
    add_subscription = types.InlineKeyboardButton('Проверка подписки',
                                                  callback_data=f'checking_subscription|{receipt_name}')
    delete_receipt = types.InlineKeyboardButton('Удалить чек', callback_data=f'delete_receipt|{receipt_name}')
    all_receipts = types.InlineKeyboardButton('Назад к чекам', callback_data='all_receipts')
    markup.add(add_subscription, delete_receipt, all_receipts)
    bot.send_message(chat_id=chat_id, text=text, reply_markup=markup, parse_mode='MarkdownV2')


@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    message_id = call.message.id
    chat_id = call.message.chat.id
    user = User.objects.get(user_id=call.from_user.id)
    if call.message:
        data = call.data
        bot.delete_message(chat_id=chat_id, message_id=message_id)
        if data == 'menu':
            main_menu(chat_id)

        elif data == 'category':
            categorys(chat_id=chat_id)

        elif data.split('|')[0] == 'subcategories':
            parent = Category.objects.get(id=data.split('|')[1])
            subcategories(chat_id=chat_id, parent=parent)

        elif data.split('|')[0] == 'product':
            category = Category.objects.get(id=data.split('|')[1])
            products(chat_id=chat_id, category=category)

        elif data.split('|')[0] == 'next_page':
            pagination_start = int(data.split('|')[2]) + 10
            pagination_end = int(data.split('|')[3]) + 10
            if data.split('|')[1] == 'category':
                categorys(chat_id, pagination_start, pagination_end)

            elif data.split('|')[1] == 'subcategories':
                id = int(data.split('|')[4])
                parent = Category.objects.get(id=id)
                subcategories(chat_id=chat_id, parent=parent, pagination_start=pagination_start,
                              pagination_end=pagination_end)

            elif data.split('|')[1] == 'product':
                id = int(data.split('|')[4])
                category = Category.objects.get(id=id)
                products(chat_id=chat_id, category=category, pagination_start=pagination_start,
                         pagination_end=pagination_end)

        elif data.split('|')[0] == 'last_page':
            pagination_start = int(data.split('|')[2]) - 10
            pagination_end = int(data.split('|')[3]) - 10
            if data.split('|')[1] == 'category':
                categorys(chat_id=chat_id, pagination_start=pagination_start, pagination_end=pagination_end)

            elif data.split('|')[1] == 'subcategories':
                id = int(data.split('|')[4])
                category = Category.objects.get(id=id)
                products(chat_id=chat_id, category=category, pagination_start=pagination_start,
                         pagination_end=pagination_end)

            elif data.split('|')[1] == 'product':
                id = int(data.split('|')[4])
                category = Category.objects.get(id=id)
                products(chat_id=chat_id, category=category, pagination_start=pagination_start,
                         pagination_end=pagination_end)

        elif data.split('|')[0] == 'new_order':
            product_id = int(data.split('|')[1])
            new_order_step_one(chat_id=chat_id, product_id=product_id)

        elif data == 'my_order':
            my_order(chat_id, user)

        elif data == 'balance':
            balance(chat_id=chat_id, user=user)

        elif data == 'earn':
            earn(chat_id=chat_id, user=user)

        elif data == 'help':
            bot.send_message(chat_id=chat_id, text='Всегда рады помочь! Заходите: https://t.me/smoservice_bot')
            main_menu(chat_id)

        elif data.split('|')[0] == 'faq':
            if len(data.split('|')) == 1:
                faq(chat_id=chat_id, answer='Что вы хотите узнать?')
            else:
                id = int(data.split('|')[1])
                answer = FAQ.objects.get(id=id).answer
                faq(chat_id=chat_id, answer=answer)

        elif data == 'receipts':
            receipts(chat_id=chat_id)

        elif data == 'create_receipt':
            create_receipts_step_one(chat_id=chat_id, user=user)

        elif data == 'all_receipts':
            all_receipts(chat_id=chat_id, user=user)

        elif data.split('|')[0] == 'detail_recept':
            receipt = Receipts.objects.get(name=data.split('|')[1])
            detail_recept(chat_id=chat_id, receipt=receipt)

        elif data.split('|')[0] == 'delete_receipt':
            receipt = Receipts.objects.get(name=data.split('|')[1])
            receipt.delete()
            msg = bot.send_message(chat_id=chat_id, text='Ваш чек был удален')
            sleep(2)
            bot.delete_message(chat_id=chat_id, message_id=msg.id)
            all_receipts(chat_id=chat_id, user=user)

        elif data.split('|')[0] == 'checking_subscription':
            receipt = Receipts.objects.get(name=data.split('|')[1])
            add_checking_subscription(chat_id=chat_id, reciept=receipt)

        elif data.split('|')[0] == 'connect':
            receipt = Receipts.objects.get(name=data.split('|')[1])
            connect(chat_id=chat_id, receipt=receipt, user=user)

        elif data.split('|')[0] == 'GOC':
            group_or_channel = GroupAndChennel.objects.get(id=data.split('|')[1])
            receipt = Receipts.objects.get(id=data.split('|')[2])
            detail_group_or_channel(chat_id=chat_id, receipt=receipt, group_or_channel=group_or_channel)

        elif data.split('|')[0] == 'disconnect':
            group_or_channel = GroupAndChennel.objects.get(id=data.split('|')[2])
            receipt = Receipts.objects.get(id=data.split('|')[1])
            detail_group_or_channel(chat_id=chat_id, receipt=receipt, group_or_channel=group_or_channel)
        elif data.split('|')[0] == 'add_group_or_channel':
            group_or_channel = GroupAndChennel.objects.get(id=data.split('|')[1])
            receipt = Receipts.objects.get(id=data.split('|')[2])
            add_group_or_channel_in_receipt(chat_id=chat_id, receipt=receipt, group_or_channel=group_or_channel)



        elif data.split('|')[0] == 'Check':
            receipt = Receipts.objects.get(id=data.split('|')[1])
            check_subscription_step_two(user_id=chat_id, receipt=receipt)


def check_subscription_step_two(user_id, receipt):
    a = True
    for group_or_channel in receipt.group_or_channels.all():
        group_or_channel_id = group_or_channel.chat_id
        try:
            bot.get_chat_member(chat_id=group_or_channel_id, user_id=user_id)
        except:
            a = False
            msg = bot.send_message(chat_id=user_id, text=f'Вы подписаны не на все каналы')
            sleep(2)
            bot.delete_message(chat_id=user_id, message_id=msg.id)
            check_subscription_step_one(user_id=user_id, receipt=receipt)
            break
    if a:
        text1 = '💰 Вы успешно активировали чек'
        text2 = '💰 Ваш чек был успешно активирован'
        user_get_money = User.objects.get(user_id=user_id)
        user_send_monet = receipt.user
        user_get_money.balance += receipt.price
        user_send_monet.balance -= receipt.price
        receipt.number -= 1
        receipt.user_use.add(user_get_money)
        user_send_monet.save()
        user_get_money.save()
        receipt.save()
        if receipt.number == 0:
            receipt.delete()
        bot.send_message(chat_id=user_id, text=text1)
        bot.send_message(chat_id=user_send_monet.user_id, text=text2)
        main_menu(chat_id=user_id)


def check_subscription_step_one(user_id, receipt):
    markup = types.InlineKeyboardMarkup(row_width=1)
    for group_or_channel in receipt.group_or_channels.all():
        add_group_or_channel_button = types.InlineKeyboardButton(group_or_channel.name,
                                                                 url=group_or_channel.invite_link)
        markup.add(add_group_or_channel_button)
    check = types.InlineKeyboardButton('Проверить подписки', callback_data=f'Check|{receipt.id}')
    markup.add(check)
    bot.send_message(chat_id=user_id, text='Для активации чека подпишитесь на все каналы', reply_markup=markup)


def receipt_check(receipt, user_id):
    user_get_money = User.objects.get(user_id=user_id)
    if receipt.user == user_get_money:
        text = 'Вы не можете активировать перевод, созданный вами.'
        bot.send_message(chat_id=user_id, text=text)
        main_menu(chat_id=user_id)

    elif user_get_money in receipt.user_use.all():
        text = 'Вы уже использовали этот чек'
        bot.send_message(chat_id=user_id, text=text)
        main_menu(chat_id=user_id)
    else:
        if not receipt.group_or_channels.all():
            text1 = '💰 Вы успешно активировали чек'
            text2 = '💰 Ваш чек был успешно активирован'
            user_send_monet = receipt.user
            user_get_money.balance += receipt.price
            user_send_monet.balance -= receipt.price
            receipt.number -= 1
            user_send_monet.save()
            user_get_money.save()
            receipt.save()
            if receipt.number == 0:
                receipt.delete()
            bot.send_message(chat_id=user_id, text=text1)
            bot.send_message(chat_id=user_send_monet.user_id, text=text2)
            main_menu(chat_id=user_id)
        else:
            check_subscription_step_one(user_id=user_id, receipt=receipt)


def create_user(message, user_id):
    if ' ' in message.text:
        inviting_user_id = int(message.text.split()[1])
        inviting_user = User.objects.get(user_id=inviting_user_id)
        user = User.objects.create(
            user_id=user_id,
            inviting_user=inviting_user_id)
        inviting_user.invited_users.add(user)
        inviting_user.balance += 5
        inviting_user.save()

    else:
        User.objects.create(
            user_id=user_id)
    bot.send_message(message.chat.id, 'Приветствуем тебя в нашем боте')


def capcha_check(message, capcha_name, user_id, message_id1, message_id2, receipt):
    bot.delete_message(message_id=message_id1, chat_id=user_id)
    bot.delete_message(message_id=message_id2, chat_id=user_id)
    bot.delete_message(message_id=message.id, chat_id=user_id)
    if str(message.text) == str(capcha_name):
        msg = bot.send_message(chat_id=user_id, text='Вы успешно прошли капчу')
        user = User.objects.get(user_id=user_id)
        user.command_start = 0
        user.save()
        bot.delete_message(message_id=msg.id, chat_id=user_id)
        receipt_check(receipt=receipt, user_id=user_id)
    else:
        msg = bot.send_message(chat_id=user_id, text='Капча пройдена неудачно. Попробуйте еще раз')
        sleep(2)
        bot.delete_message(message_id=msg.id, chat_id=user_id)
        capcha(user_id=user_id, receipt=receipt)


def capcha(receipt, user_id):
    captcha_text = random.randint(10000, 100000)
    image = ImageCaptcha(width=200, height=100)
    captcha = image.generate(str(captcha_text))
    msg1 = bot.send_message(chat_id=user_id, text='Введите капчу, чтобы продолжить работу')
    msg2 = bot.send_photo(chat_id=user_id, photo=captcha)
    bot.register_next_step_handler(msg1, capcha_check, captcha_text, user_id, msg1.id, msg2.id, receipt)


if __name__ == '__main__':
    p1 = Process(target=send_message)
    p1.start()
    p2 = Process(target=check_order_status)
    p2.start()
    p3 = Process(target=check_deposits)
    p3.start()
    p4 = Process(target=update_services)
    p4.start()
    bot.polling(none_stop=True, interval=0)