from django.db import models


class TripStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PUBLISHED = "published", "Published"
    FULL = "full", "Full"
    DEPARTED = "departed", "Departed"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"


class BookingStatus(models.TextChoices):
    REQUESTED = "requested", "Requested"
    ACCEPTED = "accepted", "Accepted"
    DECLINED = "declined", "Declined"
    EXPIRED = "expired", "Expired"
    CANCELLED_BY_PASSENGER = "cancelled_by_passenger", "Cancelled by Passenger"
    CANCELLED_BY_DRIVER = "cancelled_by_driver", "Cancelled by Driver"
    TRAVELLED = "travelled", "Travelled"
    COMPLETED = "completed", "Completed"
    DISPUTED = "disputed", "Disputed"


class ParcelStatus(models.TextChoices):
    REQUESTED = "requested", "Requested"
    ACCEPTED = "accepted", "Accepted"
    COLLECTED = "collected", "Collected"
    IN_TRANSIT = "in_transit", "In Transit"
    DELIVERED = "delivered", "Delivered"
    CONFIRMED = "confirmed", "Confirmed"

class BookingKind(models.TextChoices):
    SEAT = "seat", "Seat"
    PARCEL = "parcel", "Parcel"


class BootSize(models.TextChoices):
    SMALL = "small", "Small"
    MEDIUM = "medium", "Medium"
    LARGE = "large", "Large"


class Chattiness(models.TextChoices):
    QUIET = "quiet", "Quiet"
    DEPENDS = "depends", "Depends on my mood"
    CHATTY = "chatty", "Chatty"


# Cost-share cap (D22): fare per seat <= (distance_miles x MILEAGE_RATE_PENCE) / (seats_total + 1).
# 55p is HMRC's approved mileage rate. Each trip stores the rate and version it was priced with.
MILEAGE_RATE_PENCE  = 55
CAP_FORMULA_VERSION = "2026-1"
MAX_SEATS           = 8
