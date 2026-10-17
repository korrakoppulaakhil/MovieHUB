from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm


class AdminPasswordResetForm(PasswordResetForm):
    def send_mail(
        self,
        subject_template_name,
        email_template_name,
        context,
        from_email,
        to_email,
        html_email_template_name=None,
    ):
        backup_email = getattr(settings, "ADMIN_PASSWORD_RESET_EMAIL", "")
        if (
            context["user"].is_superuser
            and backup_email
            and self.cleaned_data["email"].casefold() == backup_email.casefold()
        ):
            to_email = backup_email
            context = {**context, "email": backup_email}

        return super().send_mail(
            subject_template_name,
            email_template_name,
            context,
            from_email,
            to_email,
            html_email_template_name=html_email_template_name,
        )

    def get_users(self, email):
        yielded_user_ids = set()
        for user in super().get_users(email):
            if user.is_staff:
                yielded_user_ids.add(user.pk)
                yield user

        backup_email = getattr(settings, "ADMIN_PASSWORD_RESET_EMAIL", "")
        if not backup_email or email.casefold() != backup_email.casefold():
            return

        superusers = get_user_model()._default_manager.filter(
            is_active=True,
            is_staff=True,
            is_superuser=True,
        )
        if superusers.count() != 1:
            return

        user = superusers.first()
        if (
            user is not None
            and user.pk not in yielded_user_ids
            and user.has_usable_password()
        ):
            yield user
