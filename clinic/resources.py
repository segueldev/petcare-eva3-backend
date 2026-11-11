from .models import Appointment, Availability, ClinicalRecord, Pet, Reminder, Tutor, Veterinarian

RESOURCES = {
    "tutores": (Tutor, "Tutores", ("name", "email", "phone")),
    "mascotas": (Pet, "Mascotas", ("name", "tutor", "species", "breed", "birth_date")),
    "profesionales": (Veterinarian, "Profesionales", ("name", "specialty")),
    "horarios": (Availability, "Horarios", ("veterinarian", "weekday", "start", "end")),
    "citas": (Appointment, "Citas", ("pet", "veterinarian", "starts_at", "ends_at", "reason", "status")),
    "fichas": (ClinicalRecord, "Fichas clínicas", ("appointment", "diagnosis", "treatment", "prescription", "exams")),
    "recordatorios": (Reminder, "Recordatorios", ("pet", "kind", "due_date", "note", "interval_days", "completed")),
}
RELATED_FIELDS = {
    Pet: ("tutor",), Availability: ("veterinarian",), Appointment: ("pet", "veterinarian"),
    ClinicalRecord: ("appointment__pet",), Reminder: ("pet",),
}
