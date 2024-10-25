from django.db import models
from restapi.models import User
from post.models import Post, Like, Comment
import requests

class FollowRequest(models.Model):
    '''
    Stores a follow request
    '''
    # person being followed
    object = models.ForeignKey(User, on_delete=models.CASCADE, related_name='follow_request_object')
    # person doing the following
    actor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='follow_request_actor')

    def __str__(self):
        return f"{self.actor.displayName} wants to follow {self.object.displayName}"

class InboxComment(models.Model):
    '''
    The Comment when being sent to an inbox
    '''
    commentUrl = models.URLField(help_text="the URL ID of the comment", editable=False)
    author = models.URLField(help_text="The user who made the comment")


class InboxPost(models.Model):
    '''
    The Post when being sent to an inbox
    '''
    # we just store the ID of the post
    # all other information can be retrieved from this ID
    post_id = models.URLField(help_text="the ID of the post", editable=False)


class Inbox(models.Model):
    '''
    ### INBOX MODEL
    The Inbox model represents a user's inbox.

    An inbox is all the new posts from who you follow, as well as follow requests, likes, and comments you should be aware of
    '''
    # author and published are just for internal use
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    published = models.DateTimeField(auto_now_add=True)

    TYPE = [
        ('POST', 'post'),
        ('LIKE', 'like'),
        ('COMMENT', 'comment'),
        ('FOLLOW', 'follow'),
    ]
    type = models.CharField(max_length=250, choices=TYPE, default='POST', help_text="The type of the notification")

    # the fields below will be non-null depending on the type of the notification
    # this allows us to create a discriminated union type
    # the serialization step will guarantee that only one of these fields is non-null

    # if the type is a post, this field will be non-null
    post = models.ForeignKey(InboxPost, on_delete=models.CASCADE, null=True, blank=True)

    # if the type is a like, this field will be non-null
    like = models.ForeignKey(Like, on_delete=models.CASCADE, null=True, blank=True)

    # if the type is a comment, this field will be non-null
    comment = models.ForeignKey(InboxComment, on_delete=models.CASCADE, null=True, blank=True)

    # if the type is a follow, this field will be non-null
    follow = models.ForeignKey(FollowRequest, on_delete=models.CASCADE, null=True, blank=True)
