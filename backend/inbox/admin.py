from django.contrib import admin
from inbox import models

# Register your models here.

admin.site.register(models.FollowRequest)
admin.site.register(models.InboxComment)
admin.site.register(models.InboxPost)

