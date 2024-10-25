import json
from django.shortcuts import render
from rest_framework import viewsets, permissions, pagination, status
from rest_framework.response import Response
from restapi.models import User
from restapi.serializers import UserSerializer
from post.models import Post, Comment, Like
from post.serializers import PostSerializer, LikeSerializer
from followers.serializers import FollowerSerializer
from inbox import models, serializers
from followers.models import Follower
from rest_framework.decorators import action
from remote_node.models import RemoteNode
import os
import requests
import util.main as util
import remote_node.util
import base64
import inbox.util



BASE_URL = os.environ.get('HOST_API_URL') + 'authors'

class CustomPagination(pagination.PageNumberPagination):
    """
    Custom pagination class to override the default page size
    """
    page_size = 5
    page_size_query_param = 'size'
    max_page_size = 100
    nodes = RemoteNode.objects.filter(disabled=False)

class InboxViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows posts to be viewed or edited.
    """
    queryset = models.Inbox.objects.all().order_by('-published')
    serializer_class = serializers.InboxSerializer
    pagination_class = CustomPagination
    nodes = RemoteNode.objects.filter(disabled=False)

    def list(self, request, *args, **kwargs):
        """
        METHOD: GET
        Returns the inbox for a specific user
        """
        author_id = self.kwargs.get('author_id')
        author_url = util.standardize_url(f'{BASE_URL}/{author_id}')
        try:
            author_json = remote_node.util.get(author_url).json()
        except requests.exceptions.RequestException as e:
            return Response({"error": f"Author {author_id} not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # if the user is in another node, just request from that node and return the response
        try:
            author_url_id = author_json.get('id')
            if not author_url_id.startswith(BASE_URL):
                # forward request to the remote node
                author_inbox_url = f'{util.url_remove_trailing_slash(author_url_id)}/inbox'
                util.log('InboxViewSet/list', f'Author {author_id} is on a remote node. Author URL: {author_url_id}. GET {author_inbox_url}')
                util.log('InboxViewSet/list', print(json.dumps(request.data, indent=2)))

                response = remote_node.util.get(author_inbox_url)
                util.log('InboxViewSet/list', f'Response from remote node {author_inbox_url}: {response.status_code}')
                return Response(response.json(), status=response.status_code)
        except Exception as e:
            return Response({"error": f"Error forwarding author inbox for {author_id}, {e}"}, status=status.HTTP_404_NOT_FOUND)
        
        # else, the user is on the local node
        try:
            author = User.objects.get(pk=self.kwargs.get('author_id'))
            inboxes = models.Inbox.objects.filter(author=author).order_by('-published')
        except User.DoesNotExist:
            return Response({"error": "Author does not exist"}, status=status.HTTP_404_NOT_FOUND)

        paginator = self.pagination_class()
        pagination_posts = paginator.paginate_queryset(inboxes, request)
        serializer = serializers.InboxSerializer(pagination_posts, many=True)

        for inbox in serializer.data:
            # deserialize inbox data here
            pass 

        posts_list = {
            "type": "inbox",
            "author": f"{BASE_URL}/{author.id}",
            "items": serializer.data
        }

        return Response(posts_list)
    


    def create(self, request, author_id, *args, **kwargs):
        '''
        method: POST
        Creates a new inbox object to the author's inbox
        '''
        # Incoming url like {local_url}/author/{author_url}/inbox
        # Need to convert to {remote_url}/author/{author_url}/inbox/ if author is on a remote node
        #       where remote_url is the url for the node that the author is on
        #             author_url is a uuid. Need to find the author's remote url

        # Example:
        #   - incoming url      - http://local.com/author/ab2d31-4cab-82a3-decab6c6b2ee/inbox/
        #   - author_id         - ab2d31-4cab-82a3-decab6c6b2ee
        #   - author_node_url   - http://remote.com/


        author_url = util.standardize_url(f'{BASE_URL}/{author_id}')
        if 'all' in request.query_params:
            # if ?all is in query params, we want to search for remote authors as well
            # thus, in the author URL we look for we add a ?all query param
            author_url += '?all'

        try:
            util.log('InboxViewSet/create', f'Retrieving author data: {author_url}')
            author_json = remote_node.util.get(author_url).json()
        except requests.exceptions.RequestException as e:
            util.log('InboxViewSet/create', f'Error retrieving author data: {e}')
            return Response({"error": f"Author {author_id} not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            author_url_id = author_json.get('id')
            if not author_url_id.startswith(BASE_URL):
                # forward request to the remote node
                author_inbox_url = f'{util.url_remove_trailing_slash(author_url_id)}/inbox'
                util.log('InboxViewSet/create', f'Author {author_id} is on a remote node. Author URL: {author_url_id}. Forwarding to {author_inbox_url}')

                # update "author" field
                request.data['author'] = author_url_id.rstrip('/')
                print(json.dumps(request.data, indent=2))

                # if the inbox type if a follow, we also want to make a copy of the remote user we are following
                # this is how Team Snack and HTTP work
                try:
                    if request.data.get('items')[0].get('type').lower() == 'follow':
                        follow_data = request.data.get('items')[0]
                        util.log('InboxViewSet/create', f'Copying remote author when doing a follow request: {json.dumps(follow_data.get("object"), indent=2)}')
                        author_followed = inbox.util.retrieve_or_copy_author(follow_data.get('object'))
                        util.log('InboxViewSet/create', f'Copied remote author: {author_followed} that is being followed.')
                        author_following = inbox.util.retrieve_or_copy_author(follow_data.get('actor'))
                        util.log('InboxViewSet/create', f'Got author: {author_following} that is doing the follow reuest.')
                        util.log('InboxViewSet/create', f'Assuming following passes - making Follow object.')
                        follow = FollowerSerializer(data={'actor': author_following.id, 'object': author_followed.id})
                        if follow.is_valid():
                            follow.save(actor=author_following, object=author_followed)
                            util.log('InboxViewSet/create', f'Follow object saved: {follow.data}')
                        else:
                            util.log('InboxViewSet/create', f'Follow object is not valid: {follow.errors}. skipping')
                    else:
                        util.log('InboxViewSet/create', f'Not a follow request. Skipping copying remote author.')
                except Exception as e:
                    util.log('InboxViewSet/create', f'Error copying remote author when doing a follow request: {e}')
                    return Response({"error": f"Error copying remote author: {e}"}, status=status.HTTP_400_BAD_REQUEST)

                response = remote_node.util.post(author_inbox_url, json=request.data)
                util.log('InboxViewSet/create', f'Response from remote node {author_inbox_url}: {response.status_code}')
                try:
                    return Response(response.json(), status=response.status_code)
                except:
                    # if the response is not JSON, return the response as is
                    return response
            
        except Exception as e:
            util.log('InboxViewSet/create', f'Error forwarding author inbox for {author_id}, {e}')
            return Response({"error": f"Error forwarding author inbox for {author_id}"}, status=status.HTTP_404_NOT_FOUND)

        # Otherwise author is on the local node
        try:
            inbox_user = User.objects.get(pk=author_id)
        except User.DoesNotExist:
            return Response({"error": "Author does not exist"}, status=status.HTTP_404_NOT_FOUND)

        try:
            inbox_data = request.data.get('items')[0]
            inbox_type = inbox_data.get('type').lower()
        except:
            return Response({"error": "Invalid inbox data. Remember to wrap Inbox items!"}, status=status.HTTP_400_BAD_REQUEST)

        util.log('InboxViewSet/create', f'Adding inbox data to user {inbox_user.displayName} inbox with type {inbox_type}')

        if inbox_type == 'post':
            # get ID of post
            post_id = util.standardize_url(inbox_data.get('id'))
            data = {'post_id': post_id}
            util.log('InboxViewSet/create', f'Post data (just the URL): {data}')
            inbox_post = serializers.InboxPostSerializer(data=data)
            if inbox_post.is_valid():
                inbox_post.save(post_id=post_id)
                inbox_model = models.Inbox.objects.create(
                    author=inbox_user,
                    type=inbox_type,
                    post=inbox_post.instance
                )
                inbox_data = serializers.InboxSerializer(inbox_model).data
                util.log('InboxViewSet/create', f'Inbox data: {inbox_data}')
                return Response(inbox_data, status=status.HTTP_201_CREATED)
            else:
                util.log('InboxViewSet/create', 'Post is not valid!')
                return Response(inbox_post.errors, status=status.HTTP_400_BAD_REQUEST)

        elif inbox_type == 'follow':
            # check if the author that is being followed exists locally. If not, this is the wrong server to send this to
            # we only care about people following our local users.
            object_id = util.id_from_url(inbox_data.get('object').get('id'))
            if not User.objects.filter(id=author_id, is_remote=False, is_node=False).exists():
                return Response({"error": "Author does not exist locally"}, status=status.HTTP_404_NOT_FOUND)
            object = User.objects.get(pk=object_id)

            # the person who is following our user
            # if it is remote, make a copy
            actor = inbox.util.retrieve_or_copy_author(inbox_data.get('actor'))
            follow = serializers.FollowRequestSerializer(data=inbox_data)
            if follow.is_valid():
                follow.save(actor=actor, object=object)
                inbox_model = models.Inbox.objects.create(
                    author=inbox_user,
                    type=inbox_type,
                    follow=follow.instance
                )
                inbox_ret = serializers.InboxSerializer(inbox_model)
                return Response(inbox_ret.data, status=status.HTTP_201_CREATED)
            else:
                util.log('InboxViewSet/create', 'Follow is not valid!')
                util.log('InboxViewSet/create', follow.errors)
                return Response(follow.errors, status=status.HTTP_400_BAD_REQUEST)

        elif inbox_type == 'comment':
            util.log('InboxViewSet/create/comment', f'\n\n COMMENT REQUEST RECEIVED FROM {author_id} \n\n')
            # author
            author_url = inbox_data.get('author').get('id')

            # Get the post being commented on
            try:
                # get the post URL
                post_url = inbox_data.get('id') or inbox_data.get('post').get('id')
                assert post_url, "Post ID is required"
                util.log('InboxViewSet/create/comment', f'Post URL: {post_url}')

                # get the post ID
                post_id = util.id_from_url(post_url)
                util.log('InboxViewSet/create/comment', f'Post ID: {post_id}')

                # get the post object in the database
                post = Post.objects.get(pk=post_id)
                assert post.author.id == author_id, f"Post {post_id} does not belong to author {author_id}"

            except AssertionError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            except Post.DoesNotExist:
                return Response({"error": "Post does not exist"}, status=status.HTTP_404_NOT_FOUND)

            # Get the user that is commenting on the post
            comment_author_data = inbox_data.get('author')
            if not comment_author_data:
                return Response({"error": "Comment author is required"}, status=status.HTTP_400_BAD_REQUEST)
            util.log('InboxViewSet/create/comment', f'Comment author: {comment_author_data}')
            comment_author = inbox.util.retrieve_or_copy_author(comment_author_data)

            # Create the comment object
            util.log('InboxViewSet/create/comment', f'INBOX DATA: {inbox_data}')
            comment_text = inbox_data.get('comment')
            if not comment_text:
                return Response({"error": "Comment content is required"}, status=status.HTTP_400_BAD_REQUEST)
            

            util.log('InboxViewSet/create/comment', f'Creating comment by author {author_id} on post {post_id}: {comment_text}')
            comment = Comment.objects.create(
                author = comment_author,
                post = post,
                comment = comment_text,
                published = inbox_data.get('published'),
                contentType = inbox_data.get('contentType') or 'text/plain'
            )
            util.log('InboxViewSet/create/comment', f'Comment created: {comment}')

            # Create the inbox object
            comment_url = comment.url

            util.log('InboxViewSet/create/comment', f'Author URL: {author_url}, Comment URL: {comment_url}')
            inbox_comment = serializers.InboxCommentSerializer(data={'commentUrl': comment_url, 'author': author_url})
            if inbox_comment.is_valid():
                # somehow the comment_url is null without this? absolutely no idea why
                inbox_comment.save(commentUrl=comment_url)
                inbox_model = models.Inbox.objects.create(
                    author=inbox_user,
                    type=inbox_type,
                    comment=inbox_comment.instance
                )
                inbox_ret = serializers.InboxSerializer(inbox_model)
                return Response(inbox_ret.data, status=status.HTTP_201_CREATED)
            else:
                util.log('InboxViewSet/create/comment', 'Comment is not valid!')
                return Response(inbox_comment.errors, status=status.HTTP_400_BAD_REQUEST)

        elif inbox_type == 'like':
            # author
            try:
                author_url = util.standardize_url(inbox_data.get('author').get('url'))
                object_url = util.standardize_url(inbox_data.get('object'))

                likes = models.Like.objects.filter(author=author_url, object=object_url)

                # if like already exists, 400
                if likes.exists():
                    util.log('InboxViewSet/create', f'User already liked this object')
                    return Response({"error": "User already liked this object"}, status=status.HTTP_400_BAD_REQUEST)

                util.log('InboxViewSet/create', f'Author URL: {author_url}, Object URL: {object_url}')
                inbox_like = LikeSerializer(data={'author': author_url, 'object': object_url})
                if inbox_like.is_valid():
                    inbox_like.save()
                    inbox_model = models.Inbox.objects.create(
                        author=inbox_user,
                        type=inbox_type,
                        like=inbox_like.instance
                    )
                    util.log('InboxViewSet/create', f'Inbox Model: {inbox_model}, Inbox Like: {inbox_like.data}')
                    inbox_data = serializers.InboxSerializer(inbox_model).data

                    return Response(inbox_data, status=status.HTTP_201_CREATED)
                else:
                    util.log('InboxViewSet/create', f'Like couldn\'t be serialized: {inbox_like.errors}')
                    return Response(inbox_like.errors, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                util.log('InboxViewSet/create', f'Error processing inbox like: {e}')
                return Response({"error": f"Error processing inbox like: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
        elif inbox_type == 'unfollow':
            # team HTTP and Lost uses the unfollow type to remove followers
            actor_id = util.id_from_url(inbox_data.get('actor').get('id'))
            object_id = util.id_from_url(inbox_data.get('object').get('id'))

            util.log('InboxViewSet/create/unfollow', f'Unfollow request received from {actor_id} to {object_id}')

            # get the actor and object
            try:
                actor = User.objects.get(pk=actor_id)
                object = User.objects.get(pk=object_id)
            except User.DoesNotExist:
                util.log('InboxViewSet/create/unfollow', f'Actor or object does not exist')
                return Response({"error": "Actor or object does not exist"}, status=status.HTTP_404_NOT_FOUND)

            # delete the follow object
            try:
                follow = Follower.objects.get(actor=actor, object=object)
                follow.delete()
                util.log('InboxViewSet/create/unfollow', f'Follow object deleted')
                return Response({"success": "Follow object deleted"}, status=status.HTTP_204_NO_CONTENT)
            except Follower.DoesNotExist:
                util.log('InboxViewSet/create/unfollow', f'Follow object does not exist')
                return Response({"error": "Follow object does not exist"}, status=status.HTTP_404_NOT_FOUND)

        else:
            # other types of inboxes
            return Response({"error": "Invalid inbox type"}, status=status.HTTP_400_BAD_REQUEST)

    # the destroy viewset function only works when you specify a specific inbox item
    # so we have to define out own delete method to delete all inboxes for a user
    @action(methods=["DELETE"], detail=False)
    def delete(self, request, *args, **kwargs):
        '''
        Deletes all inboxes for a user
        '''
        # only authenticated user of that account can delete the inbox
        author_id = self.kwargs.get('author_id')
        util.log('InboxViewSet/delete', f'Deleting all inboxes for author {author_id}')
        if request.user.id != author_id:
            return Response({"error": "You are not authorized to delete a post for this user"}, status=status.HTTP_401_UNAUTHORIZED)
        
        # remove all inboxes where the author is the user
        models.Inbox.objects.filter(author=author_id).delete()
        return Response({"success": "All inboxes deleted"}, status=status.HTTP_204_NO_CONTENT)
