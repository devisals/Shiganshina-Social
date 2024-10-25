from . import models 
from rest_framework import serializers
import os
import util.main as util

class UserSerializer(serializers.HyperlinkedModelSerializer):
    '''
    ### UserSerializer class
    Serializes the User model.
    '''
    url = serializers.SerializerMethodField()

    class Meta:
        model = models.User
        fields = ['id', 'displayName', 'github', 'url', 'host', 'profileImage']


    def get_url(self, obj):
        if "http://" in obj.id or "https://" in obj.id:
            return obj.id

        if 'snack' in obj.host:
            return util.standardize_url(f"{obj.host.rstrip('/')}/api/authors/{obj.id}")
        
        return util.standardize_url(f"{obj.host.rstrip('/')}/authors/{obj.id}")


    def to_representation(self, instance):
        '''
        Converts a User model to a dictionary representation
        '''
        return {
            'type': 'author',
            'id': f"{instance.host.rstrip('/')}/authors/{instance.id}",
            'host': instance.host,
            'displayName': instance.displayName,
            'url': self.get_url(instance),
            'github': instance.github,
            'profileImage': instance.profileImage
        }
