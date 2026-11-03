# apps/accounts/models.py
import pathlib
import uuid
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from apps.core.models import BaseModel
from .managers import UserManager


def avatar_upload_to(instance, filename):
    # Random file name: never trust the uploaded name, and don't put the user's id in a public URL.
    return f"avatars/{uuid.uuid4().hex}{pathlib.Path(filename).suffix.lower()}"


class User(BaseModel, AbstractBaseUser, PermissionsMixin):
    email =     models.EmailField(unique=True)
    name =      models.CharField(max_length=120)
    phone =     models.CharField(max_length=20, blank=True)
    bio =       models.TextField(max_length=500, blank=True)
    avatar =    models.ImageField(upload_to=avatar_upload_to, max_length=255, blank=True)

    driver_enabled     = models.BooleanField(default=False)
    is_adult_confirmed = models.BooleanField(default=False)

    phone_verified_at  = models.DateTimeField(null=True, blank=True)
    licence_checked_at = models.DateTimeField(null=True, blank=True)
    id_verified_at     = models.DateTimeField(null=True, blank=True)

    suspended_at       = models.DateTimeField(null=True, blank=True)
    suspended_reason   = models.TextField(blank=True)

    is_active          = models.BooleanField(default=True)
    is_staff           = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    class Meta:
        db_table = "users"

    def __str__(self):
        return f"{self.name} <{self.email}>"
