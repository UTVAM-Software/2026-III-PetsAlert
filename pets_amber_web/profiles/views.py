from django.shortcuts import render


def profile_screen(request):
    return render(request, 'profiles/profile_screen.html')


def my_reports_screen(request):
    return render(request, 'profiles/my_reports_screen.html')


def privacy_screen(request):
    return render(request, 'profiles/privacy_screen.html')
