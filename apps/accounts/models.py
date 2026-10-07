# apps/accounts/models.py
import uuid
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    id =        models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email =     models.EmailField(unique=True)
    name =      models.CharField(max_length=120)
    phone =     models.CharField(max_length=20, blank=True)

    driver_enabled     = models.BooleanField(default=False)
    is_adult_confirmed = models.BooleanField(default=False)

    phone_verified_at  = models.DateTimeField(null=True, blank=True)
    licence_checked_at = models.DateTimeField(null=True, blank=True)
    id_verified_at     = models.DateTimeField(null=True, blank=True)

    suspended_at       = models.DateTimeField(null=True, blank=True)
    suspended_reason   = models.TextField(blank=True)
    deleted_at         = models.DateTimeField(null=True, blank=True)

    is_active          = models.BooleanField(default=True)
    is_staff           = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    def __str__(self):
        return f"{self.name} <{self.email}>"