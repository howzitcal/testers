from django.urls import path

from . import views

urlpatterns = [
    path("", views.lead_list, name="lead_list"),
    path("leads/new/", views.lead_create, name="lead_create"),
    path("leads/<int:pk>/edit/", views.lead_edit, name="lead_edit"),
    path("leads/<int:pk>/delete/", views.lead_delete, name="lead_delete"),
]
