from rest_framework import serializers
from inbox import models
from post import serializers as post_serializers
from restapi import models as restapi_models
from restapi import serializers as restapi_serializers
import util.main as util
import json 
import requests
import remote_node.util

class FollowRequestSerializer(serializers.ModelSerializer):
    '''
    ### FOLLOW REQUEST SERIALIZER
    Serializes a follow request
    '''
    actor = restapi_serializers.UserSerializer(read_only=True)
    object = restapi_serializers.UserSerializer(read_only=True)
    class Meta:
        model = models.FollowRequest
        fields = ['id', 'actor', 'object']


class InboxCommentSerializer(serializers.ModelSerializer):
    '''
    ### COMMENT SERIALIZER

    Serializes a comment for an inbox (no post relation)
    '''
    class Meta:
        model = models.InboxComment
        fields = ['id', 'commentUrl', 'author']


class InboxPostSerializer(serializers.ModelSerializer):
    '''
    ### POST SERIALIZER
    Serializes a post for an inbox
    '''
    class Meta:
        model = models.InboxPost
        fields = ['post_id']


class InboxSerializer(serializers.ModelSerializer):
    '''
    ### INBOX SERIALIZER
    Serializes the inbox for a user
    '''
    author = post_serializers.UserSerializer(read_only=True)
    post = InboxPostSerializer(read_only=True)
    like = post_serializers.LikeSerializer(read_only=True)
    comment = InboxCommentSerializer(read_only=True)
    follow = FollowRequestSerializer(read_only=True)

    class Meta:
        model = models.Inbox
        fields = ['id', 'author', 'type', 'post', 'like', 'comment', 'follow']
    
    def to_representation(self, instance):
        '''
        Converts an Inbox model to a dictionary representation
        '''
        return_data = {
            'type': instance.type,
        }

        if instance.type == 'post':
            data = InboxPostSerializer(instance.post).data
            post_url = data.get('post_id')
            util.log('InboxSerializer', f'Fetching post from {post_url}')
            response = remote_node.util.get(post_url)
            if response.status_code == 404:
                util.log('InboxSerializer', f'Post not found! {post_url}')
                return_data['post'] = {'error': 'Post not found'}
            else:
                post_data = response.json()
                return_data = return_data | post_data
        elif instance.type == 'follow':
            data = FollowRequestSerializer(instance.follow).data
            print('InboxSerializer', f'Follow data {data}')
            return_data['actor'] = data.get('actor')
            return_data['object'] = data.get('object')
            return_data['summary'] = f'{return_data["actor"]["displayName"]} wants to follow {return_data["object"]["displayName"]}'
        elif instance.type == 'like':
            return post_serializers.LikeSerializer(instance.like).data
        elif instance.type == 'comment':
            data = InboxCommentSerializer(instance.comment).data
            util.log('InboxSerializer/comment', f'Inbox Comment data {data}')
            author_url = data.get('author')
            object_url = data.get('commentUrl')
            # this should have all the info
            try:
                comment_data = remote_node.util.get(object_url)
                return_data = return_data | comment_data.json()
            except Exception as e:
                util.log('InboxSerializer/comment', f'Error fetching comment {object_url}: {e}')
                return_data['error'] = 'Comment not found'
        return return_data

    def to_internal_value(self, data):
        '''
        Convert a raw Inbox value to our Inbox model (which has a different structure)
        This is overriding the deserialization function
        '''
        inbox_type = data['type'].lower()
        return_data = {
            'type': inbox_type,
        }
        if inbox_type == 'post':
            # serialize post and author
            author = restapi_serializers.UserSerializer(data=data['author'])
            post = post_serializers.PostSerializer(data=data)

            if author.is_valid():
                # save to db
                # Usually when we save a user (user registration, etc) we don't pass in the ID
                # this is because we want the ID to be auto-generated by the database
                # but here, we have the ID so we need to pass it in
                util.log('InboxSerializer', 'saving author to db - serializer')

                author_id = data['author']['id']
                full_author_data = author.validated_data | {'id': author_id}
                restapi_models.User.objects.create(**full_author_data)
                author_db = restapi_models.User.objects.get(pk=full_author_data['id'])
            else:
                util.log('InboxSerializer', 'author not valid - serializer')
                util.log('InboxSerializer', author.errors)

            if post.is_valid():
                # print(json.dumps(post.validated_data, indent=2))
                # print(json.dumps(author.validated_data, indent=2))
                # make a post
                post.save(author=author_db)
                return_data['post'] = post.validated_data

        elif inbox_type == 'follow':
            author = restapi_serializers.UserSerializer(data=data['actor'])
            object = restapi_serializers.UserSerializer(data=data['object'])
            if author.is_valid():
                return_data['author'] = author.validated_data | {'id': data['actor']['id']}
            if object.is_valid():
                return_data['object'] = object.validated_data | {'id': data['object']['id']}
            
            follow = FollowRequestSerializer(data=data)
            if follow.is_valid():
                follow.save()
                return_data['follow'] = follow.validated_data

        elif inbox_type == 'like':
            return_data = data
        elif inbox_type == 'comment':
            comment = InboxCommentSerializer(data=data)
            author = restapi_serializers.UserSerializer(data=data['author'])
            if comment.is_valid() and author.is_valid():
                return_data['comment'] = comment.validated_data
                return_data['author'] = author.validated_data
        else:
            raise serializers.ValidationError({
                'type': 'Unknown type ' + inbox_type
            })

        return return_data
