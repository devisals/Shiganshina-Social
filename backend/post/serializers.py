from rest_framework import serializers
from post import models
from post.models import Post, Like, Comment
from restapi.models import User
from restapi.serializers import UserSerializer
from django.contrib.contenttypes.models import ContentType
import os
import util.main as util
import remote_node.util
import json

BASE_URL = os.environ.get("HOST_API_URL") + "authors"


class PostSerializer(serializers.ModelSerializer):
    """
    ### POST SERIALIZER
    Serializes the author of the post and provides the URL to the comments on the post.
    Attributes:
        - author (UserSerializer): The author of the post
        - comments (str): The URL of the comments on the post
    Methods:
        - get_comments: Returns the URL to the comments on the post
    """

    author = UserSerializer(read_only=True)
    comments = serializers.SerializerMethodField()

    class Meta:
        model = models.Post
        fields = [
            "type",
            "id",
            "author",
            "title",
            "description",
            "content",
            "contentType",
            "published",
            "visibility",
            "comments",
            "source",
            "origin",
            "count",
            "url",
        ]

    def get_comments(self, obj):
        """
        Returns the URL to the comments on the post
        """
        return f"{BASE_URL}/{obj.author_id}/posts/{obj.id}/comments"

    def create(self, validated_data):
        """
        Creates a new Post object with the validated data
        Returns the new Post object
        """
        return Post.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """
        Updates the input post instance with the validated data.
        Returns the updated instance.
        """
        instance.title = validated_data.get("title", instance.title)
        instance.description = validated_data.get("description", instance.description)
        instance.content = validated_data.get("content", instance.content)
        instance.contentType = validated_data.get("contentType", instance.contentType)
        instance.visibility = validated_data.get("visibility", instance.visibility)
        instance.source = validated_data.get("source", instance.source)
        instance.origin = validated_data.get("origin", instance.origin)
        instance.save()
        return instance

    def to_representation(self, instance):
        """
        Convert a POST db object to a JSON object
        """
        # post["source"] = "source"
        #         post["origin"] = "origin"
        #         post["count"] = models.Comment.objects.filter(post_id=post["id"]).count()
        #         post["id"] = f"{BASE_URL}/{author_id}/posts/{post['id']}"
        #         post["author"].update({"id": f"{BASE_URL}/{author_id}"})
        data = super().to_representation(instance)

        data["source"] = f"{BASE_URL}/{instance.author_id}/posts/{data['id']}"
        data["origin"] = f"{BASE_URL}/{instance.author_id}/posts/{data['id']}"
        data["count"] = Comment.objects.filter(post_id=data["id"]).count()
        data["id"] = f"{BASE_URL}/{instance.author_id}/posts/{data['id']}"
        # data['author'] should already be a correctly formatted author JSON

        return data


class CommentSerializer(serializers.ModelSerializer):
    """
    ### COMMENT SERIALIZER
    Serializes the author of the comment.
    """

    author = UserSerializer(read_only=True)

    class Meta:
        model = models.Comment
        fields = ["type", "id", "author", "comment", "published", "contentType"]

    def create(self, validated_data):
        """
        Creates a new Comment object with the validated data
        Returns the new Comment object
        """
        return Comment.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """
        Updates the input comment instance with the validated data.
        Returns the updated instance.
        """
        instance.comment = validated_data.get("comment", instance.comment)
        instance.published = validated_data.get("published", instance.published)
        instance.contentType = validated_data.get("contentType", instance.contentType)
        instance.save()
        return instance

    def to_representation(self, instance):
        """
        Convert a COMMENT db object to a JSON object
        """
        data = super().to_representation(instance)
        data["id"] = (
            f"{BASE_URL}/{instance.post.author_id}/posts/{instance.post_id}/comments/{data['id']}"
        )

        return data


class LikeSerializer(serializers.ModelSerializer):
    """
    ### LIKE SERIALIZER
    Serializes the author of the like.

    DB Fields:
        - summary (str): A short description of the like (e.g. user likes this post)
        - type (str): The type of the activity (e.g. Like, Comment, etc.)
        - object (str): The URL of the object being liked
        - published (datetime): The date and time the like was made

    Sample JSON:
    {
        "summary": "Lara Croft Likes your post",
        "type": "Like",
        "author":{
            "type":"author",
            "id":"http://localhost:8000/9de17f29c12e8f97bcbbd34cc908f1baba40658e",
            "host":"http://127.0.0.1:5454/",
            "displayName":"Lara Croft",
            "url":"http://127.0.0.1:5454/authors/9de17f29c12e8f97bcbbd34cc908f1baba40658e",
            "github":"http://github.com/laracroft",
            "profileImage": "https://i.imgur.com/k7XVwpB.jpeg"
        },
        "object":"http://127.0.0.1:5454/authors/9de17f29c12e8f97bcbbd34cc908f1baba40658e/posts/764efa883dda1e11db47671c4a3bbd9e"
    }
    """

    class Meta:
        model = models.Like
        fields = ["id", "author", "object", "published"]

    def to_representation(self, instance):
        """
        Convert a LIKE db object to a JSON object
        """
        data = super().to_representation(instance)

        # get author locally
        try:
            author = User.objects.get(url=instance.author)
            author_data = UserSerializer(author).data
        except User.DoesNotExist:
            util.log(
                "LikeSerializer/to_representation",
                f"User {instance.author} does not exist locally, fetching from remote node",
            )
            # GOTO: get author from remote node
        except Exception as e:
            util.log(
                "LikeSerializer/to_representation",
                f"Error getting author {instance.author} from local database: {e}",
            )
            util.log("LikeSerializer/to_representation", f"Trying remote instead")
        else:
            util.log(
                "LikeSerializer/to_representation",
                f"Author data (local): {author_data}",
            )
            data["type"] = "like"
            data["author"] = author_data
            data["summary"] = f"{author_data['displayName']} likes your post"
            util.log(
                "LikeSerializer/to_representation",
                f"Like found (local):\n {json.dumps(data, indent=4)}",
            )
            return data

        # get author from remote node
        try:
            util.log(
                "LikeSerializer/to_representation", f"GET author: {instance.author}"
            )
            author_data = remote_node.util.get(instance.author)
            if author_data.status_code != 200:
                util.log(
                    "LikeSerializer/to_representation",
                    f"Failed to connect to {instance.author}. Status code: {author_data.status_code}",
                )
                raise Exception(
                    f"Failed to connect to {instance.author}. Status code: {author_data.status_code}"
                )
            else:
                util.log(
                    "LikeSerializer/to_representationt",
                    f"Author data (remote): {author_data.json()}",
                )
                data["type"] = "like"
                data["author"] = author_data.json()
                data["summary"] = f"{author_data.json()['displayName']} likes your post"
                util.log(
                    "LikeSerializer/to_representation",
                    f"Like found (remote):\n {json.dumps(data, indent=4)}",
                )
                return data

        except Exception as e:
            util.log(
                "LikeSerializer/to_representation",
                f"Error converting like {instance.id} to JSON object: {e}",
            )
            raise e
