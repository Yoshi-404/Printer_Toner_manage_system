from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("impressora/<int:pk>/", views.impressora, name="impressora"),
    path("impressora/<int:pk>/troca/", views.registrar_troca, name="troca"),
    path("estoque/", views.estoque, name="estoque"),
    path("coletar/", views.coletar_agora, name="coletar"),
]
