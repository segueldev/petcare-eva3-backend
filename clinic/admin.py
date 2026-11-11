from django.contrib import admin

from .models import Appointment, Availability, ClinicalRecord, Pet, Reminder, Tutor, Veterinarian

admin.site.site_header = "PetCare · Administración"
admin.site.site_title = "PetCare"
admin.site.index_title = "Gestión de la clínica"


@admin.register(Tutor)
class TutorAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone")
    search_fields = ("name", "email", "phone")


@admin.register(Pet)
class PetAdmin(admin.ModelAdmin):
    list_display = ("name", "species", "breed", "tutor")
    list_filter = ("species",)
    search_fields = ("name", "tutor__name")
    autocomplete_fields = ("tutor",)


@admin.register(Veterinarian)
class VeterinarianAdmin(admin.ModelAdmin):
    list_display = ("name", "specialty")
    list_filter = ("specialty",)
    search_fields = ("name", "specialty")


@admin.register(Availability)
class AvailabilityAdmin(admin.ModelAdmin):
    list_display = ("veterinarian", "weekday", "start", "end")
    list_filter = ("weekday", "veterinarian")
    search_fields = ("veterinarian__name",)


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("pet", "veterinarian", "starts_at", "ends_at", "status")
    list_filter = ("status", "veterinarian")
    search_fields = ("pet__name", "veterinarian__name", "reason")
    date_hierarchy = "starts_at"
    autocomplete_fields = ("pet", "veterinarian")


@admin.register(ClinicalRecord)
class ClinicalRecordAdmin(admin.ModelAdmin):
    list_display = ("appointment", "diagnosis")
    list_filter = ("appointment__veterinarian",)
    search_fields = ("appointment__pet__name", "diagnosis")
    autocomplete_fields = ("appointment",)


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ("pet", "kind", "due_date", "completed", "status_label")
    list_filter = ("kind", "completed", "due_date")
    search_fields = ("pet__name", "note")
    autocomplete_fields = ("pet",)
