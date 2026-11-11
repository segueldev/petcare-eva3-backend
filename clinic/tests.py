from datetime import datetime, time, timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import Client, TestCase
from django.utils import timezone

from .models import Appointment, Availability, ClinicalRecord, Pet, Reminder, Tutor, Veterinarian


class ClinicTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser("admin", password="demo-test-only-123")
        cls.tutor = Tutor.objects.create(name="Tutor de ejemplo", email="tutor@example.com", phone="123")
        cls.pet = Pet.objects.create(name="Luna", species="Canina", tutor=cls.tutor)
        cls.vet = Veterinarian.objects.create(name="Profesional de ejemplo", specialty="General")
        cls.day = timezone.localdate() + timedelta(days=1)
        cls.start = timezone.make_aware(datetime.combine(cls.day, time(10)))
        Availability.objects.create(veterinarian=cls.vet, weekday=cls.day.weekday(), start=time(9), end=time(17))

    def setUp(self):
        self.client.force_login(self.admin)

    def appointment_data(self, start):
        return {
            "pet": self.pet.pk, "veterinarian": self.vet.pk, "starts_at": start.isoformat(),
            "ends_at": (start + timedelta(minutes=30)).isoformat(),
            "reason": "Consulta de prueba", "status": "booked",
        }

    def test_anonymous_cannot_read_data(self):
        anonymous = Client()
        self.assertEqual(anonymous.get("/").status_code, 302)
        self.assertContains(anonymous.get("/cuenta/login/"), "Iniciar sesión")
        self.assertEqual(anonymous.get("/api/fichas/").status_code, 403)

    def test_roles_limit_clinical_records(self):
        call_command("preparar_roles", verbosity=0)
        user = get_user_model().objects.create_user("recepcion")
        user.groups.add(Group.objects.get(name="Recepción"))
        self.client.force_login(user)
        self.assertEqual(self.client.get("/api/mascotas/").status_code, 200)
        self.assertEqual(self.client.get("/api/fichas/").status_code, 403)
        self.assertEqual(self.client.get("/registros/fichas/").status_code, 403)

    def test_api_tutor_crud(self):
        base = "/api/tutores/"
        result = self.client.post(base, {"name": "Otra tutora", "email": "otra@example.com", "phone": "555"}, content_type="application/json")
        self.assertEqual(result.status_code, 201, result.content)
        item = f"{base}{result.json()['id']}/"
        self.assertEqual(self.client.get(item).status_code, 200)
        self.assertEqual(self.client.patch(item, {"phone": "333"}, content_type="application/json").json()["phone"], "333")
        self.assertEqual(self.client.delete(item).status_code, 204)

    def test_tutor_with_pet_cannot_be_deleted(self):
        result = self.client.delete(f"/api/tutores/{self.tutor.pk}/")
        self.assertEqual(result.status_code, 400)
        self.assertTrue(Tutor.objects.filter(pk=self.tutor.pk).exists())

    def test_api_appointments_prevent_overlap_and_allow_adjacent(self):
        base = "/api/citas/"
        for offset, expected in ((0, 201), (15, 400), (30, 201)):
            response = self.client.post(base, self.appointment_data(self.start + timedelta(minutes=offset)), content_type="application/json")
            self.assertEqual(response.status_code, expected, response.content)
        self.assertEqual(Appointment.objects.count(), 2)

    def test_cancelled_appointment_frees_slot(self):
        base = "/api/citas/"
        first = self.client.post(base, self.appointment_data(self.start), content_type="application/json")
        response = self.client.patch(f"{base}{first.json()['id']}/", {"status": "cancelled"}, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        replacement = self.client.post(base, self.appointment_data(self.start), content_type="application/json")
        self.assertEqual(replacement.status_code, 201)

    def test_cannot_book_outside_schedule(self):
        result = self.client.post("/api/citas/", self.appointment_data(self.start + timedelta(hours=8)), content_type="application/json")
        self.assertEqual(result.status_code, 400, result.content)
        self.assertFalse(Appointment.objects.exists())

    def test_clinical_record_links_to_appointment(self):
        response = self.client.post("/api/citas/", self.appointment_data(self.start), content_type="application/json")
        data = {"appointment": response.json()["id"], "diagnosis": "Control", "treatment": "Reposo", "prescription": "Sin receta", "exams": "Pendientes"}
        saved = self.client.post("/api/fichas/", data, content_type="application/json")
        self.assertEqual(saved.status_code, 201, saved.content)
        self.assertEqual(ClinicalRecord.objects.get().appointment.pet, self.pet)
        duplicate = self.client.post("/api/fichas/", data, content_type="application/json")
        self.assertEqual(duplicate.status_code, 400)

    def test_reminder_repeats_once(self):
        reminder = Reminder.objects.create(
            pet=self.pet, due_date=self.day, interval_days=30, kind="vaccine", note="Refuerzo",
        )
        self.assertEqual(reminder.status_label, "Próximo")
        reminder.completed = True
        reminder.save()
        reminder.save()
        followup = Reminder.objects.get(previous=reminder)
        self.assertEqual(followup.due_date, self.day + timedelta(days=30))
        self.assertFalse(followup.completed)
        self.assertEqual(Reminder.objects.count(), 2)

    def test_calendar_and_admin_render(self):
        call_command("cargar_demo", verbosity=0)
        self.assertContains(self.client.get("/"), "Control preventivo")
        self.assertContains(self.client.get("/admin/"), "Gestión de la clínica")
        self.assertContains(self.client.get("/registros/mascotas/"), "Luna")
        self.assertContains(self.client.get("/registros/citas/nuevo/"), "datetime-local")

    def test_create_tutor_through_web(self):
        response = self.client.post("/registros/tutores/nuevo/", {
            "name": "Tutor creado en web", "email": "web@example.com", "phone": "111",
        })
        self.assertRedirects(response, "/registros/tutores/")
        self.assertTrue(Tutor.objects.filter(email="web@example.com").exists())

    def test_session_requires_csrf_for_api_changes(self):
        browser = Client(enforce_csrf_checks=True)
        browser.force_login(self.admin)
        response = browser.post("/api/tutores/", {
            "name": "Prueba CSRF", "email": "csrf@example.com", "phone": "222",
        }, content_type="application/json")
        self.assertEqual(response.status_code, 403)
