from django.contrib.auth.forms import PasswordResetForm


class AdminPasswordResetForm(PasswordResetForm):
    def get_users(self, email):
        for user in super().get_users(email):
            if user.is_staff:
                yield user
