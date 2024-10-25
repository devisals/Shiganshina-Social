from rest_framework import serializers
from . import models
from restapi.serializers import UserSerializer

class FollowerSerializer(serializers.ModelSerializer):
    '''
    ### FOLLOWER SERIALIZER

    Serializes a follower info
    '''
    object = UserSerializer(read_only=True)

    class Meta:
        model = models.Follower
        fields = ['id', 'actor', 'object']
