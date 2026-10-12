from django.shortcuts import redirect
from functools import wraps

def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.session.get('is_admin', False):
            return redirect('feed')
        return view_func(request, *args, **kwargs)
    return _wrapped_view