from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone


class Tutor(models.Model):
    name = models.CharField("nombre", max_length=120)
    email = models.EmailField("correo", unique=True)
    phone = models.CharField("teléfono", max_length=25)

    class Meta:
        ordering = ["name"]
        verbose_name = "tutor"
        verbose_name_plural = "tutores"

    def __str__(self):
        return self.name


class Pet(models.Model):
    tutor = models.ForeignKey(Tutor, on_delete=models.PROTECT, verbose_name="tutor")
    name = models.CharField("nombre", max_length=80)
    species = models.CharField("especie", max_length=40)
    breed = models.CharField("raza", max_length=60, blank=True)
    birth_date = models.DateField("fecha de nacimiento", blank=True, null=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "mascota"

    def __str__(self):
        return self.name


class Veterinarian(models.Model):
    name = models.CharField("nombre", max_length=120)
    specialty = models.CharField("especialidad", max_length=100)

    class Meta:
        ordering = ["name"]
        verbose_name = "profesional"
        verbose_name_plural = "profesionales"

    def __str__(self):
        return self.name


class Availability(models.Model):
    class Day(models.IntegerChoices):
        MONDAY = 0, "Lunes"
        TUESDAY = 1, "Martes"
        WEDNESDAY = 2, "Miércoles"
        THURSDAY = 3, "Jueves"
        FRIDAY = 4, "Viernes"
        SATURDAY = 5, "Sábado"
        SUNDAY = 6, "Domingo"

    veterinarian = models.ForeignKey(Veterinarian, on_delete=models.CASCADE, verbose_name="profesional")
    weekday = models.PositiveSmallIntegerField("día", choices=Day.choices)
    start = models.TimeField("inicio")
    end = models.TimeField("fin")

    class Meta:
        ordering = ["weekday", "start"]
        verbose_name = "horario"
        constraints = [
            models.CheckConstraint(condition=models.Q(end__gt=models.F("start")), name="availability_valid_range"),
        ]

    def clean(self):
        if self.start and self.end and self.end <= self.start:
            raise ValidationError({"end": "El horario debe terminar después del inicio."})

    def save(self, *args, **kwargs):
        self.clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.veterinarian} · {self.get_weekday_display()} {self.start:%H:%M}–{self.end:%H:%M}"


class Appointment(models.Model):
    class Status(models.TextChoices):
        BOOKED = "booked", "Agendada"
        ATTENDED = "attended", "Atendida"
        CANCELLED = "cancelled", "Cancelada"

    pet = models.ForeignKey(Pet, on_delete=models.PROTECT, verbose_name="mascota")
    veterinarian = models.ForeignKey(Veterinarian, on_delete=models.PROTECT, verbose_name="profesional")
    starts_at = models.DateTimeField("inicio")
    ends_at = models.DateTimeField("término")
    reason = models.CharField("motivo", max_length=200)
    status = models.CharField("estado", max_length=12, choices=Status.choices, default=Status.BOOKED)

    class Meta:
        ordering = ["starts_at"]
        verbose_name = "cita"
        indexes = [models.Index(fields=["veterinarian", "starts_at"])]
        constraints = [
            models.CheckConstraint(condition=models.Q(ends_at__gt=models.F("starts_at")), name="appointment_valid_range"),
        ]

    def clean(self):
        if not self.starts_at or not self.ends_at:
            return
        if self.ends_at <= self.starts_at:
            raise ValidationError({"ends_at": "El término debe ser posterior al inicio."})
        if self.status == self.Status.CANCELLED or not self.veterinarian_id:
            return
        start = timezone.localtime(self.starts_at)
        end = timezone.localtime(self.ends_at)
        available = Availability.objects.filter(
            veterinarian_id=self.veterinarian_id, weekday=start.weekday(),
            start__lte=start.time(), end__gte=end.time(),
        )
        if start.date() != end.date() or not available.exists():
            raise ValidationError("La cita debe quedar dentro del horario del profesional.")
        overlaps = Appointment.objects.filter(
            veterinarian_id=self.veterinarian_id,
            starts_at__lt=self.ends_at, ends_at__gt=self.starts_at,
        ).exclude(status=self.Status.CANCELLED).exclude(pk=self.pk)
        if overlaps.exists():
            raise ValidationError("El profesional ya tiene otra cita en ese horario.")

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if self.veterinarian_id:
                Veterinarian.objects.select_for_update().get(pk=self.veterinarian_id)
            self.clean()
            return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.pet} · {timezone.localtime(self.starts_at):%d/%m/%Y %H:%M}"


class ClinicalRecord(models.Model):
    appointment = models.OneToOneField(Appointment, on_delete=models.PROTECT, verbose_name="cita")
    diagnosis = models.TextField("diagnóstico")
    treatment = models.TextField("tratamiento", blank=True)
    prescription = models.TextField("receta", blank=True)
    exams = models.TextField("exámenes", blank=True)

    class Meta:
        ordering = ["-appointment__starts_at"]
        verbose_name = "ficha clínica"
        verbose_name_plural = "fichas clínicas"

    def __str__(self):
        return str(self.appointment)


class Reminder(models.Model):
    class Kind(models.TextChoices):
        VACCINE = "vaccine", "Vacunación"
        CHECKUP = "checkup", "Control periódico"

    pet = models.ForeignKey(Pet, on_delete=models.PROTECT, verbose_name="mascota")
    kind = models.CharField("tipo", max_length=12, choices=Kind.choices)
    due_date = models.DateField("fecha programada")
    note = models.CharField("detalle", max_length=160)
    interval_days = models.PositiveSmallIntegerField("repetir cada (días)", default=0)
    completed = models.BooleanField("completado", default=False)
    previous = models.OneToOneField(
        "self", on_delete=models.SET_NULL, null=True, blank=True,
        editable=False, related_name="next_occurrence",
    )

    class Meta:
        ordering = ["due_date"]
        verbose_name = "recordatorio"

    @property
    def status_label(self):
        if self.completed:
            return "Completado"
        if self.due_date < timezone.localdate():
            return "Vencido"
        if self.due_date <= timezone.localdate() + timedelta(days=7):
            return "Próximo"
        return "Programado"

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if self.pk:
                Reminder.objects.select_for_update().get(pk=self.pk)
            super().save(*args, **kwargs)
            if self.completed and self.interval_days:
                next_date = self.due_date + timedelta(days=self.interval_days)
                Reminder.objects.get_or_create(previous=self, defaults={
                    "pet": self.pet, "kind": self.kind, "due_date": next_date,
                    "note": self.note, "interval_days": self.interval_days,
                })

    def __str__(self):
        return f"{self.pet} · {self.get_kind_display()} · {self.due_date:%d/%m/%Y}"
