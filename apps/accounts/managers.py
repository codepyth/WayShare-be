# apps/accounts/managers.py
from django.contrib.auth.base_user import BaseUserManager
from apps.core.models import SoftDeleteQuerySet


class UserManager(BaseUserManager.from_queryset(SoftDeleteQuerySet)):
    # Hides soft-deleted users, so they can't log in, and their open sessions stop working.
    def get_queryset(self):
        return super().get_queryset().alive()

    def create_user(self, email, name, password=None, **extra):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, name=name, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("is_adult_confirmed", True)

        if extra.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, name, password, **extra)
