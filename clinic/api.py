from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models.deletion import ProtectedError
from rest_framework import serializers, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.routers import DefaultRouter

from .resources import RELATED_FIELDS, RESOURCES


class ClinicPermissions(DjangoModelPermissions):
    # Las lecturas de la API también exigen el permiso de ver el modelo.
    perms_map = {
        **DjangoModelPermissions.perms_map,
        "GET": ["%(app_label)s.view_%(model_name)s"],
        "HEAD": ["%(app_label)s.view_%(model_name)s"],
    }


class ClinicSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        try:
            return super().create(validated_data)
        except DjangoValidationError as exc:
            raise ValidationError(exc.message_dict if hasattr(exc, "message_dict") else exc.messages) from exc

    def update(self, instance, validated_data):
        try:
            return super().update(instance, validated_data)
        except DjangoValidationError as exc:
            raise ValidationError(exc.message_dict if hasattr(exc, "message_dict") else exc.messages) from exc


class ClinicViewSet(viewsets.ModelViewSet):
    permission_classes = [ClinicPermissions]

    def perform_destroy(self, instance):
        try:
            super().perform_destroy(instance)
        except ProtectedError as exc:
            raise ValidationError("El registro tiene datos asociados y no se puede eliminar.") from exc


# El registro de recursos mantiene los mismos modelos en las vistas web y en la API.
router = DefaultRouter()
for slug, (model, _, fields) in RESOURCES.items():
    serializer = type(f"{model.__name__}Serializer", (ClinicSerializer,), {
        "Meta": type("Meta", (), {"model": model, "fields": ("id", *fields)}),
    })
    view = type(f"{model.__name__}ViewSet", (ClinicViewSet,), {
        "queryset": model.objects.select_related(*RELATED_FIELDS[model]) if model in RELATED_FIELDS else model.objects.all(),
        "serializer_class": serializer,
    })
    router.register(slug, view)
