from django.contrib import admin
from django.urls import include, path

from clinic import views
from clinic.api import router

urlpatterns = [
    path("", views.home, name="home"),
    path("cuenta/", include("django.contrib.auth.urls")),
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    path("api-auth/", include("rest_framework.urls")),
    path("registros/<slug:slug>/", views.listing, name="listing"),
    path("registros/<slug:slug>/nuevo/", views.edit, name="add"),
    path("registros/<slug:slug>/<int:pk>/editar/", views.edit, name="edit"),
    path("registros/<slug:slug>/<int:pk>/eliminar/", views.remove, name="remove"),
]
