from django.urls import path, include

from . import views

urlpatterns = [
    path('recherche-lecteur',views.recherche_lecteur, name='recherche-lecteur'),
    path('lecteur/<str:type_identifiant>/<str:identifiant>', views.lecteur, name='lecteur'),
    path('lecteur', views.lecteur_analytique, name='lecteur-analytique'),
    path('modification-lecteur/<str:identifiant>', views.modif_lecteur ,name='modif-lecteur'),
    path('distribution-compte-interne/<str:type_identifiant>/<str:identifiant>', views.distribution_compte_interne ,name='distribution-compte-interne'),
    path('suppression-lecteur/<str:identifiant>/<str:list_etab>', views.suppr_lecteur ,name='suppr-lecteur'),
    path('result-modification-lecteur/<str:identifiant>', views.result_modif_lecteur ,name='result-modif-lecteur'),
    path('', views.webhook)
]