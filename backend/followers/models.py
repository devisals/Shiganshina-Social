from django.db import models
from restapi.models import User 
import requests

# Create your models here.

class Follower(models.Model):
    '''
    Stores info about someone following someone in our server.
    '''
    # person who is being followed
    object = models.ForeignKey(User, on_delete=models.CASCADE)

    # person who is following
    # although this may be a user from another server, we make a copy so this is still a ForeignKey
    actor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='actor')


    def __str__(self):
        # foreign_author = requests.get(self.actor).json()
        return f"{self.actor} follows {self.object}"
