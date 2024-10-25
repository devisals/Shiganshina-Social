from django.contrib import admin

# Register your models here.
from .models import RemoteNode

@admin.action(description='Enable remote node(s)')
def approve_users(modeladmin, request, queryset):
    # Only set users as active if they are not a node
    queryset.update(disabled=False)

@admin.action(description='Disable remote node(s)')
def disable_users(modeladmin, request, queryset):
    # Only set users as active if they are not a node
    queryset.update(disabled=True)

class RemoteNodeAdmin(admin.ModelAdmin):
    list_display = [
        'nodeName',
        'displayName',
        'url',
        'password',
        'disabled'
    ]
    actions = [
        approve_users,  # custom action to approve users
        disable_users    # custom action to set user as a remote node
    ]


admin.site.register(RemoteNode, RemoteNodeAdmin)