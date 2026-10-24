from django.urls import path

from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path(
        'reset/<uidb64>/<token>/',
        views.RestablecerContrasenaView.as_view(),
        name='password_reset_confirm',
    ),
    path(
        'verify-email/<uidb64>/<token>/',
        views.verify_email_view,
        name='verify_email',
    ),
    path(
        'resend-verification/',
        views.resend_verification_view,
        name='resend_verification',
    ),
]
