from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Configura los grupos de recepción y profesionales con permisos de la clínica."

    def handle(self, *args, **options):
        permissions = Permission.objects.filter(content_type__app_label="clinic")
        reception, _ = Group.objects.get_or_create(name="Recepción")
        professional, _ = Group.objects.get_or_create(name="Profesionales")
        reception.permissions.set(permissions.filter(content_type__model__in=(
            "tutor", "pet", "veterinarian", "availability", "appointment", "reminder",
        )))
        professional.permissions.set(permissions.exclude(codename__in=(
            "delete_tutor", "delete_pet", "delete_veterinarian", "delete_availability",
            "add_tutor", "change_tutor", "add_veterinarian", "change_veterinarian",
        )))
        self.stdout.write(self.style.SUCCESS("Grupos Recepción y Profesionales configurados."))
