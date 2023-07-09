from rest_auth.registration.serializers import RegisterSerializer


class CustomRegisterSerializer(RegisterSerializer):
    def save(self, request):
        user = super().save(request)
        # 在这里可以执行其他相关操作，例如自动登录等
        return user

    def send_mail(self, *args, **kwargs):
        # 不执行发送电子邮件的操作，从而停用电子邮件验证
        pass
