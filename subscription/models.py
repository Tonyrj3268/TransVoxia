from datetime import timedelta

from django.db import models


# Create your models here.
class Subscription(models.Model):
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    duration = models.DurationField(default=timedelta(days=30))  # 訂閱的有效期
    # 你可以在此添加其他與訂閱相關的欄位

    def __str__(self):
        return self.name

    def getPrice(self):
        return self.price
