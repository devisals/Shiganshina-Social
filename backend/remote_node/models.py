from django.db import models

# Create your models here.
class RemoteNode(models.Model):
    '''
    A remote node we need to connect to
    '''
    nodeName = models.CharField(max_length=250, unique=True, help_text="the name of the remote node")
    displayName = models.CharField(max_length=250, unique=True, help_text="the author's display name", blank=True, null=True)
    url = models.URLField(max_length=250, help_text="url to the author's profile")
    password = models.CharField(max_length=250, help_text="password to the remote node", blank=True, null=True)
    disabled = models.BooleanField(help_text="whether the remote node is disabled", default=False)