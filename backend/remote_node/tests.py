from django.test import LiveServerTestCase, TestCase
from unittest.mock import patch 
from django.test.client import RequestFactory
from remote_node.middleware import RemoteAuthMiddleware
from django.conf import settings
from util.tests import LiveServerThreadWithReuse
from unittest.mock import MagicMock
from restapi.models import User
import base64
from remote_node import util
from remote_node.models import RemoteNode

# Create your tests here.

class RemoteAuthMiddlewareTest(TestCase):
    def setUp(self):
        # create a remoteNode user
        self.userNode = User.objects.create_node(
            displayName='testNode', 
            password='testPwd', 
            url='https://test.com/'
        )
        self.userNodeToken = base64.b64encode(b'testNode:testPwd').decode('ascii')

    def test_middleware_localhost(self):
        rf = RequestFactory()
        request = rf.get('/')
        request.META['HTTP_REFERER'] = 'http://localhost:5173/'
        request.META['HTTP_AUTHORIZATION'] = f'Basic {self.userNodeToken}'
        request.build_absolute_uri = lambda: 'http://localhost:8000/api/'

        get_response = MagicMock()

        middleware = RemoteAuthMiddleware(get_response)
        response = middleware(request)

        # test that get_response has been returned
        # if not, our middleware did something else
        self.assertEqual(get_response.return_value, response)
    
    def test_middleware_remote_noauth(self):
        '''
        Tests that the middleware returns the get_response when the request is coming from our node, with no auth
        '''
        rf = RequestFactory()
        request = rf.get('/')
        request.META['HTTP_REFERER'] = 'https://our-node.com/'
        request.build_absolute_uri = lambda: 'https://our-node.com/api/'

        get_response = MagicMock()

        middleware = RemoteAuthMiddleware(get_response)
        response = middleware(request)

        # test that get_response has been returned
        # if not, our middleware did something else
        self.assertEqual(get_response.return_value, response)
    
    def test_middleware_remote_401(self):
        '''
        Tests that the middleware returns a 401 when the request is coming from a different node, with no auth
        '''
        rf = RequestFactory()
        request = rf.get('/')
        request.META['HTTP_REFERER'] = 'https://another-node.com/'
        request.build_absolute_uri = lambda: 'https://our-node.com/api/'

        get_response = MagicMock()

        middleware = RemoteAuthMiddleware(get_response)
        response = middleware(request)

        # test that get_response has not been returned
        # if it has, our middleware did not return a 401
        self.assertNotEqual(get_response.return_value, response)
        self.assertEqual(response.status_code, 401)
    
    def test_middleware_remote_success(self):
        rf = RequestFactory()
        request = rf.get('/')
        request.META['HTTP_REFERER'] = b''
        request.META['HTTP_AUTHORIZATION'] = f'Basic {self.userNodeToken}'
        request.build_absolute_uri = lambda: 'http://localhost:8000/api/'

        get_response = MagicMock()

        middleware = RemoteAuthMiddleware(get_response)
        response = middleware(request)

        # test that get_response has been returned
        # if not, our middleware did something else
        self.assertEqual(get_response.return_value, response)
    
    def test_middleware_remote_wrongpwd(self):
        wrong_token = base64.b64encode(b'testNode:wrongPwd').decode('ascii')

        rf = RequestFactory()
        request = rf.get('/')
        request.META['HTTP_REFERER'] = b''
        request.META['HTTP_AUTHORIZATION'] = f'Basic {wrong_token}'
        request.build_absolute_uri = lambda: 'https://our-node.com/api/'

        get_response = MagicMock()
        
        middleware = RemoteAuthMiddleware(get_response)
        response = middleware(request)

        self.assertNotEqual(get_response.return_value, response)
        self.assertEqual(response.status_code, 401)


class RemoteAuthUtilTest(TestCase):
    '''
    Tests that the util.get and util.post send the right headers
    '''
    def setUp(self):
        # create a couple of RemoteNode instances
        self.node1 = RemoteNode.objects.create(
            nodeName='node1',
            displayName='local',
            url='http://localhost:8000/',
            password='node1pwd'
        )
        self.node1Token = base64.b64encode(b'local:node1pwd').decode('ascii')
    
    @patch('requests.get')
    def testNode1(self, mock_get):
        '''
        test that the util.get sends the right headers
        we are mocking the requests.get so that we don't actually send a request
        https://stackoverflow.com/a/28821004
        '''
        util.get('http://localhost:8000/api/nested/api')

        self.assertTrue(mock_get.called)
        headers = mock_get.call_args[1]['headers']
        self.assertEqual(headers['Authorization'], f'Basic {self.node1Token}')
        self.assertEqual(headers['Content-Type'], 'application/json')
        

class TransformURLTest(TestCase):
    def setUp(self):
        self.node_lost = RemoteNode.objects.create(
            nodeName='lost',
            displayName='attack',
            url='https://lostone-8ec8a3227ce0.herokuapp.com/api/',
        )
        self.node_snack = RemoteNode.objects.create(
            nodeName='Team Snack',
            displayName='teamattack@email.com',
            url='https://snackoverflow-7f593e547e10.herokuapp.com/api/',
        )
    
    def test_transform_url_lost(self):
        url = 'https://lostone-8ec8a3227ce0.herokuapp.com/authors/0bc32965-95f6-4450-8d19-5e484e825dee/inbox'
        transformed = util.transform_url_for_node(url, self.node_lost)
        self.assertEqual(transformed, 'https://lostone-8ec8a3227ce0.herokuapp.com/api/authors/0bc32965-95f6-4450-8d19-5e484e825dee/inbox/')
    
    def test_transform_url_snack(self):
        '''
        Snack should not be impacted
        '''
        url = 'https://snackoverflow-7f593e547e10.herokuapp.com/api/authors/0bc32965-95f6-4450-8d19-5e484e825dee/inbox'
        transformed = util.transform_url_for_node(url, self.node_snack)
        self.assertEqual(transformed, url)
        