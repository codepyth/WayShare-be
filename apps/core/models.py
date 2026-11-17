# apps/core/models.py — shared models used by every app.
import uuid
from django.db import IntegrityError, models, transaction
from django.utils import timezone

REFERENCE_RETRIES = 5


class SoftDeleteQuerySet(models.QuerySet):
    def alive(self):
        return self.filter(deleted_at__isnull=True)

    def deleted(self):
        return self.filter(deleted_at__isnull=False)

    def soft_delete(self):
        now = timezone.now()
        return self.update(deleted_at=now, updated_at=now)

    def restore(self):
        return self.update(deleted_at=None, updated_at=timezone.now())


class SoftDeleteManager(models.Manager.from_queryset(SoftDeleteQuerySet)):
    # Default manager: soft-deleted rows are hidden from every normal query.
    def get_queryset(self):
        return super().get_queryset().alive()


class BaseModel(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects     = SoftDeleteManager()             # live rows only
    all_objects = SoftDeleteQuerySet.as_manager()  # every row, for admin, audits and restores

    class Meta:
        abstract = True

    @property
    def is_deleted(self):
        return self.deleted_at is not None

    # .delete() stays a real delete on purpose (GDPR erasure, test clean-up).
    # Normal app code removes rows with soft_delete().
    def soft_delete(self):
        self.deleted_at = timezone.now()
        self.save(update_fields=("deleted_at", "updated_at"))

    def restore(self):
        self.deleted_at = None
        self.save(update_fields=("deleted_at", "updated_at"))


class UniqueReferenceMixin:
    # For models with a random `reference` (WS-/BK-). If a new row's code clashes with an
    # existing one, draw a fresh code and try again instead of failing the request.
    def save(self, *args, **kwargs):
        if not self._state.adding:
            return super().save(*args, **kwargs)
        generate = self._meta.get_field("reference").default
        for attempt in range(REFERENCE_RETRIES):
            try:
                with transaction.atomic():     # savepoint: a failed insert can't break the outer transaction
                    return super().save(*args, **kwargs)
            except IntegrityError:
                clash = type(self).all_objects.filter(reference=self.reference).exists()
                if not clash or attempt == REFERENCE_RETRIES - 1:
                    raise                      # a different rule failed, or we are out of retries
                self.reference = generate()
