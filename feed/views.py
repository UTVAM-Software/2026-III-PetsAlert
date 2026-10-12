from django.shortcuts import render
from auth_app.decorators import admin_required
from firebase_admin import firestore


def feed_screen(request):
    return render(request, 'feed/feed_screen.html')


def add_report_screen(request, pk=None):
    return render(
        request,
        'feed/add_report_screen.html',
        {'reporte_id': pk}
    )


def pet_detail_screen(request, pk):
    return render(
        request,
        'feed/pet_detail_screen.html',
        {'reporte_id': pk}
    )


@admin_required
def admin_dashboard(request):
    return render(request, 'feed/admin_dashboard.html')

def edit_report_screen(request, pk):
    return render(request, 'feed/add_report_screen.html', {'reporte_id': pk})