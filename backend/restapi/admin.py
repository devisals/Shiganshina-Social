from django.contrib import admin

# Register your models here.

from . import models as user_models
from post import models as post_models

@admin.action(description='Approve selected user(s)')
def approve_users(modeladmin, request, queryset):
    # Only set users as active if they are not a node
    queryset.filter(is_node=False).update(is_active=True)

@admin.action(description='Set selected user(s) as node')
def set_as_node(modeladmin, request, queryset):
    # Only set users as nodes if they are not active (active non-node users are not nodes)
    queryset.filter(is_active=False).update(is_node=True)

@admin.action(description='Activate selected node(s)')
def activate_node(modeladmin, request, queryset):
    # Only set nodes as active if they are nodes
    queryset.filter(is_node=True).update(is_active=True)

@admin.action(description='Deactivate selected node(s)')
def deactivate_node(modeladmin, request, queryset):
    # Only set inactive if they are nodes
    queryset.filter(is_node=True).update(is_active=False)

# more detailed user admin
# can filter on is_active
class UserAdmin(admin.ModelAdmin):
    '''
    ### UserAdmin class
    - Custom admin class for the User model.
    - Adds a custom action to approve users (set is_active to True)
    - Allows filtering by active users and admin users.
    - Allows searching by username and email.
    - Orders users by date joined.
    '''
    list_display = ('id', 'displayName', 'is_active', 'is_remote', 'host', 'is_staff', 'date_joined', 'is_node', 'url', 'github', )
    list_filter = ('is_active', 'is_staff', 'is_node', 'is_remote')
    search_fields = ('username', 'email')
    ordering = ('-date_joined',)
    actions = [
        approve_users,  # custom action to approve users
        set_as_node,    # custom action to set user as a remote node
        activate_node,  # custom action to activate a remote node
        deactivate_node # custom action to deactivate a remote node
    ]

# register the models
admin.site.register(user_models.User, UserAdmin)
