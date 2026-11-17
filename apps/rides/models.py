from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q
from django.db.models.lookups import LessThanOrEqual
from django.utils import timezone
from apps.core.models import BaseModel, UniqueReferenceMixin
from apps.core.utils import gen_booking_reference, gen_trip_reference
from .constants import (
    CAP_FORMULA_VERSION, MAX_SEATS, MILEAGE_RATE_PENCE,
    BookingKind, BookingStatus, BootSize, Chattiness, TripStatus,
)

# Uniqueness counts live rows only, so a soft-deleted city or route can be created again.
ALIVE = Q(deleted_at__isnull=True)


class City(BaseModel):
    name        = models.CharField(max_length=100)
    slug        = models.SlugField(max_length=100)
    is_active   = models.BooleanField(default=True)

    class Meta:
        db_table            = "cities"
        verbose_name_plural = "cities"
        ordering            = ("name",)
        constraints         = (
            models.UniqueConstraint(fields=("name",), condition=ALIVE, name="unique_city_name"),
            models.UniqueConstraint(fields=("slug",), condition=ALIVE, name="unique_city_slug"),
        )

    def __str__(self):
        return self.name


class PickupPoint(BaseModel):
    city        = models.ForeignKey(City, on_delete=models.PROTECT, related_name="pickup_points")
    name        = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    latitude    = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude   = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta:
        db_table    = "pickup_points"
        ordering    = ("city__name", "name")
        constraints = (
            models.UniqueConstraint(fields=("city", "name"), condition=ALIVE, name="unique_pickup_point_per_city"),
        )

    def __str__(self):
        return f"{self.name}, {self.city}"


class RouteDistance(BaseModel):
    origin_city         = models.ForeignKey(City, on_delete=models.PROTECT, related_name="routes_from")
    destination_city    = models.ForeignKey(City, on_delete=models.PROTECT, related_name="routes_to")
    miles               = models.DecimalField(max_digits=5, decimal_places=1)

    class Meta:
        db_table    = "route_distances"
        ordering    = ("origin_city__name", "destination_city__name")
        constraints = (
            models.UniqueConstraint(fields=("origin_city", "destination_city"), condition=ALIVE, name="unique_route"),
            models.CheckConstraint(condition=~Q(origin_city=F("destination_city")), name="route_cities_differ"),
            models.CheckConstraint(condition=Q(miles__gt=0), name="route_miles_positive"),
        )

    def __str__(self):
        return f"{self.origin_city} → {self.destination_city}: {self.miles} mi"


class Vehicle(BaseModel):
    owner           = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="vehicles")
    make            = models.CharField(max_length=50)
    model           = models.CharField(max_length=50)
    colour          = models.CharField(max_length=30)
    registration    = models.CharField(max_length=8, help_text="Stored uppercase without spaces, e.g. LM19XKR")
    boot_size       = models.CharField(max_length=10, choices=BootSize.choices)

    # Ride preferences, shown to passengers before they book.
    smoking_allowed = models.BooleanField(default=False)
    pets_allowed    = models.BooleanField(default=False)
    music_allowed   = models.BooleanField(default=True)
    chattiness      = models.CharField(max_length=10, choices=Chattiness.choices, default=Chattiness.DEPENDS)

    # Phase 2 (DVSA/DVLA checks) and phase 4 (parcels). Empty until then.
    mot_status              = models.CharField(max_length=30, blank=True)
    mot_expiry              = models.DateField(null=True, blank=True)
    tax_status              = models.CharField(max_length=30, blank=True)
    checks_run_at           = models.DateTimeField(null=True, blank=True)
    gross_plated_weight_kg  = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        db_table    = "vehicles"
        ordering    = ("make", "model")
        constraints = (
            models.UniqueConstraint(fields=("registration",), condition=ALIVE, name="unique_vehicle_registration"),
        )

    def save(self, *args, **kwargs):
        # One spelling per plate, whatever the user typed: "lm19 xkr" -> "LM19XKR".
        self.registration = self.registration.replace(" ", "").upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.colour} {self.make} {self.model} ({self.registration})"


class Trip(UniqueReferenceMixin, BaseModel):
    reference           = models.CharField(max_length=11, unique=True, editable=False, default=gen_trip_reference)
    driver              = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="trips_driven")
    vehicle             = models.ForeignKey(Vehicle, on_delete=models.PROTECT, related_name="trips")

    origin_city         = models.ForeignKey(City, on_delete=models.PROTECT, related_name="trips_from")
    origin_point        = models.ForeignKey(PickupPoint, on_delete=models.PROTECT, related_name="trips_from")
    destination_city    = models.ForeignKey(City, on_delete=models.PROTECT, related_name="trips_to")
    destination_point   = models.ForeignKey(PickupPoint, on_delete=models.PROTECT, related_name="trips_to")
    departs_at          = models.DateTimeField()
    arrives_estimate    = models.DateTimeField(null=True, blank=True)
    distance_miles      = models.DecimalField(max_digits=5, decimal_places=1)

    seats_total         = models.PositiveSmallIntegerField()
    seats_taken         = models.PositiveSmallIntegerField(default=0)

    # Money in integer pence. The rate and formula version are saved per trip, so an old fare
    # can always be explained even after the rate changes.
    fare_pence          = models.PositiveIntegerField(help_text="Per seat")
    mileage_rate_pence  = models.PositiveSmallIntegerField(default=MILEAGE_RATE_PENCE)
    cap_formula_version = models.CharField(max_length=20, default=CAP_FORMULA_VERSION)

    boot_space_offered  = models.BooleanField(default=False)
    parcel_fee_pence    = models.PositiveIntegerField(null=True, blank=True)   # phase 4

    status              = models.CharField(max_length=20, choices=TripStatus.choices, default=TripStatus.DRAFT)
    cancelled_at        = models.DateTimeField(null=True, blank=True)
    cancel_reason       = models.TextField(blank=True)

    class Meta:
        db_table    = "trips"
        ordering    = ("departs_at",)
        indexes     = (
            models.Index(fields=("origin_city", "destination_city", "departs_at"), name="trip_search_idx"),
        )
        constraints = (
            models.CheckConstraint(condition=~Q(origin_city=F("destination_city")), name="trip_cities_differ"),
            models.CheckConstraint(condition=Q(distance_miles__gt=0), name="trip_distance_positive"),
            models.CheckConstraint(condition=Q(seats_total__gte=1, seats_total__lte=MAX_SEATS), name="trip_seats_total_range"),
            models.CheckConstraint(condition=Q(seats_taken__lte=F("seats_total")), name="trip_seats_taken_within_total"),
            # The cost-share cap, enforced by the database itself. Written as a multiplication,
            # so there is no rounding: fare x (seats + 1) <= miles x rate.
            models.CheckConstraint(
                condition=LessThanOrEqual(F("fare_pence") * (F("seats_total") + 1),
                                          F("distance_miles") * F("mileage_rate_pence")),
                name="trip_fare_within_cap",
            ),
        )

    @property
    def seats_left(self):
        # Worked out, never stored (D21).
        return self.seats_total - self.seats_taken

    def clean(self):
        # Rules that span other tables can't be database checks; forms and serializers call clean().
        errors = {}
        if self.origin_point_id and self.origin_point.city_id != self.origin_city_id:
            errors["origin_point"] = "This pickup point is not in the origin city."
        if self.destination_point_id and self.destination_point.city_id != self.destination_city_id:
            errors["destination_point"] = "This pickup point is not in the destination city."
        if self.vehicle_id and self.vehicle.owner_id != self.driver_id:
            errors["vehicle"] = "You can only use your own vehicle."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.reference}: {self.origin_city} → {self.destination_city}"


class Booking(UniqueReferenceMixin, BaseModel):
    reference       = models.CharField(max_length=11, unique=True, editable=False, default=gen_booking_reference)
    trip            = models.ForeignKey(Trip, on_delete=models.PROTECT, related_name="bookings")
    user            = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="bookings")
    kind            = models.CharField(max_length=10, choices=BookingKind.choices, default=BookingKind.SEAT)
    seats           = models.PositiveSmallIntegerField(default=1)
    amount_pence    = models.PositiveIntegerField()
    request_message = models.TextField(max_length=500, blank=True)
    status          = models.CharField(max_length=30, choices=BookingStatus.choices, default=BookingStatus.REQUESTED)

    # One timestamp per step, so the history of a booking can always be read back.
    requested_at    = models.DateTimeField(default=timezone.now)
    accepted_at     = models.DateTimeField(null=True, blank=True)
    declined_at     = models.DateTimeField(null=True, blank=True)
    cancelled_at    = models.DateTimeField(null=True, blank=True)
    cancelled_by    = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                                        null=True, blank=True, related_name="+")
    cancel_reason   = models.TextField(blank=True)

    # Phase 1 completion: both sides confirm the trip happened and the cash amount paid.
    completed_by_passenger_at   = models.DateTimeField(null=True, blank=True)
    completed_by_driver_at      = models.DateTimeField(null=True, blank=True)
    cash_amount_confirmed_pence = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        db_table    = "bookings"
        ordering    = ("-requested_at",)
        indexes     = (
            models.Index(fields=("trip", "status"), name="booking_trip_status_idx"),
            models.Index(fields=("user", "status"), name="booking_user_status_idx"),
        )
        constraints = (
            # A seat booking takes at least one seat; a parcel (phase 4) takes none.
            models.CheckConstraint(condition=Q(kind=BookingKind.PARCEL) | Q(seats__gte=1), name="booking_seat_needs_seats"),
            # One open request or booking per passenger per trip, so a double tap can't book twice.
            models.UniqueConstraint(
                fields=("trip", "user", "kind"),
                condition=ALIVE & Q(status__in=(BookingStatus.REQUESTED, BookingStatus.ACCEPTED)),
                name="one_open_booking_per_trip",
            ),
        )

    def clean(self):
        if self.trip_id and self.user_id and self.trip.driver_id == self.user_id:
            raise ValidationError({"trip": "You can't book your own trip."})

    def __str__(self):
        return f"{self.reference}: {self.user} on {self.trip.reference}"
