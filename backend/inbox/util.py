from inbox import models
from restapi.serializers import UserSerializer
from util.main import id_from_url


def retrieve_or_copy_author(json_data: dict) -> models.User:
    '''
    Given the JSON of a user, either return the user if it already exists or copy the user to the local database
    
    We only search by the ID of the user
    '''
    try:
        if 'id' not in json_data:
            raise Exception('ID not found in JSON data')

        # only get UUID from the id field
        json_data['id'] = id_from_url(json_data['id'])

        if 'type' not in json_data:
            raise Exception('Type not found in JSON data')
        if json_data['type'] != 'author':
            raise Exception('Type is not author')

        # check if the user already exists
        if models.User.objects.filter(id=json_data['id']).exists():
            user = models.User.objects.get(id=json_data['id'])
            return user
        else:
            return copy_user(json_data)
    except Exception as e:
        raise Exception(f'Error creating or copying user: {e}')

def copy_user(json_data: dict) -> models.User: 
    '''
    Given some JSON, copies the user to the local database

    If there is some serialization error, throw an exception
    '''
    try:
        user = UserSerializer(data=json_data)

        # check that url and id are not null
        if 'url' not in json_data or 'id' not in json_data:
            raise Exception('URL or ID not found in JSON data')
        
        # remove the URL in the user ID if exists
        # since all our groups use UUIDs, it's safe to assume that the ID is the last part of the URL
        json_data['id'] = id_from_url(json_data['id'])
        
        # check that a user with the same ID does not already exist
        if models.User.objects.filter(id=json_data['id']).exists():
            raise Exception('User with that ID already exists')

        if user.is_valid():
            user_db = user.save(url=json_data['url'], id=json_data['id'])

            user_db.is_remote = True
            user_db.save()

            return user_db
        else:
            raise Exception(user.errors)
    except Exception as e:
        raise Exception(f'Error copying user: {e}')
