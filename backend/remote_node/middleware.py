'''
Middleware to handle remote_node stuff
'''
import urllib.parse
from django.conf import settings
from django.http import HttpResponse
import base64
from restapi.models import User
import util.main as util


class RemoteAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        # get which URL the request came from
        referer = urllib.parse.urlparse(request.META.get('HTTP_REFERER')).netloc
        host = request.build_absolute_uri()
        host_domain = urllib.parse.urlparse(host).netloc
        util.log('RemoteAuthMiddleware', f'referer: {referer}, host: {host}, request.path: {request.path}')

        if '/api/admin' in host:
            # if we're accessing the admin page, no auth needed
            # util.log('RemoteAuthMiddleware', 'we\'re accessing the admin page! No auth needed')
            return self.get_response(request)
        
        if 'api/schema/docs' in host:
            # if we're accessing the swagger docs, no auth needed
            # util.log('RemoteAuthMiddleware', 'we\'re accessing the docs! No auth needed')
            return self.get_response(request)
        
        if '/api' not in host:
            # if we're not accessing the api, no auth needed
            # util.log('RemoteAuthMiddleware', 'we\'re not accessing the api! No auth needed')
            return self.get_response(request)

        if not referer and host_domain == 'testserver':
            # if we're running tests
            # util.log('RemoteAuthMiddleware', 'we\'re running tests or in localhost! No auth needed')
            return self.get_response(request)

        if referer == host_domain:
            # The request originated from a connected frontend
            # util.log('RemoteAuthMiddleware', 'Request from connected frontend. Auth granted.')
            return self.get_response(request)

        # Otherwise, the request is coming from a remote node.
        # util.log('RemoteAuthMiddleware', f'Request from remote node. auth header: {request.META.get("HTTP_AUTHORIZATION")}')
        # find user with the given token
        # https://stackoverflow.com/a/46428523
        try:
            token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]
            displayName, pwd = base64.b64decode(token).decode('ascii').split(':')
            user = User.objects.get(displayName=displayName)
        except Exception as e:
            util.log('RemoteAuthMiddleware', f'Exception: {e}')
            return HttpResponse('Unauthorized', status=401)
        
        password_valid = user.check_password(pwd)
        if not password_valid:
            util.log('RemoteAuthMiddleware', f'Password invalid for user {user.displayName}. Unauthorized.')
            return HttpResponse('Unauthorized', status=401)

        util.log('RemoteAuthMiddleware', f'user: {user}')
        if not user.is_active:
            util.log('RemoteAuthMiddleware', f'User {user.displayName} not active. Unauthorized.')
            return HttpResponse('Unauthorized', status=401)

        if user.is_node:
            print(f'[RemoteAuthMiddleware] User {user.displayName} is a node. Auth granted.')
        else:
            print(f'[RemoteAuthMiddleware] User {user.displayName} is user, not a node. Auth granted.')

        return self.get_response(request)
