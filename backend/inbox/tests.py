from django.test import TestCase, LiveServerTestCase
from inbox import models, serializers
import json
from rest_framework import status
import base64
from util.tests import LiveServerThreadWithReuse
from util.main import standardize_url, url_remove_trailing_slash
from remote_node.models import RemoteNode
from restapi.models import User
import remote_node.util
from unittest.mock import patch 
import inbox.util

# Create your tests here.

class BaseTestCase(LiveServerTestCase):
    port = 8000
    server_thread_class = LiveServerThreadWithReuse

    def setUp(self):
        # make a user
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
    
    def _follow_inbox(self, user1, user2):
        '''
        Make user1 send a follow request to user 2 (adding to user2's inbox)
        Helper function for tests
        '''
        user1_response = self.client.get(f'/api/authors/{user1.id}')
        user2_response = self.client.get(f'/api/authors/{user2.id}')
        self.assertEqual(user1_response.status_code, status.HTTP_200_OK)
        self.assertEqual(user2_response.status_code, status.HTTP_200_OK)

        # the id we get from the user response has the URL, but we need to get the raw id
        # TODO: spec says we should use the URL
        user1_data = user1_response.data | {'id': str(user1.id)}
        user2_data = user2_response.data | {'id': str(user2.id)}
        payload = {
            "type": "inbox",
            "author": f"http://localhost:8000/api/authors/{user1.id}",
            "items": [{
                "type": "follow",
                "summary": f"{user1_data['displayName']} wants to follow {user2_data['displayName']}",
                "actor": user1_data,
                "object": user2_data
            }]
        }
        # print(json.dumps(payload, indent=2))
        # add the post to user2's inbox
        response = self.client.post(
            f'/api/authors/{user2.id}/inbox',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        print(f'Added follow request to User {user2.id}\'s inbox')


class InboxPost(BaseTestCase):
    def test_post_inbox(self):
        '''
        This test contains both post and user from another server
        Thus, we have to make a copy of hte data and store it in our own database
        '''
        # get data for test user 1
        response = self.client.get(f'/api/authors/{self.user1.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user1_data = response.data

        post_payload = {
            "type":"post",
            "title":"A Friendly post title about a post about web dev",
            "description":"This post discusses stuff -- brief",
            "contentType":"text/plain",
            "source": f"http://localhost:{self.port}/",
            "origin": f"http://localhost:{self.port}/",
            "content":"Þā wæs on burgum Bēowulf Scyldinga, lēof lēod-cyning, longe þrāge folcum gefrǣge (fæder ellor hwearf, aldor of earde), oð þæt him eft onwōc hēah Healfdene; hēold þenden lifde, gamol and gūð-rēow, glæde Scyldingas. Þǣm fēower bearn forð-gerīmed in worold wōcun, weoroda rǣswan, Heorogār and Hrōðgār and Hālga til; hȳrde ic, þat Elan cwēn Ongenþēowes wæs Heaðoscilfinges heals-gebedde. Þā wæs Hrōðgāre here-spēd gyfen, wīges weorð-mynd, þæt him his wine-māgas georne hȳrdon, oð þæt sēo geogoð gewēox, mago-driht micel. Him on mōd bearn, þæt heal-reced hātan wolde, medo-ærn micel men gewyrcean, þone yldo bearn ǣfre gefrūnon, and þǣr on innan eall gedǣlan geongum and ealdum, swylc him god sealde, būton folc-scare and feorum gumena. Þā ic wīde gefrægn weorc gebannan manigre mǣgðe geond þisne middan-geard, folc-stede frætwan. Him on fyrste gelomp ǣdre mid yldum, þæt hit wearð eal gearo, heal-ærna mǣst; scōp him Heort naman, sē þe his wordes geweald wīde hæfde. Hē bēot ne ālēh, bēagas dǣlde, sinc æt symle. Sele hlīfade hēah and horn-gēap: heaðo-wylma bād, lāðan līges; ne wæs hit lenge þā gēn þæt se ecg-hete āðum-swerian 85 æfter wæl-nīðe wæcnan scolde. Þā se ellen-gǣst earfoðlīce þrāge geþolode, sē þe in þȳstrum bād, þæt hē dōgora gehwām drēam gehȳrde hlūdne in healle; þǣr wæs hearpan swēg, swutol sang scopes. Sægde sē þe cūðe frum-sceaft fīra feorran reccan",
            "author": user1_data,
            "visibility":"PUBLIC"
        }
        # make a post
        auth_token = f'Basic {base64.b64encode(b'Test User 1:testuser1').decode('ascii')}'
        response = self.client.post(
            f'/api/authors/{self.user1.id}/posts',
            data=json.dumps(post_payload),
            content_type='application/json',
            headers={'Authorization': auth_token}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        post_data = response.data
        print(json.dumps(post_data, indent=2))

        # add the post to user2's inbox
        print('[TESTS]: Adding post to user2 inbox')
        response = self.client.post(
            f'/api/authors/{self.user1.id}/inbox',
            data=json.dumps({
                "type": "inbox",
                "author": f'http://localhost:8000/api/authors/{self.user1.id}',
                "items": [post_data]
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # now, GET the author's inbox. The post should be there
        response = self.client.get(f'/api/authors/{self.user1.id}/inbox')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['type'], 'inbox')
        self.assertEqual(len(response.data['items']), 1)
        # the inbox of the user is correct
        self.assertEqual(response.data['author'], f'http://localhost:8000/api/authors/{self.user1.id}')
        print('[INBOX POST TEST]', response.data['items'])

        # post data is correct 
        post = response.data['items'][0]
        self.assertEqual(post['id'], post_data["url"])
        self.assertEqual(post['type'], 'post')
        self.assertEqual(post['title'], post_payload['title'])
        self.assertEqual(post['author']['id'], user1_data['id'])

    def test_post_inbox_exist(self):
        '''
        This test contains both post and user from the same server
        '''
        # make a post to test user 1
        auth_token = f'Basic {base64.b64encode(b'Test User 1:testuser1').decode('ascii')}'
        create_post_response = self.client.post(
            f'/api/authors/{self.user1.id}/posts',
            data={
                "title":"hi",
                "source":"http://localhost:5173/profile?id=a239fe13-5fc7-45bf-a616-f75a22c7976f",
                "origin":"http://localhost:5173/profile?id=a239fe13-5fc7-45bf-a616-f75a22c7976f",
                "description":"asdas",
                "contentType":"text/plain",
                "content":"asdasd",
                "visibility":"PUBLIC"
            },
            content_type='application/json',
            headers={'Authorization': auth_token}
        )
        self.assertEqual(create_post_response.status_code, status.HTTP_201_CREATED)
        print('Created User 1 post')
        post_data = create_post_response.data
        post_data['type'] = 'post'

        # get user2's inbox
        response = self.client.get(f'/api/authors/{self.user2.id}/inbox')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['items']), 0)
        print('User 2 inbox is empty')

        # add the post to user2's inbox
        response = self.client.post(
            f'/api/authors/{self.user2.id}/inbox',
            data=json.dumps({
                "type": "inbox",
                "author": f'http://localhost:8000/api/authors/{self.user2.id}',
                "items": [post_data]
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        print('Added User 1 post to User 2 inbox')

        # get user2's inbox
        response = self.client.get(f'/api/authors/{self.user2.id}/inbox')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['items']), 1)
        print('[InboxPost.test_post_inbox_exist]', response.data['items'])
        print('[InboxPost.test_post_inbox_exist]', post_data)

        self.assertEqual(response.data['items'][0]['id'], post_data['id'])
        print('User 2 inbox has the correct item')


class InboxFollow(BaseTestCase):
    def _follow_inbox(self, user1, user2):
        '''
        Make user1 send a follow request to user 2 (adding to user2's inbox)
        Helper function for tests
        '''
        user1_response = self.client.get(f'/api/authors/{user1.id}')
        user2_response = self.client.get(f'/api/authors/{user2.id}')
        self.assertEqual(user1_response.status_code, status.HTTP_200_OK)
        self.assertEqual(user2_response.status_code, status.HTTP_200_OK)

        # the id we get from the user response has the URL, but we need to get the raw id
        # TODO: spec says we should use the URL
        user1_data = user1_response.data | {'id': str(user1.id)}
        user2_data = user2_response.data | {'id': str(user2.id)}
        payload = {
            "type": "follow",
            "summary": f"{user1_data['displayName']} wants to follow {user2_data['displayName']}",
            "actor": user1_data,
            "object": user2_data
        }
        # print(json.dumps(payload, indent=2))
        # add the post to user2's inbox
        response = self.client.post(
            f'/api/authors/{user2.id}/inbox',
            data=json.dumps({
                "type": "inbox",
                "author": f'http://localhost:8000/api/authors/{user2.id}',
                "items": [payload]
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        print(f'Added follow request to User {user2.id}\'s inbox')


    def test_follow_inbox(self):
        self._follow_inbox(self.user1, self.user2)

        # get user1's inbox
        response = self.client.get(f'/api/authors/{self.user2.id}/inbox')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['items']), 1)
        self.assertEqual(response.data['items'][0]['type'], 'follow')
        print('User 2 inbox has the correct item')


class InboxDelete(BaseTestCase):
    def test_delete_inbox_unauthenticated(self):
        '''
        Tests that deleting an inbox fails when a user is unauthenticated
        '''
        self._follow_inbox(self.user1, self.user2)

        # Delete user1's inbox
        response = self.client.delete(f'/api/authors/{self.user1.id}/inbox')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_delete_inbox(self):
        '''
        Tests that deleting an inbox works
        Also tests that the inboxes of other users are not affected
        '''
        self._follow_inbox(self.user1, self.user2)
        self._follow_inbox(self.user2, self.user1)

        # Delete user1's inbox
        auth_token = f'Basic {base64.b64encode(b'Test User 1:testuser1').decode('ascii')}'
        response = self.client.delete(
            f'/api/authors/{self.user1.id}/inbox',
            headers={'Authorization': auth_token}
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # get user1's inbox
        response = self.client.get(f'/api/authors/{self.user1.id}/inbox')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['items']), 0)
        print('User 1 inbox is empty')

        # get user2's inbox
        response = self.client.get(f'/api/authors/{self.user2.id}/inbox')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['items']), 1)
        print('User 2 inbox is not empty')
    
class InboxCopyUser(LiveServerTestCase):
    port = 8000
    server_thread_class = LiveServerThreadWithReuse

    def setUp(self):
        # make a user
        self.remoteUserJSON_good = {
            "type": "author",
            "id": "http://localhost:8001/api/authors/123123123",
            "host": "http://localhost:8001/api/",
            "displayName": "Test Remote User 1",
            "url": "http://localhost:8001/api/authors/123123123",
            "github": "https://github.com/uofa-cmput404",
            "profileImage": "https://github.com/uofa-cmput404.png"
        }
        # no ID field
        self.remoteUserJSON_bad = {
            "type": "author",
            "host": "http://localhost:8001/api/",
            "displayName": "Test Remote User 1",
            "github": "https://github.com/uofa-cmput404",
            "profileImage": "https://github.com/uofa-cmput404.png"
        }

        # create user
        self.user1 = models.User.objects.create_user(
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
    
    def test_create_remote_user_good(self):
        '''
        Test to see that the inbox.util.copy_user works well
        '''
        user_instance = inbox.util.copy_user(self.remoteUserJSON_good)

        self.assertEqual(type(user_instance), User)
        self.assertEqual(user_instance.displayName, self.remoteUserJSON_good['displayName'])
        self.assertEqual(user_instance.github, self.remoteUserJSON_good['github'])
        self.assertEqual(user_instance.url, self.remoteUserJSON_good['url'])
        self.assertEqual(user_instance.host, self.remoteUserJSON_good['host'])
        self.assertEqual(user_instance.profileImage, self.remoteUserJSON_good['profileImage'])
        self.assertEqual(user_instance.id, inbox.util.id_from_url(self.remoteUserJSON_good['id']))
        self.assertEqual(user_instance.is_remote, True)

    def test_create_user_bad(self):
        '''
        Test to see that the inbox.util.create_or_copy works well
        '''
        with self.assertRaises(Exception):
            user_instance = inbox.util.copy_user(self.remoteUserJSON_bad)
    
    def test_create_or_copy(self):
        '''
        Run create_or_copy twice with the good JSOn data

        we should get the same user object back
        '''
        user_1 = inbox.util.retrieve_or_copy_author(self.remoteUserJSON_good)
        user_2 = inbox.util.retrieve_or_copy_author(self.remoteUserJSON_good)

        self.assertEqual(user_1, user_2)
    
    def test_create_or_copy_existing_user(self):
        # get the user1 
        user1 = self.client.get(f'/api/authors/{self.user1.id}')

        # run create_or_copy with the user1 data
        user_1 = inbox.util.retrieve_or_copy_author(user1.data)
        self.assertEqual(user_1, self.user1)


# class InboxComment(BaseTestCase):
#     def setUp(self):
#         # call super setUp
#         super().setUp()

#         # make a post to user1
#         auth_token = f'Basic {base64.b64encode(b'Test User 1:testuser1').decode("ascii")}'
#         response = self.client.post(
#             f'/api/authors/{self.user1.id}/posts/',
#             data={
#                 "title":"hi",
#                 "source":"http://localhost:5173/profile?id=a239fe13-5fc7-45bf-a616-f75a22c7976f",
#                 "origin":"http://localhost:5173/profile?id=a239fe13-5fc7-45bf-a616-f75a22c7976f",
#                 "description":"asdas",
#                 "contentType":"text/plain",
#                 "content":"asdasd",
#                 "visibility":"PUBLIC"
#             },
#             content_type='application/json',
#             headers={'Authorization': auth_token}
#         )
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#         self.post_data = response.data
#         self.post_data['type'] = 'post'
    
#     def test_comment_inbox(self):
#         # send a comment to user1's inbox (from user 2)
#         user1_response = self.client.get(f'/api/authors/{self.user1.id}/')
#         user2_response = self.client.get(f'/api/authors/{self.user2.id}/')
#         self.assertEqual(user1_response.status_code, status.HTTP_200_OK)
#         self.assertEqual(user2_response.status_code, status.HTTP_200_OK)

#         print(json.dumps(self.post_data, indent=2))

#         make_comment_payload = {
#             "type":"comment",
#             "author": user2_response.data,
#             "comment":"Sick Olde English",
#             "contentType":"text/markdown",
#             "published":"2015-03-09T13:07:04+00:00",
#         }
#         post_comment_response = self.client.post(
#             self.post_data.get('comments'),
#             data=json.dumps(make_comment_payload),
#             content_type='application/json',
#             headers={'Authorization': f'Basic {base64.b64encode(b"Test User 2:testuser2").decode("ascii")}'}
#         )
#         self.assertEqual(post_comment_response.status_code, status.HTTP_201_CREATED)
#         comment_data = post_comment_response.data
#         self.assertEqual(post_comment_response.data.get('type'), 'comment')

#         print(f'[TESTS]: Comment data:')
#         comment_url = standardize_url(f"{self.post_data.get('url')}/comments/{comment_data.get('id')}")
#         # get request to comment_url
#         response = self.client.get(comment_url)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(response.data.get('type'), 'comment')
#         self.assertEqual(response.data.get('comment'), 'Sick Olde English')
#         print(json.dumps(response.data, indent=2))


#         # payload = {
#         #     "type":"comment",
#         #     "author": user1_response.json(),
#         #     "comment":"Sick Olde English",
#         #     "contentType":"text/markdown",
#         #     "published":"2015-03-09T13:07:04+00:00",
#         #     "id": f"{self.post_data.get('url')}/comments/{comment_data.get('id')}",
#         # }
#         # response = self.client.post(
#         #     f'/api/authors/{self.user1.id}/inbox',
#         #     data=json.dumps({
#         #         "type": "inbox",
#         #         "author": f'http://localhost:8000/api/authors/{self.user1.id}',
#         #         "items": [payload]
#         #     }),
#         #     content_type='application/json',
#         # )
#         # self.assertEqual(response.status_code, status.HTTP_201_CREATED
    
class InboxLike(BaseTestCase):
    def test_add_like_inbox(self):
        # GET user1 json data
        response = self.client.get(f'/api/authors/{self.user1.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user1_data = response.data | {'id': str(self.user1.id)}

        payload = {
            "summary": "Lara Croft Likes your post",         
            "type": "like",
            "author": user1_data,
            "object":"http://127.0.0.1:5454/authors/9de17f29c12e8f97bcbbd34cc908f1baba40658e/posts/764efa883dda1e11db47671c4a3bbd9e"
        }
        response = self.client.post(
            f'/api/authors/{self.user1.id}/inbox',
            data=json.dumps({
                "type": "inbox",
                "author": f'http://localhost:8000/api/authors/{self.user1.id}',
                "items": [payload]
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # now, GET the author's inbox. The post should be there
        response = self.client.get(f'/api/authors/{self.user1.id}/inbox')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['type'], 'inbox')
        self.assertEqual(len(response.data['items']), 1)

        item_1 = response.data['items'][0]

        # the inbox of the user is correct
        self.assertEqual(item_1['author']['id'], f'http://localhost:8000/api/authors/{self.user1.id}')
    
    def test_add_like_inbox_2(self):
        '''
        Send a like to an inbox and check that a Like object is created in the database
        '''
         # GET user1 json data
        response = self.client.get(f'/api/authors/{self.user1.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user1_data = response.data | {'id': str(self.user1.id)}

        payload = {
            "summary": "Lara Croft Likes your post",         
            "type": "like",
            "author": user1_data,
            "object":"http://127.0.0.1:5454/authors/9de17f29c12e8f97bcbbd34cc908f1baba40658e/posts/764efa883dda1e11db47671c4a3bbd9e"
        }
        response = self.client.post(
            f'/api/authors/{self.user1.id}/inbox',
            data=json.dumps({
                "type": "inbox",
                "author": f'http://localhost:8000/api/authors/{self.user1.id}',
                "items": [payload]
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # check that a Like object is created in the database
        like = models.Like.objects.filter(
            author=standardize_url(self.user1.url),
            object=standardize_url(payload['object'])
        )
        self.assertEqual(like.count(), 1)

