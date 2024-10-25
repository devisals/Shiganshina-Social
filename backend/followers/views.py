import base64
from django.shortcuts import render
from rest_framework import viewsets, permissions, pagination, status
from . import models, serializers
from rest_framework.response import Response
import requests
import urllib
from restapi.serializers import UserSerializer
import util.main as util
import remote_node.util
from remote_node.models import RemoteNode
import os
import json
from restapi.models import User

# Create your views here.
BASE_URL = os.environ.get('HOST_API_URL') + 'authors'
class FollowerViewSet(viewsets.ModelViewSet):
    '''
    API endpoint that allows followers to be added/edited/removed
    '''
    queryset = models.Follower.objects.all()
    serializer_class = serializers.FollowerSerializer
    nodes = RemoteNode.objects.filter(disabled=False)

    def list(self, request, author_id=None, *args, **kwargs):
        '''
        method: GET
        Returns a list of followers for a single author
        URL: /authors/{AUTHOR_ID}/followers/
        '''
        followers_list = {"type": "followers", "items": []}

        if 'all' not in request.query_params:
            # search only locally
            util.log('FollowerViewSet/list', f'Getting followers for author {author_id} LOCALLY: {request.query_params}')
            try:
                author = models.User.objects.get(pk=author_id, is_remote=False)
                followers = models.Follower.objects.filter(object=author)

                for follower in followers:
                    try:
                        follower_still_exists = self._check_remote_follower(author, follower.actor, foreign_author_id=follower.actor.url)
                        if follower_still_exists:
                            followers_list['items'].append(UserSerializer(follower.actor).data)
                        else:
                            util.log('FollowerViewSet/list', f'Follower object does not exist anymore for (object={author}, actor={follower.actor}). Skipping adding to list...')
                    except Exception as e:
                        util.log('FollowerViewSet/get_single', f'Error checking remote follower: {e}. Moving on...')
                return Response(followers_list, status=status.HTTP_200_OK)
            except models.User.DoesNotExist:
                util.log('FollowerViewSet/list', f'Author {author_id} does not exist')
                return Response({'error': f'Author {author_id} does not exist'}, status=status.HTTP_404_NOT_FOUND)

        # else, we look through all nodes

        for node in self.nodes:
            request_url = remote_node.util.transform_url_for_node(
                f'{node.url.rstrip("/")}/authors/{author_id}/followers', 
                node
            )
            try:
                util.log('FollowerViewSet/list', f'Request URL: {request_url}')
                auth_token = base64.b64encode(f"{node.displayName}:{node.password}".encode('ascii')).decode('ascii')
                headers = {
                    'Authorization': f'Basic {auth_token}',
                    'Content-Type': 'application/json'
                }
                response = requests.get(request_url, headers=headers)
                if response.status_code == 200:
                    followers_list['items'] = response.json()['items']
                    util.log('FollowerViewSet/list', f'Got {len(followers_list["items"])} followers from {request_url}')
                    return Response(followers_list, status=status.HTTP_200_OK)
                else:
                    util.log('FollowerViewSet/list', f'Failed to get followers from {request_url} with status code {response.status_code}. Moving onto next node...')
            except Exception as e:
                util.log('FollowerViewSet/list', f'Error getting followers: {e}. Moving onto next node.')

        util.log('FollowerViewSet/list', f'Couldn\'t find followers for author {author_id} in any node. Returning empty list')
        return Response({'error': f'Could not find author {author_id} in any node.'}, status=status.HTTP_404_NOT_FOUND)


    def get_single(self, request, author_id=None, foreign_author_id=None, *args, **kwargs):
        '''
        method: GET
        Returns a single follower
        URL: /authors/{AUTHOR_ID}/followers/{FOREIGN_AUTHOR_ID}
        '''

        object_id = self.kwargs.get('author_id')
        actor_id = util.id_from_url(foreign_author_id)

        if 'all' not in request.query_params:
            util.log('FollowerViewSet/get_single', f'Getting single follower locally: object={object_id} actor={actor_id}')
            try:
                object = models.User.objects.get(pk=object_id)
            except models.User.DoesNotExist:
                util.log('FollowerViewSet/get_single', f'Object user {object_id} does not exist (followee)')
                return Response({'error': f'Object user {object_id} does not exist (Followee)'}, status=status.HTTP_404_NOT_FOUND)

            try:
                actor = models.User.objects.get(pk=actor_id)
            except models.User.DoesNotExist:
                util.log('FollowerViewSet/get_single', f'Actor user {actor_id} does not exist (follower)')
                return Response({'error': f'Object user {actor_id} does not exist'}, status=status.HTTP_404_NOT_FOUND)

            if not models.Follower.objects.filter(object=object_id, actor=actor_id).exists():
                util.log('FollowerViewSet/get_single', f'Follower object does not exist (object={object}, actor={actor})')
                return Response({'error': f'Follower object does not exist (object={object}, actor={actor})'}, status=status.HTTP_404_NOT_FOUND)

            object_data = UserSerializer(object).data
            actor_data = UserSerializer(actor).data

            try:
                follower_still_exists = self._check_remote_follower(object, actor, foreign_author_id)
                if not follower_still_exists:
                    return Response({'error': f'Follower object does not exist anymore for (object={object}, actor={actor})'}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                util.log('FollowerViewSet/get_single', f'Error checking remote follower: {e}. Moving on...')

            return Response({
                'type': 'follower',
                'summary': f'{actor_data["displayName"]} follows {object_data["displayName"]}',
                'actor': actor_data,
                'object': object_data 
            })

        # else, we look through all nodes
        util.log('FollowerViewSet/get_single', f'Getting single follower from all nodes: object={object_id} actor={actor_id}')
        for node in self.nodes:
            request_url = remote_node.util.transform_url_for_node(
                f'{node.url.rstrip("/")}/authors/{author_id}/followers/{urllib.parse.quote(foreign_author_id, safe="")}',
                node
            )
            try:
                util.log('FollowerViewSet/get_single', f'Request URL: {request_url}')
                auth_token = base64.b64encode(f"{node.displayName}:{node.password}".encode('ascii')).decode('ascii')
                headers = {
                    'Authorization': f'Basic {auth_token}',
                    'Content-Type': 'application/json'
                }
                response = requests.get(request_url, headers=headers)
                if response.status_code == 200:
                    follower_json = response.json()
                    util.log('FollowerViewSet/get_single', f'Got 200 response from {request_url}:')
                    print(json.dumps(follower_json, indent=2))
                    return Response(follower_json, status=status.HTTP_200_OK)
                else:
                    util.log('FollowerViewSet/get_single', f'Failed to get follower {foreign_author_id} from {request_url} with status code {response.status_code}. Moving onto next node...')
            except Exception as e:
                util.log('FollowerViewSet/get_single', f'Error getting follower: {e}. Moving onto next node.')

        util.log('FollowerViewSet/get_single', f'Could not find follower data author={author_id}, actor={foreign_author_id} in any node. Returning 404')
        return Response({'error': f'Could not find follower data author={author_id}, actor={foreign_author_id} in any node.'}, status=status.HTTP_404_NOT_FOUND)

    def update(self, request, author_id=None, foreign_author_id=None, *args, **kwargs):
        '''
        method: PUT
        Creates a new follower FOREIGN_AUTHOR_ID for author AUTHOR_ID
        URL: /authors/{AUTHOR_ID}/followers/{FOREIGN_AUTHOR_ID}
        '''
        if request.user.is_anonymous:
            return Response(status=status.HTTP_403_FORBIDDEN)

        # ensure the user is not a node
        if request.user.is_node:
            return Response(status=status.HTTP_403_FORBIDDEN)

        # ensure user is logged in (in any way)
        util.log('FollowerViewSet/update', f'Update follow request: {request.user.is_authenticated} {request.user}')
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_403_FORBIDDEN)
        try:
            author = models.User.objects.get(pk=author_id, is_remote=False)
            print('[FollowerViewSet/update] Found author:', author.displayName)
        except models.User.DoesNotExist:
            print('[FollowerViewSet/update] Author not found')
            return Response({'error': 'The author you want to follow cannot be found'}, status=status.HTTP_404_NOT_FOUND)
        
        # ensure the user is the author
        if request.user.id != author_id:
            print(f'[FollowerViewSet/update] User {request.user.id} is not allowed to add followers for author {author_id}')
            return Response({'error': 'You are not allowed to add followers for this author'}, status=status.HTTP_403_FORBIDDEN)

        actor_id = util.id_from_url(foreign_author_id)
        if not models.User.objects.filter(pk=actor_id).exists():
            return Response({'error': 'The follower does not exist.'}, status=status.HTTP_404_NOT_FOUND)
        actor = models.User.objects.get(pk=actor_id)

        # check if the follower already exists
        try:
            models.Follower.objects.get(object=author, actor=actor)
            print(f'[FollowerViewSet/update] Follower already exists')
            return Response(data={'error': f'That user already follows {author.displayName}'}, status=status.HTTP_400_BAD_REQUEST)
        except models.Follower.DoesNotExist:
            pass
        
        util.log('FollowerViewSet/update', f'Making {actor.displayName} follow {author.displayName}')
        serializer = serializers.FollowerSerializer(data={
            'object': author.id,
            'actor': actor.id
        })
        if serializer.is_valid():
            serializer.save(object=author, actor=actor)

            returnData = {
                'type': 'follower',
                'summary': f'{actor.displayName} follows {author.displayName}',
                'actor': UserSerializer(actor).data,
                'object': UserSerializer(author).data
            }
            return Response(returnData, status=status.HTTP_201_CREATED)
        else:
            util.log('FollowerViewSet/update', f'Error creating follower: {serializer.errors}')
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def destroy(self, request, foreign_author_id=None, *args, **kwargs):
        '''
        method: DELETE
        Removes a follower FOREIGN_AUTHOR_ID for author AUTHOR_ID
        URL: /authors/{AUTHOR_ID}/followers/{FOREIGN_AUTHOR_ID}

        This only deletes from the local Follower table. 
        '''
        author_id = self.kwargs.get('author_id')
        actor_id = util.id_from_url(foreign_author_id)

        # check if the author exists locally
        if not models.User.objects.filter(pk=author_id).exists():
            util.log('FollowerViewSet/destroy', f'Author {author_id} does not exist (followee)')
            return Response({'error': f'Author {author_id} not found (follower)'}, status=status.HTTP_404_NOT_FOUND)

        # test that actor exists locally
        if not models.User.objects.filter(pk=actor_id).exists():
            util.log('FollowerViewSet/destroy', f'Actor {actor_id} does not exist (follower)')
            return Response({'error': f'Actor {actor_id} not found (followee)'}, status=status.HTTP_404_NOT_FOUND)

        author = models.User.objects.get(pk=author_id)
        actor = models.User.objects.get(pk=actor_id)

        if author.is_remote and 'linkup1' in author.url:
            # we are trying to unfollow a user from TeamHTTP. Send them an "unfollow" inbox
            inbox_url = f"{author.url.rstrip('/')}/inbox"
            util.log('FollowerViewSet/destroy', f'Author is remote and from HTTP. Sending unfollow inbox to {inbox_url}')
            data = {
                'type': 'unfollow',
                'summary': f'{actor.displayName} unfollowed {author.displayName}.',
                'actor': UserSerializer(actor).data,
                'object': UserSerializer(author).data
            }
            inbox_item = {
                'type': 'inbox',
                'author': author.url,
                'items': [data]
            }
            util.log('FollowerViewSet/destroy', f'Sending unfollow inbox to {author.url} in team HTTP')
            print(json.dumps(inbox_item, indent=2))
            print(inbox_item)
            response = remote_node.util.post(inbox_url, inbox_item)
            if response.status_code == 201 or response.status_code == 200:
                print('[FollowerViewSet/destroy] Unfollow inbox sent successfully')
            else:
                print(f'[FollowerViewSet/destroy] Failed to send unfollow inbox: {response.status_code} {response.text}. Whatever...')
        elif author.is_remote and 'lostone' in author.url:
            # we are trying to unfollow a user from team Lost. Send them an "unfollow" inbox
            inbox_url = f"{author.url.rstrip('/')}/inbox/"
            util.log('FollowerViewSet/destroy', f'Author is remote and from HTTP. Sending unfollow inbox to {inbox_url}')
            data = {
                'type': 'Unfollow',
                'summary': f'{actor.displayName} unfollowed {author.displayName}.',
                'actor': UserSerializer(actor).data,
                'object': UserSerializer(author).data
            }
            util.log('FollowerViewSet/destroy', f'Sending unfollow inbox to {author.url} in team Lost')
            print(json.dumps(data, indent=2))
            print(data)
            response = remote_node.util.post(inbox_url, data)
            if response.status_code == 201 or response.status_code == 200:
                print('[FollowerViewSet/destroy] Unfollow inbox sent successfully')
            else:
                print(f'[FollowerViewSet/destroy] Failed to send unfollow inbox: {response.status_code} {response.text}. Whatever...')


        try:
            follower = models.Follower.objects.get(
                object=author, 
                actor=actor
            )
            follower.delete()
            print('[FollowerViewSet/destroy] Follower removed successfully')
            return Response(status=status.HTTP_204_NO_CONTENT)
        except models.Follower.DoesNotExist:
            print('[FollowerViewSet/destroy] Follower not found')
            return Response({'error': 'Follower not found'}, status=status.HTTP_404_NOT_FOUND)


    def _check_remote_follower(self, object: User, actor: User, foreign_author_id=None):
        '''
        now, check if object is remote
        If they are, we need to check the appropriate remote nodes to see if the follower exists (e.g. if the remote user unfollowed)
        if the remote use unfollowed, we should delete the local follower entry

        returns False if the follower does not exist
        returns True if it does
        '''
        # check if "linkup1" is NOT in object.url because team HTTP does not do things this way.
        # team lost also does not do things this way, so escape
        if object.is_remote and 'linkup1' not in object.url and 'lostone' not in object.url:
            util.log('FollowerViewSet/get_single', f'User "{object} is remote. Checking remote if {actor} still follows {object}"')
            object_follower_url = object.url.rstrip('/') + '/followers/' + urllib.parse.quote(foreign_author_id, safe='')
            util.log('FollowerViewSet/get_single', f'getting url: {object_follower_url}')
            response = remote_node.util.get(object_follower_url)
            if response.status_code == 200:
                # we're good, continuing
                util.log('FollowerViewSet/get_single', f'Got 200 response from {object_follower_url}, so {actor} still follows {object}. We are good!')
                return True
            elif response.status_code == 404:
                # the follower does not exist, so we should delete the local follower entry
                util.log('FollowerViewSet/get_single', f'Got 404 response from {object_follower_url}, so {actor} does not follow {object}. Deleting local follower entry...')
                models.Follower.objects.get(object=object, actor=actor).delete()
                return False
            else:
                util.log('FollowerViewSet/get_single', f'Failed to get follower from {object_follower_url} with status code {response.status_code}. Skipping.')
                return True
        else:
            return True
