from django.shortcuts import render


def chat_list_screen(request):
    return render(request, 'chat/chat_list_screen.html')


def chat_room_screen(request, receiver_id):
    return render(
        request,
        'chat/chat_room_screen.html',
        {'receiver_id': receiver_id},
    )
