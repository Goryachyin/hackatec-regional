from django.urls import path
from . import views

urlpatterns = [
    path('auth/session/', views.session),
    path('auth/register/', views.register),
    path('auth/verify/', views.verify),
    path('auth/resend/', views.resend),
    path('auth/login/', views.sign_in),
    path('auth/logout/', views.sign_out),
    path('catalog/', views.catalog),
    path('documents/', views.documents),
    path('documents/<uuid:doc_id>/', views.manage_document),
    path('documents/<uuid:doc_id>/download/', views.download),
    path('documents/<uuid:doc_id>/analyze/', views.reanalyze),
    path('applications/', views.applications),
    path('applications/<uuid:app_id>/', views.application_detail),
    path('applications/<uuid:app_id>/submit/', views.submit),
]
