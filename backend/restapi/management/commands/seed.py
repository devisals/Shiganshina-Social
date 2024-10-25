from django.core.management.base import BaseCommand
from django_seed import Seed
from django.contrib.contenttypes.models import ContentType

import restapi.models as user_models
import post.models as post_models
from inbox.models import Inbox

from remote_node.models import RemoteNode

import os, urllib.parse

# python manage.py seed

class Command(BaseCommand):
    help = "seed database for testing and development."

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        # clear all data
        user_models.User.objects.all().delete()
        post_models.Post.objects.all().delete()
        post_models.Like.objects.all().delete()
        post_models.Comment.objects.all().delete()
        RemoteNode.objects.all().delete()
        Inbox.objects.all().delete()

        # get HOST_URL environment variable
        host = os.environ.get('HOST_API_URL')
        if host is None:
            raise ValueError('HOST_API_URL environment variable must be set')
        host = urllib.parse.urlparse(host).geturl()

        print('Cleared all data.')

        seeder = Seed.seeder()

        # create admin user (not django superuser but a register admin user)
        admin = user_models.User.objects.create_admin(
            'Hazel Campbell', 
            'hazel123',
            'https://github.com/hazelybell', 
            'https://github.com/hazelybell.png'
        )
        print('Created admin user with displayName: Hazel Campbell and password: hazel123')

        # create normal user
        user = user_models.User.objects.create_user(
            'Linus Torvalds',
            'linus123',
            'https://github.com/torvalds',
            'https://github.com/torvalds.png'
        )
        print('Created user with displayName: Linus Torvalds and password: linus123')

        # create test acive node
        user_models.User.objects.create_node(
            displayName='ActiveNode',
            password='active123',
            url=seeder.faker.url(),
        )
        print('Created active node with displayName: ActiveNode and password: active123')

        # create test inactive node
        user_models.User.objects.create_node(
            displayName='InactiveNode',
            password='inactive123',
            url=seeder.faker.url(),
        )
        print('Created inactive node with displayName: InactiveNode and password: inactive123')


        self.stdout.write('seeding data...')

        seeder.add_entity(user_models.User, 5, {
            'displayName': lambda x: seeder.faker.name(),
            'host': host,
            'is_node': False,
            'is_staff': False,
            'is_active': True,
        })
        seeder.add_entity(post_models.Post, 5)
        seeder.add_entity(post_models.Comment, 5)
        # Randomly like 10 posts, and 10 comments
        seeder.add_entity(post_models.Like, 5, {
            'author': lambda x: seeder.faker.random_element(user_models.User.objects.all()).url,
            'object': lambda x: seeder.faker.random_element(post_models.Post.objects.all()).url,
        })
        seeder.add_entity(post_models.Like, 5, {
            'author': lambda x: seeder.faker.random_element(user_models.User.objects.all()).url,
            'object': lambda x: seeder.faker.random_element(post_models.Comment.objects.all()).url,
        })

        # make linus post 3 posts
        linus = user_models.User.objects.get(displayName='Linus Torvalds')
        seeder.add_entity(post_models.Post, 3, {
            'author': linus,
        })
        inserted_pks = seeder.execute()
        print(inserted_pks)

        # Add connents to linus's posts
        for post in linus.post_set.all():
            seeder.add_entity(post_models.Comment, 3, {
                'post': post,
                'author': admin,
                'comment': 'This is a comment on Linus Torvalds post.',
                'published': '2021-10-10T10:00:00Z',
                'contentType': 'text/plain',
            })
        inserted_pks = seeder.execute()
        print(inserted_pks)

        # edit all the user url fields
        users = user_models.User.objects.all()
        for user in users:
            user.url = urllib.parse.urljoin(host, f'authors/{user.id}')
            user.save()
        
        # add local node to remoteNode table
        RemoteNode.objects.create(
            nodeName='Local Node',
            url=host,
            displayName='local',
            password='1234'
        )
        user_models.User.objects.create_node(
            displayName='local',
            password='1234',
            url=host,
        )

        self.stdout.write('Done seeding data.')
