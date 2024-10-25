from typing import Any
from django.db import models
from django.dispatch import receiver
from django.db.models.signals import pre_save
from restapi.models import User
import uuid
import base64

# Create a ForeignKey for Like that us a union of Post and Comment
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType

class Post(models.Model):
    '''
    ### POST MODEL
    The Post model represesnts a single post on the network.
    When the user is deleted, all posts made by the user are also deleted
    Fields:
        - type (str): The type of the activity (e.g. Like, Comment, etc.)
        - author (int): The user id of the author of the post.
        - title (str): The title of the post.
        - source (str): A URL of the source of the post.
        - origin (str): A URL of the origin of the post.
        - description (str): A short description of the post.
        - count (int): The number of comments on the post.
        - content (str): The content of the post.
        - contentType (str): The content type of the post.
                            This can be one of Plain Text, Markdown, Application, PNG/JPEG Image, or GIF Image
        - published (datetime): The date and time the post was published
        - visibility (str): The visibility of the post, one of PUBLIC, FRIENDS, or UNLISTED
        - URL (str): The URL of the post
    '''
    
    # overriding ID field to be a charfield
    # for us, it is a UUID, but if it's from another node, it's a URL
    id = models.CharField(max_length=250, unique=True, help_text="the ID of the user", default=uuid.uuid4, primary_key=True, editable=False)
    
    type = models.CharField(max_length=4, default="post", editable=False)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=250)
    source = models.URLField(max_length=250, help_text="The original source of the post")
    origin = models.URLField(max_length=250, help_text="The origin of the post")
    description = models.CharField(max_length=500)
    count = models.IntegerField(default=0, help_text="The number of comments on the post")
    content = models.TextField()
    CONTENT_TYPES = [
        ('text/plain', 'Plain Text'),
        ('text/markdown', 'Markdown'),
        ('application/base64', 'Base64 Application'),
        ('image/png;base64', 'Base64 PNG Image'),
        ('image/jpeg;base64', 'Base64 JPEG Image'),
        ('image/gif;base64', 'Base64 GIF Image'),
    ]
    contentType = models.CharField(max_length=250, choices=CONTENT_TYPES, default='text/plain', help_text="Content type of the post")
    published = models.DateTimeField(auto_now_add=True)
    VISIBILITIES = [
        ('PUBLIC', 'Public'),
        ('FRIENDS', 'Friends'),
        ('UNLISTED', 'Unlisted'),
    ]
    visibility = models.CharField(max_length=250, choices=VISIBILITIES, default='PUBLIC', help_text="Visibility of the post")
    isGithub = models.BooleanField(default=False, help_text="Is this post from Github?")

    @property
    def url(self):
        return f"{self.author.url}/posts/{self.id}"

    def __str__(self):
        return self.title

    def image_to_base64(self):
        '''
        This method converts an image to base64
        '''
        if self.contentType in ['image/png;base64', 'image/jpeg;base64', 'image/gif;base64']:
            with open(self.content, "rb") as image_file:
                self.content = base64.b64encode(image_file.read()).decode('utf-8')
        super().save()

        
        
        
        
  

### COMMENT MODEL

class Comment(models.Model):
    '''
    ### COMMENT MODEL
    The Comment model represents a comment on a post.
    When the user or post is deleted, all comments made by the user, or all comments on the post are deleted too
    Fields:
        - type (str): The type of the activity (e.g. Like, Comment, etc.)
        - post (int): The post being commented on
        - author (int): The user who made the comment
        - comment (str): The content of the comment
        - url (str): The URL of the comment (default is <post_url>/comments/<comment_id>)
        - published (datetime): The date and time the comment was made
        - contentType (str): The content type of the comment.
                             This can be one of Plain Text, Markdown, Application, PNG/JPEG Image, or GIF Image
    '''
    # overriding ID field to be a charfield
    # for us, it is a UUID, but if it's from another node, it's a URL
    id = models.CharField(max_length=250, unique=True, help_text="the ID of the user", default=uuid.uuid4, primary_key=True, editable=False)

    type = models.CharField(max_length=7, default="comment", editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments', help_text="The post being commented on")
    author = models.ForeignKey(User, on_delete=models.CASCADE, help_text="The user who made the comment")
    comment = models.TextField(help_text="The content of the comment")
    published = models.DateTimeField(auto_now_add=True)
    CONTENT_TYPES = [
        ('text/plain', 'Plain Text'),
        ('text/markdown', 'Markdown'),
        ('application/base64', 'Base64 Application'),
        ('image/png;base64', 'Base64 PNG Image'),
        ('image/jpeg;base64', 'Base64 JPEG Image'),
        ('image/gif;base64', 'Base64 GIF Image'),
    ]
    contentType = models.CharField(max_length=250, choices=CONTENT_TYPES, default='text/plain', help_text="Content type of the comment")

    @property
    def url(self):
        return f"{self.post.url}/comments/{self.id}"

    def __str__(self):
        return f"Comment by {self.author} on {self.post}"



### LIKE MODEL
class Like(models.Model):
    '''
    ### LIKE MODEL
    The Like model represents a like on a post.
    When the user or post is deleted, all likes made by the user, or all likes on the post are deleted too.
    Fields:
        - author (int): The user who liked the post
        - object (int): The post being liked
        - published (datetime): The date and time the like was made
    '''

    class Meta:
        indexes = [
            models.Index(fields=['author', 'object']),
        ]

    published = models.DateTimeField(auto_now_add=True)
    author = models.URLField(help_text="The user URL ID who liked the post")
    object = models.URLField(help_text="The URL ID of the object being liked")

