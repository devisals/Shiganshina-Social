import base64
import datetime
import json
from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.contenttypes.models import ContentType
from restapi.serializers import UserSerializer
from post import models, serializers
from rest_framework import viewsets, permissions, pagination, status, views
from rest_framework.response import Response
from rest_framework.request import Request
from restapi.models import User
from .models import Comment, Like, Post
from inbox.models import Inbox, InboxComment
from followers.models import Follower
from remote_node.models import RemoteNode
from django.db.models import Q
import os
import requests
from util.main import url_remove_trailing_slash, standardize_url, removeQueryParamAll
from followers.serializers import FollowerSerializer
import remote_node.util
import util.main as util
from remote_node.util import get as get_remote

BASE_URL = os.environ.get('HOST_API_URL') + 'authors'

class CustomPagination(pagination.PageNumberPagination):
    """
    Custom pagination class to override the default page size
    """
    page_size = 5
    page_size_query_param = 'size'
    max_page_size = 100

class PostViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows posts to be viewed or edited.
    """
    queryset = models.Post.objects.all().order_by('-published')
    serializer_class = serializers.PostSerializer
    pagination_class = CustomPagination
    nodes = RemoteNode.objects.filter(disabled=False)

    def list(self, request, *args, **kwargs):
        """
        METHOD: GET
        Returns a list of posts by a single author
        URL: ://service/authors/{AUTHOR_ID}/posts
        """

        # remote nodes cannot access this resource
        util.log('PostViewSet/list', f'JSON: {json.dumps(request.data)}')
        util.log('PostViewSet/list', f'User: {request.user}')
        if not request.user.is_authenticated:
            return Response({"error": "You are not allowed to access this resource"}, status=status.HTTP_403_FORBIDDEN)

        post_list = {"type": "posts", "items": []}

        author_id = self.kwargs.get('author_id')
        if not author_id:
            util.log('PostViewSet/list', f"Author ID is None")
            return Response({"error": "Author ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # FIRST CHECK LOCAL DATABASE
        util.log('PostViewSet/list', f"Checking local database for user with ID: {self.kwargs.get('author_id')}")
        try:
            author = User.objects.get(pk=author_id, is_remote=False)
        except User.DoesNotExist:
            util.log('PostViewSet/list', f"Author {author_id} not found in the local database")
            author = None

        # Author found in the local database
        if author:
            # Get all posts by the author
            posts = models.Post.objects.filter(author=author).order_by('-published')
            util.log('PostViewSet/list', f"Posts: {posts}")

            # If the user is not authenticated, only return public posts
            if not request.user.is_authenticated:
                util.log('PostViewSet/list', f"User is not authenticated")
                posts = posts.filter(visibility='PUBLIC')
            
            # if the user is a node, return all posts
            elif request.user.is_node:
                util.log('PostViewSet/list', f"User is a node")
                pass

            # If the authenticated user is the author, retrn all posts
            elif request.user.id == author.id:
                pass

            # check if the authenticated user is following the author. If not, only return public posts
            elif not Follower.objects.filter(actor=request.user, object=author).exists():
                    util.log('PostViewSet/list', f"User is not following the author")
                    posts = posts.filter(visibility='PUBLIC')

            # If the authenticated user is following the author, check if the author is following the user
            # If the author is following the user, return public and friends posts
            else:
                util.log('PostViewSet/list', f"Testing if author is following the user")
                try:
                    user = User.objects.get(url=request.user.url.rstrip('/'))
                    # if the user is in the local database, check if the user is following the author
                    if Follower.objects.filter(actor=author, object=user).exists():
                        posts = posts.filter(Q(visibility='PUBLIC') | Q(visibility='FRIENDS'))
                    else:
                        posts = posts.filter(visibility='PUBLIC')
                except User.DoesNotExist:
                    # if the user is not in the local database make remote requests to check following
                    url = f'{request.user.url.rstrip("/")}/followers/{author.url.rstrip("/")}'
                    response = get_remote(url)
                    if not response or response.status_code != 200:
                        posts = posts.filter(visibility='PUBLIC')
                    else:
                        posts = posts.filter(Q(visibility='PUBLIC') | Q(visibility='FRIENDS'))

            # Return paginated posts
            paginator = self.pagination_class()
            pagination_posts = paginator.paginate_queryset(posts, request)
            serializer = serializers.PostSerializer(pagination_posts, many=True)

            post_list["items"] += serializer.data
            return Response(post_list, status=status.HTTP_200_OK)

        # IF ALL NOT IN QUERY PARAMS, RETURN 404
        if 'all' not in request.query_params:
            util.log('PostViewSet/list', f"All not in query params, returning 404")
            return Response({"error": "Author not found"}, status=status.HTTP_404_NOT_FOUND)
        

        # IF ALL IN QUERY PARAMS, CHECK REMOTE NODES
        util.log('PostViewSet/list', f"Searching for author {author_id} on remote nodes")
        url = request.build_absolute_uri().split('api/')[1].rstrip('/')
        url = removeQueryParamAll(url)

        for node in self.nodes:
            if node.displayName == 'local':
                continue
            try:
                request_url = remote_node.util.transform_url_for_node(
                    f"{node.url.rstrip('/')}/{url}",
                    node
                )
                auth_token = base64.b64encode(f"{node.displayName}:{node.password}".encode('ascii')).decode('ascii')
                headers = {
                    'Authorization': f'Basic {auth_token}',
                    'Content-Type': 'application/json'
                }
                if node.displayName == 'user':
                    # add slash before query parameters just for team HTTP
                    # we're adding this weird condition here instead of transform_url_for_node because
                    # we only want to add trailing slash for certain endpoints.
                    request_url = request_url.split('?')[0]
                    request_url += '/'

                util.log('PostViewSet/list', f"Requesting posts from {node.nodeName}: {request_url}")
                response = requests.get(request_url, headers=headers)
                
                # If the response is successful, return the posts
                if response.status_code == 200:
                    return Response(response.json())
                else:
                    util.log('PostViewSet/list', f"{node.nodeName} returned status code: {response.status_code}")

            except requests.RequestException as e:
                util.log('PostViewSet/list', f"Error connecting to {node.nodeName}: {e}")

        # Author not found in the local database and remote nodes
        return Response({"error": "Author not found"}, status=status.HTTP_404_NOT_FOUND)

    def retrieve(self, request, author_id=None, pk=None):
        """
        METHOD: GET
        Returns a single post
        URL: ://service/authors/{AUTHOR_ID}/posts/{POST_ID}
        """
        # check if the user exists in the local database
        util.log('PostViewSet/retrieve', f"Author ID: {author_id}, Post ID: {pk}")
        if User.objects.filter(pk=author_id, is_remote=False).exists():
            try:
                post = models.Post.objects.get(pk=pk)
            except models.Post.DoesNotExist:
                return Response({"error": f"Post {pk} not found under author {author_id}"}, status=status.HTTP_404_NOT_FOUND)

            # Validate that the author of the post is the same as the author_id
            if post.author.id != author_id:
                util.log('PostViewSet/retrieve', f"User {author_id} is not the author of post {pk} (Author: {post.author.id})")
                return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)


            # Crazy if statement to implement (good luck deciphering it)
            # Cases where post is publicly viewable
            util.log('PostViewSet/retrieve', f"Post visibility: {post.visibility}")
            util.log('PostViewSet/retrieve', f"User: {request.user}" + f" Author ID: {author_id}")
            if (post.visibility in ['PUBLIC', 'UNLISTED'] or                # Anyone can view public or unlisted posts
                request.user.id == author_id or                             # The author can view their own posts
                (request.user.is_authenticated and request.user.is_node)):  # Nodes can view any post
                util.log('PostViewSet/retrieve', f"Post is publicly viewable or user is the author or a node")
                pass

            # Otherwise, the post is a 'FRIENDS' post, the user is not the author, and the user is not a node, or the user is not authenticated
            # The user must be following the author and the author must be following the user
            elif request.user.is_authenticated:
                util.log('PostViewSet/retrieve', f"Post is a friends post and user is not the author or a node but is authenticated")
                # if the user is not following the author, they cannot view the post
                if not Follower.objects.filter(actor=request.user, object=post.author).exists():
                    return Response({"error": "You are not authorized to view this post"}, 
                                    status=status.HTTP_401_UNAUTHORIZED)
                # if the author is not following the user, they cannot view the post
                # Try get the user from the local database
                try:
                    user = User.objects.get(url=request.user.url.rstrip('/'))
                    # Check if the author is following the user
                    if not Follower.objects.filter(actor=post.author, object=user).exists():
                        return Response({"error": "You are not authorized to view this post"}, 
                                        status=status.HTTP_401_UNAUTHORIZED)
                # If the user is not in the local database, make a remote request to check following
                except User.DoesNotExist:
                    url = f'{request.user.url.rstrip("/")}/followers/{post.author.url.rstrip("/")}'
                    response = get_remote(url)
                    if not response or response.status_code != 200:
                        return Response({"error": "You are not authorized to view this post"}, 
                                        status=status.HTTP_401_UNAUTHORIZED)

            else:
                util.log("PostViewSet/retrieve", f"User is not authenticated")
                return Response({"error": "You are not authorized to view this post"}, 
                                status=status.HTTP_401_UNAUTHORIZED)

            serializer = serializers.PostSerializer(post)
            # add a type field with the value "post"
            post_data = serializer.data
            return Response(post_data, status=status.HTTP_200_OK)
        
        if 'all' not in request.query_params:
            return Response({"error": "Author not found"}, status=status.HTTP_404_NOT_FOUND)

        url = request.build_absolute_uri().split('api/')[1].rstrip('/')
        url = removeQueryParamAll(url)

        for node in self.nodes:
            if node.displayName == 'local':
                continue

            try:
                request_url = remote_node.util.transform_url_for_node(
                    f"{node.url.rstrip('/')}/{url}",
                    node
                )
                auth_token = base64.b64encode(f"{node.displayName}:{node.password}".encode('ascii')).decode('ascii')
                headers = {
                    'Authorization': f'Basic {auth_token}',
                    'Content-Type': 'application/json'
                }
                if node.displayName == 'user':
                    # add slash for team HTTP only for this endpoint
                    request_url = request_url.split('?')[0]
                    request_url += '/'
                response = requests.get(request_url, headers=headers)
                if response.status_code == 200:
                    return Response(response.json())
                else:
                    util.log('PostViewSet/retrieve', f"Failed to connect to {node.nodeName}. Status code: {response.status_code}")
            except requests.RequestException as e:
                util.log('PostViewSet/retrieve', f"Error connecting to {node.nodeName}: {e}")


        return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)

    def create(self, request, *args, **kwargs):
        '''
        METHOD: POST
        Creates a new post
        URL: ://service/authors/{AUTHOR_ID}/posts
        '''
        # only authenticated user of that account can create a post
        util.log('PostViewSet/create', f'User: {request.user}')

        if not request.user.is_authenticated:
            util.log('PostViewSet/create', f'User not authenticated')
            return Response({"error": "You are not authorized to create a post"}, status=status.HTTP_401_UNAUTHORIZED)
        if request.user.is_node:
            util.log('PostViewSet/create', f'User is a node')
            return Response({"error": "You are not allowed to access this resource"}, status=status.HTTP_403_FORBIDDEN)

        util.log('PostViewSet/create', f'Author ID: {self.kwargs.get("author_id")}')
        author_id = self.kwargs.get('author_id')
        if request.user.id != author_id:
            print(request.user)
            print(request.user.id, author_id)
            util.log('PostViewSet/create', f'User is not the author of the post')
            return Response({"error": "You are not authorized to create a post for this user"}, status=status.HTTP_401_UNAUTHORIZED)
        
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=request.user)
            headers = self.get_success_headers(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # get all user who follow this user, so we can send them a notification to their inbox
        follower_queryset = Follower.objects.filter(object=author_id)
        followers = FollowerSerializer(follower_queryset, many=True).data
        for follower in followers:
            try:
                # send a notification to the follower
                follower_url = follower['actor']
                author_url = f'{url_remove_trailing_slash(BASE_URL)}/{author_id}'
                util.log('PostViewSet/create', f'Sending new-post notif to follower: {follower_url}')
                url_post = f'{url_remove_trailing_slash(follower_url)}/posts'

                x = remote_node.util.post(
                    f"{url_remove_trailing_slash(follower_url)}/inbox", 
                    json={
                        "type": "inbox",
                        "author": author_url,
                        "items": [serializer.data['id']]
                    }
                )
                util.log('PostViewSet/create', f'Notification response: {x.status_code}')
            except Exception as e:
                util.log('PostViewSet/create', f'Error sending a new-post notif to follower: {e}')
                continue

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED, headers=headers
        )

    def destroy(self, request, *args, **kwargs):
        # only authenticated user of that account can delete a post
        if request.user.is_node:
            return Response({"error": "You are not allowed to access this resource"}, status=status.HTTP_403_FORBIDDEN)
        util.log('PostViewSet/destroy', f'User: {request.user.id}, Author ID: {self.kwargs.get("author_id")}')
        author_id = self.kwargs.get('author_id')
        if request.user.id != author_id:
            return Response({"error": "You are not authorized to delete a post for this user"}, status=status.HTTP_401_UNAUTHORIZED)
        return super().destroy(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        '''
        method: PUT
        Updates a post
        URL: ://service/authors/{AUTHOR_ID}/posts/{POST_ID}
        '''
        # only authenticated user of that account can update a post
        if request.user.is_node:
            return Response({"error": "You are not allowed to access this resource"}, status=status.HTTP_403_FORBIDDEN)
        util.log('PostViewSet/update', f'User: {request.user}')
        author_id = self.kwargs.get('author_id')
        if request.user.id != author_id:
            return Response({"error": "You are not authorized to update a post for this user"}, status=status.HTTP_401_UNAUTHORIZED)
        return super().update(request, *args, **kwargs)

    def public_posts(self, request, *args, **kwargs):
        """
        METHOD: GET
        Returns a list of public posts
        """
        util.log('PostViewSet/public_posts', f'User: {request.user} getting public posts')
        posts = models.Post.objects.filter(visibility='PUBLIC').order_by('-published')
        page = self.paginate_queryset(posts)
        serializer = serializers.PostSerializer(page, many=True)

        return Response({"type": "posts", "items": serializer.data}, status=status.HTTP_200_OK)
        

    def retrive_image(self, request, author_id=None, post_id=None):
        """
        METHOD: GET
        Returns the image of a single post
        """
        # check if author exists in the local database
        if User.objects.filter(pk=author_id).exists():

            # check if post exists in the local database
            try:
                post = models.Post.objects.get(pk=post_id)
            except models.Post.DoesNotExist:
                return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)

            # check if the post is a public image with the correct content type and author_id
            if post.visibility != 'PUBLIC':
                return Response({"error": "Post is not public"}, status=status.HTTP_400_BAD_REQUEST)
            if post.contentType not in ['image/png;base64', 'image/jpeg;base64', 'image/gif;base64']:
                return Response({"error": "Post is not an image"}, status=status.HTTP_400_BAD_REQUEST)
            if post.author.id != author_id:
                return Response({"error": f"User {author_id} does not have post {post_id}"}, status=status.HTTP_404_NOT_FOUND)
            image_data = base64.b64decode(post.content)
            return HttpResponse(image_data, content_type=post.contentType)

        # if not checking remote nodes, return 404
        if 'all' not in request.query_params:
            return Response({"error": "Author not found"}, status=status.HTTP_404_NOT_FOUND)

        # Try retrive image from remote nodes
        url = request.build_absolute_uri().split('api/')[1].rstrip('/')
        url = removeQueryParamAll(url)

        for node in self.nodes:
            if node.displayName == 'local':
                continue
            try:
                request_url = remote_node.util.transform_url_for_node(
                    f"{node.url.rstrip('/')}/{url}",
                    node
                )
                if node.displayName == 'lost':
                    util.log('FollowerViewSet/list', f'Adding trailing slash to {node.url} for team lost')
                    request_url += '/'
                auth_token = base64.b64encode(f"{node.displayName}:{node.password}".encode('ascii')).decode('ascii')
                headers = {
                    'Authorization': f'BASIC {auth_token}',
                    'Content-Type': 'application/json'
                }
                response = requests.get(request_url, headers=headers)
                if response.status_code == 200:
                    return Response(response.json())
                else:
                    util.log('PostViewSet/retrive_image', f"Failed to connect to {node.nodeName}. Status code: {response.status_code}")
            except requests.RequestException as e:
                util.log('PostViewSet/retrive_image', f"Error connecting to {node.nodeName}: {e}")
        return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)
    
    def retrive_friends_follwing(self, request, author_id=None):
        """
        METHOD: GET
        Returns a list of posts:
            - from authors that the user is following that are public
            - friends only post from authors that the user is following and vice versa
        """

        # get the author from the local database
        try:
            author = User.objects.get(pk=author_id)
        except User.DoesNotExist:
            return Response({"error": "Author not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # get the list of useres that the author is following
        following = Follower.objects.filter(actor=author)
        get_author_ids = [f.object.id for f in following]
        if len(get_author_ids) == 0:
            util.log('PostViewSet/retrive_friends_follwing', f"Author is not following anyone")
        else:
            util.log('PostViewSet/retrive_friends_follwing', f"Author is following {get_author_ids}")

        util.log('PostViewSet/retrive_friends_follwing', f"Checking for friends only posts")
        # check from the list of authors that the user is following, get the list of authors that are following the user
        friends = []
        for author in get_author_ids:
            # if current author is following the user and user is following the author, then add user to friends list
            if Follower.objects.filter(actor=author, object=author_id).exists():
                friends.append(Follower.objects.get(actor=author_id, object=author))
        # print("Friends: ", friends)
        get_friends_ids = []
        get_friends_ids = [f.object.id for f in friends]
        # take intersection of the two lists
        if len(get_friends_ids) == 0:
            util.log('PostViewSet/retrive_friends_follwing', f"Author has no friends")
        else:
            util.log('PostViewSet/retrive_friends_follwing', f"Authors friends: {get_friends_ids}")

        # get_friends_ids = list(set(get_author_ids) & set(get_friends_ids))
        # print("Friends: ", get_friends_ids)

        # get public posts from authors that the user is following, do not include the author's posts
        # for authors that are local
        posts_list = []
        for author in get_author_ids:
            # check if the author is a remote author
            if User.objects.filter(pk=author, is_remote=True).exists():
                # get the posts from the remote author remotely
                user = User.objects.get(pk=author)
                url = f"{user.url.rstrip('/')}/posts"
                if 'linkup' or 'lost' in url:
                    url += '/'
                response = get_remote(url)
                if response.status_code == 200:
                    for post in response.json()['items']:
                        if post['visibility'] == 'PUBLIC' and not 'Github Activity:' in post['title']:
                            posts_list.append(post)
            else:
                # title should not have 'Github Activity:' in it
                posts = models.Post.objects.filter(Q(author_id=author) & Q(visibility='PUBLIC') & ~Q(title__contains='Github Activity:')).order_by('-published')
                serializer = serializers.PostSerializer(posts, many=True)
                posts_list += serializer.data

        # get friends only posts from authors that the user is following and vice versa
        for author in get_friends_ids:
            # check if the author is a remote author
            if User.objects.filter(pk=author, is_remote=True).exists():
                # get the posts from the remote author remotely
                user = User.objects.get(pk=author)
                url = f"{user.url.rstrip('/')}/posts"
                if 'linkup' or 'lost' in url:
                    url += '/'
                response = get_remote(url)
                if response.status_code == 200:
                    for post in response.json()['items']:
                        if post['visibility'] == 'FRIENDS':
                            posts_list.append(post)
            else:
                posts = models.Post.objects.filter(Q(author_id=author) & Q(visibility='FRIENDS')).order_by('-published')
                serializer = serializers.PostSerializer(posts, many=True)
                posts_list += serializer.data

        util.log('PostViewSet/retrive_friends_follwing', f"Posts: \n{json.dumps(posts_list, indent=4)}")
        # paginate the posts
        posts_list = sorted(posts_list, key=lambda x: x['published'], reverse=True)
        paginator = self.pagination_class()
        pagination_posts = paginator.paginate_queryset(posts_list, request)
        return Response({"type": "posts", "items": pagination_posts}, status=status.HTTP_200_OK)

class CommentViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows comments to be viewed or edited.
    """
    queryset = models.Comment.objects.all().order_by('-published')
    serializer_class = serializers.CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = CustomPagination
    nodes = RemoteNode.objects.filter(disabled=False)

    def list(self, request, author_id=None, post_id=None):
        """
        METHOD: GET
        Returns a list of comments for a single post
        Defaults to the first 5 comments sorted by published date, newest first
        """
        comment_list = {"type": "comments", "items": []}
        # check if the comments exist in the local database
        if models.Comment.objects.filter(post_id=post_id).exists():
            comments = models.Comment.objects.filter(post_id=post_id).order_by('-published')

            if comments.first().post.author.id != author_id:
                return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)

            page = self.paginate_queryset(comments)
            serializer = serializers.CommentSerializer(page, many=True)
            comment_list["items"] = serializer.data

            try:
                if request.user.is_authenticated and request.user.displayName == 'attack-and-lost':
                    # make "items" key "comments"
                    util.log('CommentViewSet/list', f"Changing 'items' key to 'comments' for team lost")
                    comment_list["comments"] = comment_list.pop("items")
                    print(json.dumps(comment_list, indent=4))
                    return Response(comment_list, status=status.HTTP_200_OK)
            except Exception as e:
                util.log('CommentViewSet/list', f"Error changing 'items' key to 'comments' for team lost: {e}. Returning normal response")

            return Response(comment_list, status=status.HTTP_200_OK)

        if 'all' not in request.query_params:
            return Response(comment_list, status=status.HTTP_200_OK)

        url = request.build_absolute_uri().split('api/')[1].rstrip('/')
        url = removeQueryParamAll(url)

        for node in self.nodes:
            if node.displayName == 'local':
                continue
            try:
                request_url = remote_node.util.transform_url_for_node(
                    f"{node.url.rstrip('/')}/{url}",
                    node
                )
                auth_token = base64.b64encode(f"{node.displayName}:{node.password}".encode('ascii')).decode('ascii')
                headers = {
                    'Authorization': f'Basic {auth_token}',
                    'Content-Type': 'application/json'
                }
                response = requests.get(request_url, headers=headers)
                util.log('CommentViewSet/list', f"{node.nodeName} returned status code: {response.status_code}")
                if response.status_code == 200:
                    return Response(response.json())
            except requests.RequestException as e:
                util.log('CommentViewSet/list', f"Error connecting to {node.nodeName}: {e}")
        return Response(comment_list, status=status.HTTP_200_OK)
    
    def retrieve(self, request, author_id=None, post_id=None, pk=None):
        """
        METHOD: GET
        Returns a single comment
        """
        # Check if the comment exists in the local database
        if models.Comment.objects.filter(pk=pk).exists():
            comment = models.Comment.objects.get(pk=pk)

            if comment.post.id != post_id:
                util.log('CommentViewSet/retrieve', f"Post {post_id} not found when retrieving comment")
                return Response({"error": f"Post {post_id} not found when retrieving comment"}, status=status.HTTP_404_NOT_FOUND)
            if comment.post.author.id != author_id:
                util.log('CommentViewSet/retrieve', f"Author {author_id} is not the author of post {post_id}")
                return Response({"error": f"Author {author_id} is not the author of post {post_id}"}, status=status.HTTP_404_NOT_FOUND)

            serializer = serializers.CommentSerializer(comment)

            # add a type field with the value "comment"
            comment_data = serializer.data
            return Response(comment_data)
        
        if 'all' not in request.query_params:
            return Response({"error": "Comment not found"}, status=status.HTTP_404_NOT_FOUND)

        url = request.build_absolute_uri().split('api/')[1].rstrip('/')
        url = removeQueryParamAll(url)

        for node in self.nodes:
            if node.displayName == 'local':
                continue
            try:
                request_url = remote_node.util.transform_url_for_node(
                    f"{node.url.rstrip('/')}/{url}",
                    node
                )
                auth_token = base64.b64encode(f"{node.displayName}:{node.password}".encode('ascii')).decode('ascii')
                headers = {
                    'Authorization': f'BASIC {auth_token}',
                    'Content-Type': 'application/json'
                }
                response = requests.get(request_url, headers=headers)
                util.log('CommentViewSet/retrieve', f"{node.nodeName} returned status code: {response.status_code}")
                if response.status_code == 200:
                    return Response(response.json())
            except requests.RequestException as e:
                util.log('CommentViewSet/retrieve', f"Error connecting to {node.nodeName}: {e}")
        return Response({"error": "Comment not found"}, status=status.HTTP_404_NOT_FOUND)

    def get_queryset(self):
        """
        METHOD: GET
        Returns a list of comments for a single post
        """
        post_id = self.kwargs.get('post_id')
        return Comment.objects.filter(post_id=post_id)

    def create(self, request, *args, **kwargs):
        """
        METHOD: POST
        Creates a new comment for a post
        """
        # if the post is a public post, anyone can comment on it
        # if the post is a friends post, only friends can comment on it
        # if the post is an unlisted post, only the author can comment on it

        if request.user.is_node:
            return Response({"error": "You are not allowed to access this resource"}, status=status.HTTP_403_FORBIDDEN)

        post_id = self.kwargs.get('post_id')
        post = None
        util.log('CommentViewSet/create', f'Post ID to comment on: {post_id}')
        try:
            post = models.Post.objects.get(pk=post_id)
        except models.Post.DoesNotExist:
            util.log('CommentViewSet/create', f"Post {post_id} not found locally")
        
        # check for post on remote nodes if it exists create a comment on it
        if not post:
            response = self.create_remote_comment(request, post_id)
            if response.status_code == 200 or response.status_code == 201:
                return response
            else:
                return Response({"error": "Post not found"}, status=response.status_code)

        if post.visibility == 'UNLISTED' and request.user.id != post.author_id:
            return Response({"error": "You are not authorized to comment on this post"}, status=status.HTTP_401_UNAUTHORIZED)

        if post.visibility == 'FRIENDS':
            #check if actor is following the object and vice versa
            try:
                user = User.objects.get(url=request.user.url)
                if not Follower.objects.filter(actor=post.author, object=user).exists():
                    return Response({"error": "You are not authorized to comment on this post"}, status=status.HTTP_401_UNAUTHORIZED)
                if not Follower.objects.filter(actor=user, object=post.author).exists():
                    return Response({"error": "You are not authorized to comment on this post"}, status=status.HTTP_401_UNAUTHORIZED)
            except User.DoesNotExist:
                url = f'{request.user.url.rstrip("/")}/followers/{post.author.url.rstrip("/")}'
                response = get_remote(url)
                if not response or response.status_code != 200:
                    return Response({"error": "You are not authorized to comment on this post"}, status=status.HTTP_401_UNAUTHORIZED)
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = serializer.save(post=post, author=request.user)
        headers = self.get_success_headers(serializer.data)
        util.log('CommentViewSet/create', f"Comment successfully created: {comment}")

        # send notification to the author of the post
        try:
            util.log('CommentViewSet/create', f'Sending notification to author of post')
            inbox_comment = InboxComment.objects.create(
                commentUrl= comment.url,
                author=request.user.url,
            )
            inbox_comment.save()
            inbox_item = Inbox.objects.create(
                type="comment",
                comment=inbox_comment,
                author=comment.post.author
            )
            inbox_item.save()
        except Exception as e:
            util.log('CommentViewSet/create', f'Error sending a new-comment notif to author inbox: {e}')

        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def create_remote_comment(self, request, post_id):
        """
        Create a comment on a post that is not found locally
        """
        author_id = request.user.id
        url = request.build_absolute_uri().split('api/')[1].rstrip('/')
        url = removeQueryParamAll(url)
        print("> URL:", url)

        for node in self.nodes:
            if node.displayName == 'local':
                continue
            try:
                request_url = f"{node.url.rstrip('/')}/{url}"
                request_url = remote_node.util.transform_url_for_node(
                    request_url.split('/comments')[0],
                    node
                )
                util.log('CommentViewSet/create_remote_comment', f"Request URL: {request_url}")
                auth_token = base64.b64encode(f"{node.displayName}:{node.password}".encode('ascii')).decode('ascii')
                headers = {
                    'Authorization': f'Basic {auth_token}',
                    'Content-Type': 'application/json'
                }
                response = requests.get(request_url, headers=headers)
                if response.status_code == 200:
                    author = UserSerializer(request.user).data
                    if node.displayName == 'teamattack@email.com':
                        comment_data = {
                            "type": "comment",
                            "author": author,
                            "comment": request.data['comment'],
                            "contentType": 'text/markdown',
                            "published": datetime.datetime.now().isoformat(),
                            # "id": response.json()['id'],
                            "post": {"id": response.json()['id']}
                        }
                    else:
                        comment_data = {
                            "type": "comment",
                            "author": author,
                            "comment": request.data['comment'],
                            "contentType": 'text/markdown',
                            "published": datetime.datetime.now().isoformat(),
                            "id": response.json()['id']
                        }

                    inbox_data = {
                        "type": "inbox",
                        "author": response.json()['author']['id'],
                        "items": [comment_data]
                    }
                    # request to /inbox
                    url = f"{node.url.rstrip('/')}/authors/{response.json()['author']['id'].split('/')[-1]}/inbox"
                    if 'lost' in url:
                        url += '/'
                    util.log('CommentViewSet/create_remote_comment', f"Sending comment to {url}")
                    util.log('CommentViewSet/create_remote_comment', f"Data: {json.dumps(inbox_data, indent=4)}")
                    response = requests.post(url, headers=headers, json=inbox_data)
                    util.log('CommentViewSet/create_remote_comment', f"Response: {response.status_code}")
                    util.log('CommentViewSet/create_remote_comment', f"Response: {response.json()}")
                    return Response(response)
            except requests.RequestException as e:
                util.log('CommentViewSet/create_remote_comment', f"Error connecting to {node.nodeName}: {e}")
        return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)


class LikeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows likes to be viewed or edited.
    """
    queryset = Like.objects.all().order_by('-published')
    serializer_class = serializers.LikeSerializer
    nodes = RemoteNode.objects.filter(disabled=False)

    def list(self, request:Request, author_id:str, post_id:str, comment_id:str = None) -> Response:
        """
        METHOD: GET
        URL: ://service/authors/{AUTHOR_ID}/posts/{POST_ID}/likes
             ://service/authors/{AUTHOR_ID}/posts/{POST_ID}/comments/{COMMENT_ID}/likes
        Returns a list of likes from other authors on AUTHOR_ID's post (POST_ID) or comment
        """

        # Get the post or comment object locally
        try:
            author = User.objects.get(pk=author_id)
            util.log('LikeViewSet/list', f"Author {author.displayName} ({author_id}) found locally.")
            if comment_id:
                object = Comment.objects.get(pk=comment_id)
                util.log('LikeViewSet/list', f"Comment {comment_id} found locally.")
            else:
                object = Post.objects.get(pk=post_id)
                util.log('LikeViewSet/list', f"Post {post_id} found locally.")
        except User.DoesNotExist:
            util.log('LikeViewSet/list', f"Author {author_id} not found locally.")
        except Post.DoesNotExist:
            util.log('LikeViewSet/list', f"Post {post_id} not found locally.")
        except Comment.DoesNotExist:
            util.log('LikeViewSet/list', f"Comment {comment_id} not found locally.")
        else:

            # Verify the object is the author's
            try:
                # If the object is a comment, verify the comment is on the author's post
                if comment_id:
                    assert object.post.author.id == author_id
                    assert object.post.id == post_id
                else:
                    assert object.author.id == author_id
            except AssertionError:
                if comment_id:
                    util.log('LikeViewSet/list', f"Comment {comment_id} not found on Post {post_id} by Author {author_id}")
                    util.log('LikeViewSet/list', f"Post author: {object.post.author.id}, input author: {author_id}")
                    util.log('LikeViewSet/list', f"Post ID: {object.post.id}, input post ID: {post_id}")
                    return Response({"error": f"Object not found: Comment {comment_id} not found on Post {post_id} by Author {author_id}"}, 
                            status=status.HTTP_404_NOT_FOUND)
                else:
                    util.log('LikeViewSet/list', f"Post {post_id} not found by Author {author_id}")
                    util.log('LikeViewSet/list', f"Post author: {object.author.id}, input author: {author_id}")
                    return Response({"error": f"Object not found: Post {post_id} not found by Author {author_id}"},
                            status=status.HTTP_404_NOT_FOUND)

            # Get the likes
            likes = Like.objects.filter(object=object.url.rstrip('/')).order_by('-published')
            util.log('LikeViewSet/list', f"Found {likes.count()} likes on {object.url} by {author_id}.")
            serializer = serializers.LikeSerializer(likes, many=True)
            util.log('LikeViewSet/list', f"Serialized likes: {serializer.data}")
            return Response({"type": "likes", "items": serializer.data}, status=status.HTTP_200_OK)

        if 'all' not in request.query_params:
            return Response({"error": "Likes not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Get the likes from remote nodes
        url = request.build_absolute_uri().split('api/')[1]
        url = removeQueryParamAll(url)

        for node in self.nodes:
            if node.displayName == 'local':
                continue

            try:
                request_url = remote_node.util.transform_url_for_node(
                    f"{node.url.rstrip('/')}/{url}",
                    node
                )
                auth_token = base64.b64encode(f'{node.displayName}:{node.password}'.encode('ascii')).decode('ascii')
                headers = {
                    'Authorization': f'Basic {auth_token}',
                    'Content-Type': 'application/json'
                }
                util.log('LikeViewSet/list', f"Requesting likes from {node.nodeName}: {request_url}")
                response = requests.get(request_url, headers=headers)
                if response.status_code == 200:
                    return Response(response.json())
                else:
                    util.log('LikeViewSet/list', f"{node.nodeName} returned status code: {response.status_code}")
            except requests.RequestException as e:
                util.log('LikeViewSet/list', f"Error requesting likes from {node.nodeName}: {e}")

        return Response({"error": "Likes not found for requested object"}, status=status.HTTP_404_NOT_FOUND)
