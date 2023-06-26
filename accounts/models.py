from django.db import models
from django.contrib.auth.models import AbstractUser
from subscription.models import Subscription
from django.utils import timezone


class CustomUser(AbstractUser):
    subscription = models.ForeignKey(
        Subscription, on_delete=models.SET_NULL, null=True, blank=True
    )
    subscription_start = models.DateTimeField(null=True, blank=True)  # 訂閱的開始時間
    remaining_balance = models.DecimalField(
        max_digits=10, decimal_places=2, default=100.00
    )

    @property
    def is_subscription_active(self):
        if self.subscription and self.subscription_start:
            return self.subscription_start + self.subscription.duration > timezone.now()
        else:
            return False
