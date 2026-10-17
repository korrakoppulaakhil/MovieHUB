import re

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    STORAGES={
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    },
)
class AdminPasswordResetTests(TestCase):
    def test_admin_login_has_password_reset_link(self):
        response = self.client.get("/admin/login/")

        self.assertContains(response, "/admin/password_reset/")

    def test_reset_email_is_sent_to_staff_account(self):
        user_model = get_user_model()
        user_model.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="old-password",
            is_staff=True,
        )

        response = self.client.post(
            "/admin/password_reset/",
            {"email": "admin@example.com"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response["Location"],
            "/admin/password_reset/done/",
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("/admin/reset/", mail.outbox[0].body)
        reset_path = re.search(
            r"http://testserver(/admin/reset/\S+)",
            mail.outbox[0].body,
        ).group(1)

        confirm_response = self.client.get(reset_path)
        self.assertEqual(confirm_response.status_code, 302)

        reset_response = self.client.post(
            confirm_response["Location"],
            {
                "new_password1": "brand-new-safe-passphrase",
                "new_password2": "brand-new-safe-passphrase",
            },
        )

        self.assertRedirects(
            reset_response,
            "/admin/reset/done/",
            fetch_redirect_response=False,
        )
        user = user_model.objects.get(username="admin")
        self.assertTrue(user.check_password("brand-new-safe-passphrase"))

    def test_reset_email_is_not_sent_to_non_staff_account(self):
        user_model = get_user_model()
        user_model.objects.create_user(
            username="customer",
            email="customer@example.com",
            password="old-password",
        )

        self.client.post(
            "/admin/password_reset/",
            {"email": "customer@example.com"},
        )

        self.assertEqual(len(mail.outbox), 0)
