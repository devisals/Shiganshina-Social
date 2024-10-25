from django.test import TestCase
import json
from rest_framework import status
from . import models
from remote_node.models import RemoteNode
from restapi.models import User
import util.main as util

# Create your tests here.

class RegisterAuthorTest(TestCase):
    '''
    Tests registering an author

    Note that we need ALL data to register
    '''
    def setUp(self):
        self.valid_payload_noimg = {
            "displayName": "Test User 1",
            "password": "testpassword1",
            "github": "https://github.com/joshuanianji",
        }

        self.valid_payload = {
            "displayName": "Test User 1",
            "password": "testpassword1",
            "github": "https://github.com/joshuanianji",
            "profileImage": "https://github.com/joshuanianji.png"
        }

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
    
    def test_register_author(self):
        response = self.client.post(
            '/api/auth',
            data=json.dumps(self.valid_payload_noimg),
            content_type='application/json'
        )
        user_id = response.data['id']
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['displayName'], 'Test User 1')
        self.assertEqual(response.data['url'], f'{user_id}')

        # get user from database, check that it's inactive
        user = models.User.objects.get(pk=util.id_from_url(user_id))
        self.assertFalse(user.is_active)
    
    def test_register_author_with_image(self):
        response = self.client.post(
            '/api/auth',
            data=json.dumps(self.valid_payload),
            content_type='application/json'
        )
        user_id = response.data['id']
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['displayName'], 'Test User 1')
        self.assertEqual(response.data['url'], f'{user_id}')
        self.assertEqual(response.data['profileImage'], 'https://github.com/joshuanianji.png')

        user = models.User.objects.get(pk=util.id_from_url(user_id))
        self.assertFalse(user.is_active)
    
    def test_register_author_no_data(self):
        response = self.client.post(
            '/api/auth',
            data=json.dumps({}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
        
    def test_registered_user_cannot_login(self):
        '''
        If a user just registered, they must be approved by an admin before they can login
        '''
        response_register = self.client.post(
            '/api/auth',
            data=json.dumps(self.valid_payload_noimg),
            content_type='application/json'
        )

        response_login = self.client.get(
            '/api/auth',
            content_type='application/json',
            headers={'HTTP_AUTHORIZATION': 'Basic "Test User 1:testpassword1"'}
        )
        self.assertEqual(response_login.status_code, status.HTTP_401_UNAUTHORIZED)

class AuthorURLTests(TestCase):
    '''
    Tests for the author URL
    '''
    def setUp(self):
        self.valid_payload_noimg = {
            "displayName": "Test User 1",
            "password": "testpassword1",
            "github": "https://github.com/joshuanianji",
        }

        self.valid_payload = {
            "displayName": "Test User 1",
            "password": "testpassword1",
            "github": "https://github.com/joshuanianji",
            "profileImage": "https://github.com/joshuanianji.png"
        }

        # create a remoteNode user
        self.user1 = User.objects.create_user(
            displayName='Test User 1',
            password='testuser1',
            github='https://github.com/uofa-cmput404',
            profileImage=None
        )
        self.user1.save()

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
    
    def test_get_authors(self):
        '''
        Should not return the node object
        '''
        response = self.client.get(
            '/api/authors',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['type'], 'authors')
        self.assertEqual(len(response.data['items']), 1)

        items = response.data['items']
        self.assertEqual(items[0]['displayName'], 'Test User 1')
    
    def test_get_authors_all(self):
        response = self.client.get(
            '/api/authors?all',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['type'], 'authors')
        self.assertEqual(len(response.data['items']), 1)

        items = response.data['items']
        self.assertEqual(items[0]['displayName'], 'Test User 1')

    def test_get_author(self):
        response = self.client.get(
            f'/api/authors/{self.user1.id}',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['type'], 'author')
        self.assertEqual(response.data['displayName'], 'Test User 1')

    def test_get_author_all(self):
        '''
        ?all shouldn't change the output
        '''
        response = self.client.get(
            f'/api/authors/{self.user1.id}?all',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['type'], 'author')
        self.assertEqual(response.data['displayName'], 'Test User 1')

    def test_get_author_404(self):
        response = self.client.get(
            f'/api/authors/999',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_author_404_all(self):
        response = self.client.get(
            f'/api/authors/999?all',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
