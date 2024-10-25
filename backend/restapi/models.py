from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from .user_manager import CustomUserManager
import uuid

def string_uuid():
    return str(uuid.uuid4())

# Use Django's User model under the hood, but extend it to include additional fields
# https://testdriven.io/blog/django-custom-user-model/
class User(AbstractUser):
    '''
    ### User class
    All fields have max_length=250. Username (displayName) must be unique.
    Creates a User model with the following fields:
        - displayName: The author's displayed name and username (required)
        - github: A URL to the author's GitHub profile (required)
        - url: A URL to the author's profile
        - host: A URL to the author's home host
        - profileImage: A URL to the author's profile image, can be null
    Managed by the CustomUserManager, which creates regular users and admins.
    '''
    # making sure the username field is not used
    username = None

    # overriding ID field to be a charfield
    # for us, it is a UUID, but if it's from another node, it's a URL
    id = models.CharField(max_length=250, unique=True, help_text="the ID of the user", default=string_uuid, primary_key=True, editable=False)
    # custom fields
    displayName = models.CharField(max_length=250, unique=True, help_text="the author's display name")
    github = models.URLField(max_length=250)
    url = models.URLField(max_length=250, help_text="url to the author's profile")
    host = models.URLField(max_length=250, help_text="the home host of the author")
    # nullable profile image
    profileImage = models.URLField(max_length=250, help_text="url to the author's profile image", null=True, blank=True)

    # isNode is a boolean field that is true if the user is a remote node.
    # This is used for remote authentication of remote API requests.
    is_node = models.BooleanField(default=False)

    # isRemoteUser is a boolean field that is true if the user is copied from a remote node
    is_remote = models.BooleanField(default=False)

    USERNAME_FIELD = 'displayName'
    REQUIRED_FIELDS = ['github']

    objects = CustomUserManager()

    def __str__(self):
        return self.displayName