from django.urls import path
from . import views

urlpatterns = [
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('', views.feed_screen, name='feed_screen'),
    path('add/', views.add_report_screen, name='add_report_screen'),
    path('add/<str:pk>/', views.add_report_screen, name='edit_report_screen'),
    path('<str:pk>/', views.pet_detail_screen, name='pet_detail_screen'),
    path('edit/<str:pk>/', views.edit_report_screen, name='edit_report_screen'),
]