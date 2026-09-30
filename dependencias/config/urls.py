from django.urls import path
from django.contrib.auth.views import LogoutView
from receiver import views

urlpatterns = [
    path('health/', views.health),
    path('login/', views.sign_in),
    path('logout/', LogoutView.as_view()),
    path('', views.inbox),
    path('expedientes/<uuid:pk>/', views.detail),
    path('documentos/<uuid:pk>/', views.download),
    path('expedientes/<uuid:pk>/resolver/<str:area>/', views.resolve),
    path('api/expedientes/<uuid:pk>/', views.exchange),
    path('api/expedientes/<uuid:pk>/documentos/<uuid:doc_id>/', views.upload),
    path('api/expedientes/<uuid:pk>/confirmar/', views.confirm),
]
