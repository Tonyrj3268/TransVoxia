from django.contrib import admin
from .models import CustomUser


# Register your models here.
class CustomUserAdmin(admin.ModelAdmin):
    list_display = (
        "username",
        "email",
        "subscription",
        "subscription_start",
        "remaining_balance",
    )  # 將這裡的欄位名稱換成你的模型的欄位名稱


admin.site.register(CustomUser, CustomUserAdmin)
