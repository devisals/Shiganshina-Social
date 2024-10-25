from django.contrib import admin

# Register your models here.

from .models import Comment, Post, Like


class PostAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'author',
        'title',
        'description',
        'content',
        'contentType',
        'published',
        'visibility',
        'source',
        'origin',
        'count',
        'url',
    ]


class CommentAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'author',
        'post',
        'comment',
        'url',
        'published',
    ]

class LikeAdmin(admin.ModelAdmin):
    list_display = [
        'author',
        'object',
        'published',
    ]

admin.site.register(Comment, CommentAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Like, LikeAdmin)


