from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _
import os
import urllib.parse

class CustomUserManager(BaseUserManager):
    """
    Custom user model manager where DisplayName is the unique identifier
    for authentication instead of usernames.
    """
    def create_node(self, displayName, password, url):
        """
        Create and save a node with the given displayName and password.
        """
        if not displayName:
            raise ValueError(_("The display name must be set"))
        
        userNode = self.create_user(displayName, password, "https://github.com/yyx990803", "https://github.com/yyx990803.png")

        userNode.is_node = True
        userNode.url = url
        userNode.save()

    def create_user(self, displayName, password, github, profileImage, **extra_fields):
        """
        Create and save a user with the given displayName and password.
        """
        if not displayName:
            raise ValueError(_("The display name must be set"))
        if profileImage is None:
            profileImage = github.rstrip('/') + ".png"
        user = self.model(displayName=displayName, github=github, profileImage=profileImage, **extra_fields)
        user.set_password(password)
        user.is_node = False
        user.save()

        # get the HOST_URL environment variable
        host = os.environ.get('HOST_API_URL')
        if host is None:
            raise ValueError(_("HOST_API_URL environment variable must be set"))
        host = urllib.parse.urlparse(host).geturl()
        user.host = host
        user.url = urllib.parse.urljoin(host, f'authors/{user.id}')
        user.save() # save again

        return user

    def create_admin(self, displayName, password, github, profileImage, **extra_fields):
        """
        Create and save a SuperUser with the given displayName and password.
        """
        # is_staff is a built-in way to check if a user is an admin
        extra_fields.setdefault("is_staff", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Admin must have is_staff=True."))
        return self.create_user(displayName, password, github, profileImage, **extra_fields)

    def create_superuser(self, displayName, password, github, **extra_fields):
        """
        Create and save a SuperUser with the given displayName and password.
        (for CLI stuff).
        """
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))

        print('Creating superuser with: ', displayName, password, github, extra_fields)
        
        self.create_admin(displayName, password, github, None, **extra_fields)
