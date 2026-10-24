from django.contrib import admin

from .models import Chat, ChatMessage

class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ('sender', 'content', 'is_read', 'created_at')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ('id', 'report', 'owner', 'interested', 'created_at', 'updated_at')
    search_fields = ('owner__email', 'interested__email', 'report__description')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [ChatMessageInline]
