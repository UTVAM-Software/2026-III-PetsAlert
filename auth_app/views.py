from django.shortcuts import render
from django.http import JsonResponse
from firebase_admin import auth

def login_view(request):
    if request.method == 'POST':
        id_token = request.POST.get('id_token')
        try:
            decoded_token = auth.verify_id_token(id_token)
            request.session['uid'] = decoded_token['uid']
            request.session['is_admin'] = decoded_token.get('admin', False)
            return JsonResponse({'status': 'success'})
        except Exception:
            return JsonResponse({'status': 'error'}, status=400)
            
    return render(request, 'auth_app/login.html')

def register_view(request):
    return render(request, 'auth_app/register.html')

def forgot_password_view(request):
    return render(request, 'auth_app/forgot_password.html')