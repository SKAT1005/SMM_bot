from django.contrib import admin

from Models.models import User, Product, Orders, Category, FAQ, Message, API, Type_API, Receipts, GroupAndChennel, Bot


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    pass

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    pass

@admin.register(Orders)
class OrdersAdmin(admin.ModelAdmin):
    pass

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    pass

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    pass

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    pass

@admin.register(API)
class APIAdmin(admin.ModelAdmin):
    pass


@admin.register(Type_API)
class TypeAPIAdmin(admin.ModelAdmin):
    pass

@admin.register(Receipts)
class ReceiptsAdmin(admin.ModelAdmin):
    pass

@admin.register(GroupAndChennel)
class GroupAndChennelAdmin(admin.ModelAdmin):
    pass


@admin.register(Bot)
class BotAdmin(admin.ModelAdmin):
    pass
