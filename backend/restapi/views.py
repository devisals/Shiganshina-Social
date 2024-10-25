import base64
import json
from rest_framework import viewsets, status, permissions, pagination
from rest_framework.response import Response
from rest_framework.views import APIView
from . import models, serializers
from rest_framework.authentication import BasicAuthentication
from post.serializers import LikeSerializer
from post.models import Like, Post
from rest_framework import permissions
from restapi.serializers import UserSerializer
from post.serializers import PostSerializer
from githubUpdater.githubUpdater import updateGithubAll, updateGithubSingle
from remote_node.models import RemoteNode
import remote_node.util

import requests
from util.main import url_remove_trailing_slash
import util.main as util
import os

BASE_URL = os.environ.get('HOST_API_URL') + 'authors'

class CustomPagination(pagination.PageNumberPagination):
    page_size = 20
    page_size_query_param = 'size'
    max_page_size = 10000


class AuthView(APIView):
    '''
    Register, or login
    '''
    authentication_classes = [BasicAuthentication]

    def post(self, request, format=None):
        '''
        METHOD: POST
        Adds a user as inactive (is_active=False) so the site admin can approve them

        See: https://eclass.srv.ualberta.ca/mod/forum/discuss.php?d=2450399
        https://forum.djangoproject.com/t/django-registrations-controlled-by-admin/27931

        usage:
        curl -X POST -u "admin:1234" -H "Content-Type: application/json" -d '{"displayName": "Test User 1", "password": "testpassword1", "github": "https://github.com/joshuanianji", "host": "http://localhost:8000/api/"}' http://localhost:8000/api/auth/
        '''
        data = request.data

        # I still want to use the serializer, but I don't want to require the "host" or 'url' field
        if not all(field in data for field in ['password', 'displayName', 'github']):
            return Response({'error': 'missing fields!'}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = serializers.UserSerializer(data=request.data, partial=True)
        if serializer.is_valid():
            # we could user serializer.save(), but we have a good user_manager function
            serialized = serializer.validated_data
            new_user = models.User.objects.create_user(
                serialized['displayName'],
                data['password'],
                serialized['github'],
                serialized['profileImage'] if 'profileImage' in serialized else f"{url_remove_trailing_slash(serialized['github'])}.png",
            )

            # set is_active to False, so the admin can approve the user
            new_user.is_active = False
            new_user.save()
            serialized_user = serializers.UserSerializer(new_user).data

            return Response(serialized_user, status=status.HTTP_201_CREATED)
        else:
            util.log('AuthView/post', f"Error: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def get(self, request, format=None):
        '''
        METHOD: GET
        Basically login. Given the basic auth, returns the user object

        usage:

        curl -X GET -u "admin:1234" http://localhost:8000/api/auth/
        '''
        util.log('AuthView/get', f'Login request {request.user}, {request.auth}')
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        content = serializers.UserSerializer(request.user).data  # `django.contrib.auth.User` instance.
        return Response(content)


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed (no user story for editing)
    """
    queryset = models.User.objects.all().order_by('-date_joined')
    serializer_class = serializers.UserSerializer
    # permission_classes = [permissions.IsAuthenticated]


class AuthorViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows authors (users who are non-admins) to be viewed or edited.
    """
    # authors are all users without the "is_staff" field
    queryset = models.User.objects.filter(is_staff=False, is_node=False, is_remote=False).order_by('-date_joined')
    serializer_class = serializers.UserSerializer
    # permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = CustomPagination
    nodes = RemoteNode.objects.filter(disabled=False)

    def list(self, request):
        """
        METHOD: GET
        Returns a list of authors on the local system
        URL: authors/
        """

        authors = {"type": "authors", "items": []}

        # Get local authors first
        util.log('AuthorViewSet/list', 'Requesting local authors only, all not in query params')
        queryset = models.User.objects.filter(is_staff=False, is_node=False, is_active=True, is_remote=False).order_by('-date_joined')
        local_serializer = serializers.UserSerializer(queryset, many=True)
        authors["items"] = local_serializer.data

        # if all authors are not requested, paginate and return local authors
        if "all" not in request.query_params:
            paginator = CustomPagination()
            paginated_authors = paginator.paginate_queryset(authors["items"], request)
            authors["items"] = paginated_authors
            return Response(authors, status=status.HTTP_200_OK)


        # otherwise, return all authors from all nodes
        remote_authors = []
        for node in self.nodes:
            # Skip the local node
            if node.displayName == "local":
                continue
            
            request_url = remote_node.util.transform_url_for_node(
                f"{node.url.rstrip('/')}/authors",
                node
            )
            auth_token = base64.b64encode(f"{node.displayName}:{node.password}".encode('ascii')).decode('ascii')
            headers = {"Authorization": f"Basic {auth_token}"}
            try:
                if node.displayName == 'user':
                    # team HTTP needs a trailing slash
                    request_url += '/'
                response = requests.get(request_url, headers=headers)
                if response.status_code != status.HTTP_200_OK:
                    util.log('AuthorViewSet/list', f"Failed to connect to {node.nodeName}. Status code: {response.status_code}")
                    continue
                remote_authors.extend(response.json()["items"])
            except requests.RequestException as e:
                util.log('AuthorViewSet/list', f"Error connecting to {node.nodeName}: {e}")

        # Combine local and remote authors
        authors["items"] += remote_authors

        # Paginate the combined authors
        paginator = CustomPagination()
        paginated_authors = paginator.paginate_queryset(authors["items"], request)
        authors["items"] = paginated_authors
        return Response(authors, status=status.HTTP_200_OK)

    def retrieve(self, request, pk):
        """
        METHOD: GET
        Returns a single author
        URL: authors/{author_id}/
        """
        author_id = pk

        # Try find the author locally
        try:
            author = models.User.objects.get(pk=author_id, is_staff=False, is_node=False, is_remote=False)
            serializer = serializers.UserSerializer(author)
            author_data = serializer.data
            return Response(author_data, status=status.HTTP_200_OK)
        except models.User.DoesNotExist:
            util.log('AuthorViewSet/retrieve', f"Author {author_id} not found locally")

        # if all is not in the query params, return 404
        if "all" not in request.query_params:
            util.log('AuthorViewSet/retrieve', f"All not in query params, returning 404 for author {author_id}")
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        # Try find the author on a remote node
        for node in self.nodes:
            # Skip local node
            if node.displayName == "local":
                continue

            request_url = remote_node.util.transform_url_for_node(
                f"{node.url}authors/{author_id}", 
                node
            )
            util.log('AuthorViewSet/retrieve', f"Requesting author {author_id} from {node.nodeName} using URL {request_url}")
            auth_token = base64.b64encode(f"{node.displayName}:{node.password}".encode('ascii')).decode('ascii')
            headers = {"Authorization": f"Basic {auth_token}"}
            try:
                response = requests.get(request_url, headers=headers)
                # Return if found, log otherwise
                if response.status_code == status.HTTP_200_OK:
                    return Response(response.json())
                util.log('AuthorViewSet/retrieve', f"{node.displayName} returned status code {response.status_code} for author {author_id}")
            except requests.RequestException as e:
                util.log('AuthorViewSet/retrieve', f"Error connecting to {node.nodeName}: {e}")

        return Response(status=status.HTTP_404_NOT_FOUND)



    def update(self, request, pk=None):
        """
        METHOD: PUT
        Updates a single author
        URL: authors/{author_id}/
        """
        # Nodes are not allowed to update local authors
        if request.user.is_node:
            return Response(
                {"error": "You cannot update authors on this node"},
                status=status.HTTP_403_FORBIDDEN)

        # if logged in user is not the author, return 403
        if str(request.user.id) != pk:
            return Response(
                {"error": "You cannot update another author"},
                status=status.HTTP_403_FORBIDDEN)

        author = models.User.objects.get(pk=pk)

        oldGithub = author.github
        serializer = serializers.UserSerializer(author, data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()


        if oldGithub != author.github:
            # update the profile image if it has changed
            if author.profileImage == oldGithub + '.png':
                author.profileImage = author.github + '.png'
                author.save()
            # clear the old github posts
            try:
                clearGithubPosts = Post.objects.filter(author=author, isGithub=True)
                postCount = clearGithubPosts.count()
                clearGithubPosts.delete()
            except Post.DoesNotExist:
                pass
            util.log('AuthorViewSet/update', f'Cleared {postCount} github posts')
            # update the github posts
            util.log('AuthorViewSet/update', f'Added {len(updateGithubSingle(pk))} new github posts')
        updated_author = serializers.UserSerializer(author).data
        return Response(updated_author, status=status.HTTP_200_OK)


class LikedViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows all the likes of an author to be viewed.
    URL: authors/{author_id}/liked/
    """
    queryset = Like.objects.all()
    serializer_class = LikeSerializer
    nodes = RemoteNode.objects.filter(disabled=False)

    def list(self, request, author_id):
        # check local author exists
        try:
            author = models.User.objects.get(pk=author_id)
        except models.User.DoesNotExist:
            util.log('LikedViewSet/list', f"Author {author_id} not found locally")
        else:
            util.log('LikedViewSet/list', f"Author {author_id} found locally")
            likes = Like.objects.filter(author=author.url)
            serializer = self.serializer_class(likes, many=True)
            author_data = UserSerializer(author).data
            for like in serializer.data:
                like["author"] = author_data
                return Response({
                    "type": "liked",
                    "items": serializer.data
                }, status=status.HTTP_200_OK)
            
        # if all is not in the query params, return 404
        if "all" not in request.query_params:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        # try find the author on a remote node
        url = request.build_absolute_uri().split('api/')[1]
        url = util.removeQueryParamAll(url)

        for node in self.nodes:
            if node.displayName == "local":
                continue
            try:
                request_url = remote_node.util.transform_url_for_node(
                    f"{node.url.rstrip('/')}/{url}",
                    node
                )
                util.log('LikedViewSet/list', f'Requesting from {request_url}')
                response = remote_node.util.get(request_url)
                if response.status_code == 200:
                    return Response(response.json())
                else:
                    util.log('LikedViewSet/list', f"Failed to connect to {node.nodeName}. Status code: {response.status_code}")
            except requests.RequestException as e:
                util.log('LikedViewSet/list', f"Error connecting to {node.nodeName}: {e}")
        return Response(status=status.HTTP_404_NOT_FOUND)



class UpdateGithub(APIView):
    '''
    Update the github posts
    URL: /update_github/
    '''
    def put(self, request):
        '''
        METHOD: PUT
        Updates the github field of a user
        '''
        # Nodes are not allowed to update local authors
        # if request.user.is_node:
        #     return Response(status=status.HTTP_403_FORBIDDEN)

        util.log('UpdateGithub', 'Updating github posts')
        newPosts = {
            "type": "github-new",
            "items": []
        }

        new_created = updateGithubAll()
        for post in new_created:
            newPosts["items"].append(PostSerializer(post).data)
        return Response(newPosts, status=status.HTTP_200_OK)

