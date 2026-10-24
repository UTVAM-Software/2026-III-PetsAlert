from django.urls import include, path
from rest_framework.routers import SimpleRouter

from . import views

router = SimpleRouter()
router.register('reports', views.PetReportViewSet, basename='report')

urlpatterns = [

    path('', views.feed_screen, name='feed_screen'),
    path('add/', views.add_report_screen, name='add_report_screen'),
    path('add/<int:pk>/', views.add_report_screen, name='edit_report_screen'),

    path('api/', include(router.urls)),

    path('<int:pk>/', views.pet_detail_screen, name='pet_detail_screen'),
]
