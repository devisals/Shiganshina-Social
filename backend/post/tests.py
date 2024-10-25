from time import sleep
from django.test import TestCase, LiveServerTestCase
from remote_node.models import RemoteNode
from post import models, serializers
import urllib
import base64
import os
import util
from util.tests import LiveServerThreadWithReuse
import util.main as util
from restapi.models import User
from rest_framework import status
import json

# Create your tests here.
class PostTestCase(LiveServerTestCase):
    port = 8000
    server_thread_class = LiveServerThreadWithReuse

    def setUp(self):
        self.user1 = models.User.objects.create_user(
            displayName='Test User 1',
            password='testuser1',
            github='https://github.com/uofa-cmput404',
            profileImage=None
        )
        self.user1.save()
        self.user2 = models.User.objects.create_user(
            displayName='Test User 2',
            password='testuser2',
            github='https://github.com/uofa-cmput404',
            profileImage=None
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

    def test_create_post(self):
        """
        Creating a PUBLIC post and checking if it is visible to the other user
        """
        auth_token = f'Basic {base64.b64encode(b"Test User 1:testuser1").decode("ascii")}'
        print("User ID:", self.user1.id)
        response = self.client.post(
            f'/api/authors/{self.user1.id}/posts',
            {
                "title": "Test Post validate data",
                "source": "https://example.com",
                "origin": "https://example.com",
                "description": "Test Description",
                "content": "Test Content",
                "contentType": "text/plain",
                "visibility": "PUBLIC"
            },
            content_type='application/json',
            HTTP_AUTHORIZATION=auth_token
        )
        self.assertEqual(response.status_code, 201)
        
        # now check if post is visible to the other user
        post_id = response.json()['id'].split('posts')[1][1:]
        auth_token = f'Basic {base64.b64encode(b"local:testnode").decode("ascii")}'
        response = self.client.get(f'/api/authors/{self.user1.id}/posts/{post_id}', HTTP_AUTHORIZATION=auth_token)
        self.assertEqual(response.status_code, 200)
    
    def test_list_post(self):
        """
        Listing all posts of a user
        """
        auth_token = f'Basic {base64.b64encode(b"Test User 1:testuser1").decode("ascii")}'
        response = self.client.get(
            f'/api/authors/{self.user1.id}/posts',
            HTTP_AUTHORIZATION=auth_token
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['items']), 0)
    
    def test_list_post_paged_otheruser(self):
        """
        Listing all posts of a user with pagination

        Use auth of another user
        """
        auth_token = f'Basic {base64.b64encode(b"Test User 2:testuser2").decode("ascii")}'
        response = self.client.get(
            f'/api/authors/{self.user1.id}/posts?page=1&size=5',
            HTTP_AUTHORIZATION=auth_token
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['items']), 0)

    def test_correct_post(self):
        """
        Checking if the user can correct a typo in the post
        """
        auth_token = f'Basic {base64.b64encode(b"Test User 1:testuser1").decode("ascii")}'
        response = self.client.post(
            f'/api/authors/{self.user1.id}/posts',
            {
                "title": "Test Post",
                "source": f"http://localhost:{self.port}/api/authors/{self.user1.id}/posts/",
                "origin": f"http://localhost:{self.port}/api/authors/{self.user1.id}/posts/",
                "description": "This is a test post",
                "contentType": "text/plain",
                "content": "This is a test post with an reor",
                "visibility": "PUBLIC"
            },
            content_type='application/json',
            HTTP_AUTHORIZATION=auth_token
        )
        self.assertEqual(response.status_code, 201)
        post_url = util.standardize_url(response.json()['id'])
        print("Post ID:", post_url)
        # now check if "error" is in the post
        response = self.client.get(post_url, HTTP_AUTHORIZATION=f'Basic {base64.b64encode(b"local:testnode").decode("ascii")}')
        print(response.json())
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("error", response.content.decode('utf-8'))

        #edit the post
        response = self.client.put(
            post_url,
            {
                "title": "Test Post",
                "source": f"http://localhost:{self.port}/api/authors/{self.user1.id}/posts/",
                "origin": f"http://localhost:{self.port}/api/authors/{self.user1.id}/posts/",
                "description": "This is a test post",
                "contentType": "text/plain",
                "content": "This is a test post with an error",
                "visibility": "PUBLIC"
            },
            content_type='application/json',
            HTTP_AUTHORIZATION=auth_token
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("error", response.content.decode('utf-8'))

    def test_delete_post(self):
        """
        Deleting a post
        """
        auth_token = f'Basic {base64.b64encode(b"Test User 1:testuser1").decode("ascii")}'
        response = self.client.post(
            f'/api/authors/{self.user1.id}/posts',
            {
                "title": "Test Post validate data",
                "source": "https://example.com",
                "origin": "https://example.com",
                "description": "Test Description",
                "content": "Test Content",
                "contentType": "text/plain",
                "visibility": "PUBLIC"
            },
            content_type='application/json',
            HTTP_AUTHORIZATION=auth_token
        )
        self.assertEqual(response.status_code, 201)

        post_id = util.standardize_url(response.json()['id'])
        print('[PostTestCase.test_delete_post] Deleting post:', post_id)
        response = self.client.delete(
            post_id,
            HTTP_AUTHORIZATION=auth_token
        )
        self.assertEqual(response.status_code, 204)

    def test_create_unlisted_post(self):
        """
        Creating an UNLISTED post
        """
        auth_token = f'Basic {base64.b64encode(b"Test User 1:testuser1").decode("ascii")}'
        response = self.client.post(
            f'/api/authors/{self.user1.id}/posts',
            {
                "title": "Test Post",
                "source": f"http://localhost:{self.port}/api/authors/{self.user1.id}/posts",
                "origin": f"http://localhost:{self.port}/api/authors/{self.user1.id}/posts",
                "description": "This is a test post",
                "contentType": "text/plain",
                "content": "This is a test post",
                "visibility": "UNLISTED"
            },
            content_type='application/json',
            HTTP_AUTHORIZATION=auth_token
        )
        self.assertEqual(response.status_code, 201)
        post_id = util.standardize_url(response.json()['id'])

        # post should be visisble to users if they have the link
        auth_token = f'Basic {base64.b64encode(b"Test User 2:testuser2").decode("ascii")}'
        print(f'[PostTestCase.test_create_unlisted_post] Checking if post is visible to user 2')
        post_id = post_id.split('posts')[1][1:]
        print(f'[PostTestCase.test_create_unlisted_post] Post ID: {post_id}')
        response = self.client.get(f'/api/authors/{self.user1.id}/posts/{post_id}', HTTP_AUTHORIZATION=auth_token)
        # response = self.client.get(post_id, HTTP_AUTHORIZATION=auth_token)
        self.assertEqual(response.status_code, 200)
    
    def test_make_comment(self):
        """
        Creating a comment on a post
        """
        auth_token = f'Basic {base64.b64encode(b"Test User 1:testuser1").decode("ascii")}'
        response = self.client.post(
            f'/api/authors/{self.user1.id}/posts',
            {
                "title": "Test Post",
                "source": f"http://localhost:{self.port}/api/authors/{self.user1.id}/posts",
                "origin": f"http://localhost:{self.port}/api/authors/{self.user1.id}/posts",
                "description": "This is a test post",
                "contentType": "text/plain",
                "content": "This is a test post",
                "visibility": "PUBLIC"
            },
            content_type='application/json',
            HTTP_AUTHORIZATION=auth_token
        )
        self.assertEqual(response.status_code, 201)
        post_id = response.json()['id']
        auth_token = f'Basic {base64.b64encode(b"Test User 2:testuser2").decode("ascii")}'
        print('[PostTestCase.test_make_comment] Making a comment on post:', post_id)
        response = self.client.post(
            f'{post_id}/comments',
            {
                "comment": "This is a test comment"
            },
            content_type='application/json',
            HTTP_AUTHORIZATION=auth_token
        )
        print(response)

        self.assertEqual(response.status_code, 201)
        comment_content = response.json()['comment']
        self.assertEqual(comment_content, "This is a test comment")
    
    def test_like_post(self):
        """
        Liking a post
        """
        auth_token = f'Basic {base64.b64encode(b"Test User 1:testuser1").decode("ascii")}'
        response = self.client.post(
            f'/api/authors/{self.user1.id}/posts',
            {
                "title": "Test Post",
                "source": f"http://localhost:{self.port}/api/authors/{self.user1.id}/posts",
                "origin": f"http://localhost:{self.port}/api/authors/{self.user1.id}/posts",
                "description": "This is a test post",
                "contentType": "text/plain",
                "content": "This is a test post",
                "visibility": "PUBLIC"
            },
            content_type='application/json',
            HTTP_AUTHORIZATION=auth_token
        )

        post_id = response.json()['id']
        auth_token = f'Basic {base64.b64encode(b"Test User 2:testuser2").decode("ascii")}'
        like_object = {
            "type": "like",
            "author": {
                "id": self.user2.id,
                "host": f"http://localhost:{self.port}",
                "displayName": "Test User 2",
                "url": f"http://localhost:{self.port}/api/authors/{self.user2.id}",
                "github": "https://github.com/cmput415-2023/"
            },
            "object": f"http://localhost:{self.port}/api/authors/{self.user1.id}/posts/{post_id}"
        }
        response = self.client.post(
            f'/api/authors/{self.user1.id}/inbox',
            {
                "type": "inbox",
                "author": f'http://localhost:8000/api/authors/{self.user1.id}',
                "items": [like_object]
            },
            content_type='application/json',
            HTTP_AUTHORIZATION=auth_token
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['type'], "like")
    
    def test_check_number_of_likes(self):
        """
        Checking the number of likes on a post
        """
        auth_token = f'Basic {base64.b64encode(b"Test User 1:testuser1").decode("ascii")}'
        response = self.client.post(
            f'/api/authors/{self.user1.id}/posts',
            {
                "title": "Test Post",
                "source": f"http://localhost:{self.port}/api/authors/{self.user1.id}/posts",
                "origin": f"http://localhost:{self.port}/api/authors/{self.user1.id}/posts",
                "description": "This is a test post",
                "contentType": "text/plain",
                "content": "This is a test post",
                "visibility": "PUBLIC"
            },
            content_type='application/json',
            HTTP_AUTHORIZATION=auth_token
        )

        post_id = response.json()['id']
        auth_token = f'Basic {base64.b64encode(b"Test User 2:testuser2").decode("ascii")}'
        like_object = {
            "type": "like",
            "summary": f"Test User 2 liked your post",
            "author": {
                "id": self.user2.url,
                "host": f"http://localhost:{self.port}/",
                "displayName": "Test User 2",
                "url": f"http://localhost:{self.port}/api/authors/{self.user2.id}",
                "github": "https://github.com/cmput415-2023/"
            },
            "object": post_id
        }
        response = self.client.post(
            f'/api/authors/{self.user1.id}/inbox',
            {
                "type": "inbox",
                "author": f'http://localhost:8000/api/authors/{self.user1.id}',
                "items": [like_object]
            },
            content_type='application/json',
            HTTP_AUTHORIZATION=auth_token
        )

        self.assertEqual(response.status_code, 201)
        print(f'[PostTestCase.test_check_number_of_likes] Checking number of likes on url "{post_id}/likes"')
        response = self.client.get(f'{post_id}/likes')
        self.assertEqual(response.status_code, 200)
        # to count the number of likes, we count the number of items in the response
        self.assertEqual(len(response.json()['items']), 1)

    def test_comments_on_friends_post_viewed_by_friends(self):
        """
        Viewing comments on a friend's post
        """
        auth_token = f'Basic {base64.b64encode(b"Test User 1:testuser1").decode("ascii")}'
        response = self.client.post(
            f'/api/authors/{self.user1.id}/posts',
            {
                "title": "Test Post",
                "source": f"http://localhost:{self.port}/api/authors/{self.user1.id}/posts",
                "origin": f"http://localhost:{self.port}/api/authors/{self.user1.id}/posts",
                "description": "This is a test post",
                "contentType": "text/plain",
                "content": "This is a test post",
                "visibility": "FRIENDS"
            },
            content_type='application/json',
            HTTP_AUTHORIZATION=auth_token
        )
        self.assertEqual(response.status_code, 201)

        post_id = response.json()['id']

        # make user2 follow user1
        user2_data = self.client.get(f'/api/authors/{self.user2.id}')
        self.assertEqual(user2_data.status_code, 200)
        user2_data = user2_data.json()
        user2_url = urllib.parse.quote(user2_data['url'], safe='')
        print("> User 2 URL:", user2_url)
        response = self.client.put(
            f'/api/authors/{self.user1.id}/followers/{user2_url}',
            HTTP_AUTHORIZATION=auth_token
        )
        self.assertEqual(response.status_code, 201)

        # make user1 follow user2
        auth_token = f'Basic {base64.b64encode(b"Test User 2:testuser2").decode("ascii")}'
        user1_data = self.client.get(f'/api/authors/{self.user1.id}')
        self.assertEqual(user1_data.status_code, 200)
        user1_data = user1_data.json()
        user1_url = urllib.parse.quote(user1_data['url'], safe='')
        print("> User 1 URL:", user1_url)
        response = self.client.put(
            f'/api/authors/{self.user2.id}/followers/{user1_url}',
            HTTP_AUTHORIZATION=auth_token
        )
        self.assertEqual(response.status_code, 201)

        print("User 1 and User 2 are now friends")

        # now user2 should be able to comment on user1's post
        response = self.client.post(
            f'{post_id}/comments',
            {
                "comment": "This is a test comment"
            },
            HTTP_AUTHORIZATION=auth_token
        )
        
        self.assertEqual(response.status_code, 201)
        comment_content = response.json()['comment']
        self.assertEqual(comment_content, "This is a test comment")

        # make a user3 who is not following user1
        self.user3 = models.User.objects.create_user(
            displayName='Test User 3',
            password='testuser3',
            github='www.github.com',
            profileImage=None
        )
        self.user3.save()

        # now user3 should not be able to comment on user1's post
        auth_token = f'Basic {base64.b64encode(b"Test User 3:testuser3").decode("ascii")}'
        response = self.client.post(
            f'{post_id}/comments',
            {
                "comment": "This is a test comment"
            },
            content_type='application/json',
            HTTP_AUTHORIZATION=auth_token
        )
        self.assertEqual(response.status_code, 401)


class CommentTestCase(LiveServerTestCase):
    port = 8000
    server_thread_class = LiveServerThreadWithReuse

    def setUp(self):
        self.user1 = models.User.objects.create_user(
            displayName='Test User 1',
            password='testuser1',
            github='https://github.com/uofa-cmput404',
            profileImage=None
        )
        self.user1.save()
        self.user2 = models.User.objects.create_user(
            displayName='Test User 2',
            password='testuser2',
            github='https://github.com/uofa-cmput404',
            profileImage=None
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
    
    def _make_post(self, user, password, visibility):
        '''
        Helper function to make a post by a user and visibility. Returns the post data as json
        '''
        print("> User:", user)
        auth_token = f'Basic {base64.b64encode(f"{user}:{password}".encode('ascii')).decode('ascii')}'

        response = self.client.post(
            f'/api/authors/{user.id}/posts',
            data={
                "title":"hi",
                "source":"http://localhost:5173/profile?id=a239fe13-5fc7-45bf-a616-f75a22c7976f",
                "origin":"http://localhost:5173/profile?id=a239fe13-5fc7-45bf-a616-f75a22c7976f",
                "description":"asdas",
                "contentType":"text/plain",
                "content":"asdasd",
                "visibility": visibility
            },
            content_type='application/json',
            HTTP_AUTHORIZATION=auth_token
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        post_data = self.client.get(
            util.standardize_url(response.json()["id"]),
            HTTP_AUTHORIZATION=auth_token
        )
        self.assertEqual(post_data.status_code, status.HTTP_200_OK)
        return post_data.json()

    def test_post_no_comments(self):
        '''
        User 1 makes a post with no comments

        Test that the post returns 200 and has no comments
        '''
        user1_response = self.client.get(f'/api/authors/{self.user1.id}')
        user2_response = self.client.get(f'/api/authors/{self.user2.id}')
        self.assertEqual(user1_response.status_code, status.HTTP_200_OK)
        self.assertEqual(user2_response.status_code, status.HTTP_200_OK)

        post_data = self._make_post(self.user1, 'testuser1', 'PUBLIC')
        post_data_comments_url = post_data.get('comments')
        print(f'[TESTS]: Post data:', json.dumps(post_data, indent=2))

        post_comments = self.client.get(post_data_comments_url, HTTP_AUTHORIZATION=f'Basic {base64.b64encode(b"Test User 1:testuser1").decode("ascii")}')
        self.assertEqual(post_comments.status_code, status.HTTP_200_OK)

    
    def test_comment_adds_to_inbox(self):
        '''
        User 2 comments on User 1's public post

        test that user 1 gets an inbox notification
        '''
        user1_response = self.client.get(f'/api/authors/{self.user1.id}')
        user2_response = self.client.get(f'/api/authors/{self.user2.id}')
        self.assertEqual(user1_response.status_code, status.HTTP_200_OK)
        self.assertEqual(user2_response.status_code, status.HTTP_200_OK)

        post_data = self._make_post(self.user1, 'testuser1', 'PUBLIC')

        make_comment_payload = {
            "type":"comment",
            "author": user2_response.data,
            "comment":"User 2 comments on user 1 post",
            "contentType":"text/markdown",
        }
        post_comment_response = self.client.post(
            post_data.get('comments').rstrip('/'),
            data=json.dumps(make_comment_payload),
            content_type='application/json',
            HTTP_AUTHORIZATION = f'Basic {base64.b64encode(b"Test User 2:testuser2").decode("ascii")}'
        )
        self.assertEqual(post_comment_response.status_code, status.HTTP_201_CREATED)

        # get user1's inbox
        auth_token = f'Basic {base64.b64encode(b"Test User 1:testuser1").decode("ascii")}'
        user1_inbox = self.client.get(
            f'/api/authors/{self.user1.id}/inbox',
            HTTP_AUTHORIZATION=auth_token
        )
        self.assertEqual(user1_inbox.status_code, status.HTTP_200_OK)
        print("> User 1 inbox data:", user1_inbox.data)
        self.assertEqual(user1_inbox.data.get('type'), 'inbox')
        self.assertEqual(len(user1_inbox.data.get('items')), 1)
        self.assertEqual(user1_inbox.data.get('items')[0].get('type'), 'comment')


    def test_comment_on_public_post(self):
        '''
        User 2 comments on User 1's public post

        Test that the comment can be retrieved from the database
        '''
        user1_response = self.client.get(f'/api/authors/{self.user1.id}')
        user2_response = self.client.get(f'/api/authors/{self.user2.id}')
        self.assertEqual(user1_response.status_code, status.HTTP_200_OK)
        self.assertEqual(user2_response.status_code, status.HTTP_200_OK)

        post_data = self._make_post(self.user1, 'testuser1', 'PUBLIC')

        make_comment_payload = {
            "type":"comment",
            "author": user2_response.data,
            "comment":"user 2 comments on user 1 post",
            "contentType":"text/markdown",
        }
        post_comment_response = self.client.post(
            post_data.get('comments').rstrip('/'),
            data=json.dumps(make_comment_payload),
            content_type='application/json',
            HTTP_AUTHORIZATION = f'Basic {base64.b64encode(b"Test User 2:testuser2").decode("ascii")}'
        )
        self.assertEqual(post_comment_response.status_code, status.HTTP_201_CREATED)
        comment_data = post_comment_response.data
        self.assertEqual(post_comment_response.data.get('type'), 'comment')

        print(f'[TESTS]: Comment data:', json.dumps(comment_data, indent=2))
        comment_url = util.standardize_url(comment_data.get('id'))
        # get request to comment_url
        response = self.client.get(comment_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('type'), 'comment')
        self.assertEqual(response.data.get('comment'), 'user 2 comments on user 1 post')
        print(json.dumps(response.data, indent=2))
