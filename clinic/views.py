from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db import models
from django.db.models.deletion import ProtectedError
from django.forms import DateInput, DateTimeInput, TimeInput, modelform_factory
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .models import Appointment, Availability, Pet, Reminder
from .resources import RELATED_FIELDS, RESOURCES


def can(user, action, model):
    return user.has_perm(f"clinic.{action}_{model._meta.model_name}")


def require_permission(user, action, model):
    if not can(user, action, model):
        raise PermissionDenied


def navigation(user):
    return [(slug, label) for slug, (model, label, _) in RESOURCES.items() if can(user, "view", model)]


@login_required
def home(request):
    today = timezone.localdate()
    try:
        day = date.fromisoformat(request.GET.get("dia", ""))
    except ValueError:
        day = today
    visits = Appointment.objects.none()
    if can(request.user, "view", Appointment):
        visits = Appointment.objects.filter(starts_at__date=day).select_related("pet", "veterinarian")
    schedules = Availability.objects.none()
    if can(request.user, "view", Availability):
        schedules = Availability.objects.filter(weekday=day.weekday()).select_related("veterinarian")
    # La agenda muestra vencidos y los recordatorios de los próximos siete días.
    reminders = Reminder.objects.none()
    if can(request.user, "view", Reminder):
        reminders = Reminder.objects.filter(
            completed=False, due_date__lte=today + timedelta(days=7)
        ).select_related("pet")[:10]
    return render(request, "clinic/home.html", {
        "nav": navigation(request.user), "day": day, "visits": visits,
        "reminders": reminders, "schedules": schedules,
        "show_visits": can(request.user, "view", Appointment),
        "show_reminders": can(request.user, "view", Reminder),
        "show_schedules": can(request.user, "view", Availability),
        "pet_count": Pet.objects.count() if can(request.user, "view", Pet) else None,
    })


def resource(slug):
    try:
        return RESOURCES[slug]
    except KeyError as exc:
        raise Http404 from exc


@login_required
def listing(request, slug):
    model, title, fields = resource(slug)
    require_permission(request.user, "view", model)
    objects = model.objects.select_related(*RELATED_FIELDS.get(model, ())) if model in RELATED_FIELDS else model.objects.all()
    page = Paginator(objects, 15).get_page(request.GET.get("pagina"))
    columns = [model._meta.get_field(field).verbose_name.capitalize() for field in fields]
    rows = []
    for instance in page.object_list:
        values = []
        for field in fields:
            display = getattr(instance, f"get_{field}_display", None)
            value = display() if display else getattr(instance, field)
            if isinstance(value, bool):
                value = "Sí" if value else "No"
            values.append(value)
        if model is Reminder:
            values.append(instance.status_label)
        rows.append((instance, values))
    if model is Reminder:
        columns.append("Estado")
    return render(request, "clinic/list.html", {
        "nav": navigation(request.user), "slug": slug, "title": title, "page": page,
        "columns": columns, "rows": rows, "may_add": can(request.user, "add", model),
        "may_change": can(request.user, "change", model), "may_delete": can(request.user, "delete", model),
    })


@login_required
@require_http_methods(["GET", "POST"])
def edit(request, slug, pk=None):
    model, title, fields = resource(slug)
    require_permission(request.user, "change" if pk else "add", model)
    instance = get_object_or_404(model, pk=pk) if pk else None
    widgets = {}
    for name in fields:
        field = model._meta.get_field(name)
        if isinstance(field, models.DateTimeField):
            widgets[name] = DateTimeInput(format="%Y-%m-%dT%H:%M", attrs={"type": "datetime-local"})
        elif isinstance(field, models.DateField):
            widgets[name] = DateInput(format="%Y-%m-%d", attrs={"type": "date"})
        elif isinstance(field, models.TimeField):
            widgets[name] = TimeInput(format="%H:%M", attrs={"type": "time"})
    form_class = modelform_factory(model, fields=fields, widgets=widgets)
    form = form_class(request.POST if request.method == "POST" else None, instance=instance)
    if request.method == "POST" and form.is_valid():
        try:
            form.save()
        except ValidationError as exc:
            form.add_error(None, " ".join(exc.messages))
        else:
            messages.success(request, "Cambios guardados.")
            if can(request.user, "view", model):
                return redirect("listing", slug)
            return redirect("home")
    return render(request, "clinic/form.html", {
        "nav": navigation(request.user), "title": title, "slug": slug, "form": form, "editing": bool(pk),
    })


@login_required
@require_http_methods(["GET", "POST"])
def remove(request, slug, pk):
    model, title, _ = resource(slug)
    require_permission(request.user, "delete", model)
    instance = get_object_or_404(model, pk=pk)
    if request.method == "POST":
        try:
            instance.delete()
        except ProtectedError:
            messages.error(request, "El registro tiene datos asociados y no se puede eliminar.")
        else:
            messages.success(request, "Registro eliminado.")
        if can(request.user, "view", model):
            return redirect("listing", slug)
        return redirect("home")
    return render(request, "clinic/delete.html", {
        "nav": navigation(request.user), "title": title, "slug": slug, "instance": instance,
    })
