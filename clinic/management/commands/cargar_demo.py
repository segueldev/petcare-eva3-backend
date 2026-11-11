from datetime import datetime, time, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from clinic.models import Appointment, Availability, ClinicalRecord, Pet, Reminder, Tutor, Veterinarian


class Command(BaseCommand):
    help = "Crea registros ficticios para mostrar la aplicación."

    @transaction.atomic
    def handle(self, *args, **options):
        tutor, _ = Tutor.objects.get_or_create(email="tutora@example.com", defaults={
            "name": "Camila Soto (demo)", "phone": "+56 9 0000 0000",
        })
        pet, _ = Pet.objects.get_or_create(tutor=tutor, name="Luna", defaults={
            "species": "Canina", "breed": "Mestiza",
        })
        vet, _ = Veterinarian.objects.get_or_create(
            name="Valeria Rojas (demo)", defaults={"specialty": "Medicina general"},
        )
        day = timezone.localdate()
        for weekday in range(7):
            Availability.objects.get_or_create(
                veterinarian=vet, weekday=weekday, start=time(9), end=time(17),
            )
        start = timezone.make_aware(datetime.combine(day, time(10)))
        appointment, _ = Appointment.objects.get_or_create(
            pet=pet, veterinarian=vet, starts_at=start,
            defaults={"ends_at": start + timedelta(minutes=30), "reason": "Control preventivo"},
        )
        ClinicalRecord.objects.get_or_create(appointment=appointment, defaults={
            "diagnosis": "Control preventivo sin hallazgos relevantes (demo).",
            "treatment": "Seguimiento habitual.",
            "prescription": "Sin receta.",
            "exams": "Sin exámenes solicitados.",
        })
        Reminder.objects.get_or_create(
            pet=pet, kind=Reminder.Kind.VACCINE, due_date=day + timedelta(days=3),
            defaults={"note": "Refuerzo anual de vacuna", "interval_days": 365},
        )
        Reminder.objects.get_or_create(
            pet=pet, kind=Reminder.Kind.CHECKUP, due_date=day + timedelta(days=6),
            defaults={"note": "Control semestral", "interval_days": 180},
        )
        self.stdout.write(self.style.SUCCESS("Datos ficticios preparados para la agenda de hoy."))
