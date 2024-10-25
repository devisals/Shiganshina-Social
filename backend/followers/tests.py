from django.test import TestCase, LiveServerTestCase
from followers import models, serializers
import urllib
import base64
import os
from util.tests import LiveServerThreadWithReuse
from remote_node.models import RemoteNode
from util.main import standardize_url
from restapi.models import User
import json

# Create your tests here.

class FollowerTestCase(LiveServerTestCase):
    port = 8000
    server_thread_class = LiveServerThreadWithReuse

    def setUp(self):
        self.user1 = models.User.objects.create_user(
            displayName='Test User 1',
            password='testuser1',
            github='https://github.com/uofa-cmput404',
            profileImage=None,
            is_active=True,
            is_node=False,
        )
        self.user1.save()
        self.user2 = models.User.objects.create_user(
            displayName='Test User 2',
            password='testuser2',
            github='https://github.com/uofa-cmput404',
            profileImage=None,
            is_active=True,
            is_node=False,
        )
        self.user2.save()

        # add both remoteNode and userNode so our tests can communicate with itself
        RemoteNode.objects.create(
            nodeName="test",
            url=f"http://localhost:8000/api/",
            displayName='local',
            password='testnode'
        )
        User.objects.create_node(
            displayName='local',
            url='http://localhost:8000/api/',
            password='testnode',
        )
    
    def test_add_follower_unauthenticated(self):
        # make user1 follow user2
        response = self.client.put(
            f'/api/authors/{self.user2.id}/followers/{self.user1.url}/'
        )
        self.assertEqual(response.status_code, 403)

    def test_add_follower(self):
        # get URL of user
        user1_data = self.client.get(f'/api/authors/{self.user1.id}')
        self.assertEqual(user1_data.status_code, 200)
        user1_data = user1_data.json()
        user1_url = urllib.parse.quote(user1_data['url'], safe='')
        print("User 1 URL:", user1_url)
        # make user1 follow user2
        auth_token = f'Basic {base64.b64encode(b'Test User 2:testuser2').decode('ascii')}'
        print('PUT')
        response = self.client.put(
            f'/api/authors/{self.user2.id}/followers/{user1_url}',
            headers={'Authorization': auth_token}
        )
        self.assertEqual(response.status_code, 201)

        # look through the followers of user2
        followers = models.Follower.objects.filter(object=self.user2)
        self.assertEqual(len(followers), 1)
        follower = followers[0]
        self.assertEqual(
            standardize_url(follower.actor.url),
            standardize_url(user1_data['url'])
        )

    def test_get_followers(self):
        user1_followers = self.client.get(f'/api/authors/{self.user1.id}/followers')
        self.assertEqual(user1_followers.status_code, 200)
        user1_followers = user1_followers.json()
        self.assertEqual(user1_followers['type'], 'followers')
        self.assertEqual(len(user1_followers['items']), 0)
    
    def test_get_nonfollower(self):
        user2_url = urllib.parse.quote(self.user2.url, safe='')
        user1_follower = self.client.get(f'/api/authors/{self.user1.id}/followers/{user2_url}')
        self.assertEqual(user1_follower.status_code, 404)

    def test_delete_follower(self):
        # get URL of user
        user1_data = self.client.get(f'/api/authors/{self.user1.id}')
        self.assertEqual(user1_data.status_code, 200)
        user1_data = user1_data.json()
        user1_url = urllib.parse.quote(user1_data['url'], safe='')
        print("User 1 URL:", user1_url)

        # make user1 follow user2
        auth_token = f'Basic {base64.b64encode(b'Test User 2:testuser2').decode('ascii')}'
        response = self.client.put(
            f'/api/authors/{self.user2.id}/followers/{user1_url}',
            headers={'Authorization': auth_token}
        )
        self.assertEqual(response.status_code, 201)

        # look through the followers of user2
        followers = models.Follower.objects.filter(object=self.user2)
        self.assertEqual(len(followers), 1)
        follower = followers[0]
        self.assertEqual(
            standardize_url(follower.actor.url), 
            standardize_url(user1_data['url'])
        )
        print('[TESTS] Deleting follower')

        # delete the follower
        # NOTE: deleting a follower does not need authentication
        response = self.client.delete(
            f'/api/authors/{self.user2.id}/followers/{user1_url}',
        )

        # look through the followers of user2
        self.assertEqual(response.status_code, 204)
        followers = models.Follower.objects.filter(object=self.user2)
        self.assertEqual(len(followers), 0)
    
    def test_get_individual_follower(self):
        # make user 1 follow user 2
        models.Follower.objects.create(
            object=self.user2,
            actor=self.user1
        )

        # get the follower
        user1_url = urllib.parse.quote(self.user1.url, safe='')
        follower_response = self.client.get(f'/api/authors/{self.user2.id}/followers/{user1_url}')
        self.assertEqual(follower_response.status_code, 200)

        follower_data = follower_response.json()
        self.assertEqual(follower_data['type'], 'follower')
        self.assertEqual(follower_data['actor']['displayName'], self.user1.displayName)
        self.assertEqual(follower_data['object']['displayName'], self.user2.displayName)
    
    def test_get_individual_follower_nonexistent(self):
        # get the follower
        user1_url = urllib.parse.quote(self.user1.url, safe='')
        follower_response = self.client.get(f'/api/authors/{self.user2.id}/followers/{user1_url}')
        self.assertEqual(follower_response.status_code, 404)

