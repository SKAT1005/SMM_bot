from django.db import models


class Type_API(models.Model):
    name = models.CharField(max_length=256, verbose_name='Название типа API')
    API_url = models.URLField(verbose_name='API url')

    def __str__(self):
        return self.name


class API(models.Model):
    API_key = models.CharField(max_length=256, verbose_name='API ключ')
    login = models.CharField(max_length=256, verbose_name='Логин')
    password = models.CharField(max_length=64, verbose_name='Пароль')
    type = models.ForeignKey('Type_API', on_delete=models.CASCADE, related_name='api_type', verbose_name='Тип API')

    def __str__(self):
        return self.type.name


class User(models.Model):
    user_id = models.IntegerField(verbose_name='ID пользователя')
    inviting_user = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True,
                                      related_name='inviting', verbose_name='Пригласивший пользователь')
    invited_users = models.ManyToManyField('self', blank=True,
                                           verbose_name='Приглашенные пользователи')
    balance = models.IntegerField(default=0, verbose_name='Баланс')
    orders = models.ManyToManyField('Orders', blank=True, related_name='order',
                                    verbose_name='Заказы')
    money_earned = models.IntegerField(default=0, verbose_name='Денег заработано')
    pay_balanse = models.BooleanField(default=False, verbose_name='Пополняет ли пользователь баланс')
    last_pay_id = models.CharField(max_length=128, blank=True, verbose_name='Последний ID платежа')
    channel_and_group = models.ManyToManyField('GroupAndChennel', blank=True, verbose_name='Группы и чаты пользователя')
    bots = models.ManyToManyField('Bot', blank=True, verbose_name='Боты пользователя')


class Bot(models.Model):
    token = models.CharField(max_length=64, verbose_name='Токен бота')
    is_active = models.BooleanField(default=False, verbose_name='Активирован ли бот')

    def __str__(self):
        return self.token


class Receipts(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='user', verbose_name='Создатель чека')
    name = models.CharField(max_length=64, verbose_name='Имя чека')
    price = models.FloatField(verbose_name='Сумма чека')
    number = models.IntegerField(default=1, verbose_name='Колличество пользховаетлей, которым можно отправить чек')
    group_or_channels = models.ManyToManyField('GroupAndChennel', blank=True,
                                               verbose_name='Группы и чаты для проверки')
    user_use = models.ManyToManyField('User', related_name='use_user', verbose_name='Пользователи, использовавшие чек')


class GroupAndChennel(models.Model):
    name = models.CharField(max_length=128, verbose_name='Название группы/чата')
    chat_id = models.IntegerField(verbose_name='ID группы/чата')
    invite_link = models.CharField(max_length=64, verbose_name='Приглашение в чат')

    def __str__(self):
        return self.name


class Category(models.Model):
    parents = models.ForeignKey('self', blank=True, null=True, on_delete=models.CASCADE, related_name='parent',
                                verbose_name='Категория подкатегории')
    name = models.CharField(max_length=64, verbose_name='Название категории')

    def __str__(self):
        return self.name


class Product(models.Model):
    api = models.ForeignKey('API', on_delete=models.CASCADE, related_name='api', verbose_name='')
    servis_id = models.IntegerField(verbose_name='ID услуги в сервисе')
    category = models.ForeignKey('Category', on_delete=models.CASCADE, related_name='category',
                                 verbose_name='Категория товара')
    min_summ = models.IntegerField(default=0, verbose_name='Минимальное колличество услуг')
    max_summ = models.IntegerField(default=0, verbose_name='Максимальное колличество услуг')
    name = models.CharField(max_length=64, verbose_name='Название товара')
    description = models.CharField(max_length=128, verbose_name='Описание товара')
    price = models.FloatField(verbose_name='Цена товара')
    extra_charge = models.FloatField(default=1, verbose_name='Наценка на услугу(1.1 - наценка на 10%)')

    def __str__(self):
        return self.name


class Orders(models.Model):
    product = models.ForeignKey('Product', null=True, on_delete=models.SET_NULL, related_name='product',
                                verbose_name='Товар')
    order_id = models.IntegerField(blank=True, verbose_name='ID заказа в сервисе', null=True)
    price = models.FloatField(verbose_name='Общая цена заказа')
    quantity = models.IntegerField(verbose_name='Кол-во услуг')
    link = models.URLField(verbose_name='Адрес целевой страницы (ссылка на фото, профиль, видео) ')
    status = models.CharField(max_length=16, verbose_name='Статус заказа')


class FAQ(models.Model):
    question = models.CharField(max_length=32, verbose_name='Вопрос в разделе FAQ')
    answer = models.CharField(max_length=64, verbose_name='Ответ на вопрос')

    def __str__(self):
        return self.question


class Message(models.Model):
    message = models.CharField(max_length=1024, verbose_name='Сообщение')
    photo = models.ImageField(upload_to='message/',verbose_name='Фотография к сообщению', blank=True, null=True)
