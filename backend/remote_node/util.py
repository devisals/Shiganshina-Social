'''
Utilities regarding remote node functionality
'''
import requests
from remote_node.models import RemoteNode
import base64
from rest_framework.response import Response
from rest_framework import status
import util.main

def get(url: str, header: dict = None) -> requests.Response:
    url = util.main.standardize_url(url)
    util.main.log('util/GET', f'GETting from {url}.')
    # look through RemoteNode until we find the one that matches the url
    for node in RemoteNode.objects.filter(disabled=False):
        url = transform_url_for_node(url, node)

        if url.startswith(node.url.rstrip('/')):
            util.main.log('util/GET', f'Getting from {node.url}')
            # if we find it, we return the response
            if not header:
                token = base64.b64encode(f'{node.displayName}:{node.password}'.encode('ascii')).decode('ascii')
                headers = {
                    'Authorization': f'Basic {token}',
                    'Content-Type': 'application/json'
                }

            response = requests.get(url, headers=headers)
            util.main.log('util/GET', f'{node.url} returned response {response.status_code} in {response.elapsed.total_seconds()} seconds')
            return response
    
    util.main.log('util/GET', f'No node matched the URL {url}. Returning 404.')
    return Response({ 'error': 'we tried to search through all nodes, but we couldn\'t find any that matched!'}, status=status.HTTP_404_NOT_FOUND)

def post(url: str, json: dict) -> requests.Response:
    url = util.main.standardize_url(url)
    util.main.log('util/POST', f'POSTing to {url} with JSON {json}. Need to look through all nodes to find the right one')

    # look through RemoteNode until we find the one that matches the url
    for node in RemoteNode.objects.filter(disabled=False):
        util.main.log('util/POST', f'Getting from {node.url}')
        url = transform_url_for_node(url, node)

        if url.startswith(node.url.rstrip('/')):
            # if we find it, we return the response
            token = base64.b64encode(f'{node.displayName}:{node.password}'.encode('ascii')).decode('ascii')
            headers = {
                'Authorization': f'Basic {token}',
                'Content-Type': 'application/json'
            }
            if node.nodeName == 'lost':
                if '/inbox' in url:
                    util.main.log('util/POST', f'stripping off inbox wrapping from inbox forward data, and capitalizing "type": "Follow"')
                    json['type'] = 'Follow'
                    if 'items' in json:
                        json = json['items'][0]
                    else:
                        util.main.log('util/POST', f'no items in json but i literally do not care anymore. Here is the JSON post data: {json}')

            util.main.log('util/POST', f'Bingo! Returning response {url} with JSON {json}')
            return requests.post(url, json=json, headers=headers)
    
    return Response({ 'error': 'we tried to search through all nodes, but we couldn\'t find any that matched!'}, status=status.HTTP_404_NOT_FOUND)

def transform_url_for_node(url: str, node: RemoteNode) -> str:
    '''
    Given a URL and a node, transform the URL to match any specifications of specific nodes

    e.g. team lost needs a trailing slash, but team snack does not

    '''

    util.main.log('remote_node/util/transform_url_for_node', f'Transforming url {url} for node {node.nodeName}')
    url = util.main.standardize_url(url)

    if node.nodeName == 'lost':
        util.main.log('remote_node/util/transform_url_for_node', f'Adding trailing slash to {url} for team lost')
        url_split = url.split('?', maxsplit=2)
        if len(url_split) > 1:
            url = url_split[0] + '/?' + url_split[1]
        else:
            url = url.rstrip('/') + '/'
        
        # also, replace "https://lostone-8ec8a3227ce0.herokuapp.com/" with "https://lostone-8ec8a3227ce0.herokuapp.com/api/"
        if "https://lostone-8ec8a3227ce0.herokuapp.com/api" not in url:
            util.main.log('remote_node/util/transform_url_for_node', f'adding /api/ to url {url}')
            url = url.replace("https://lostone-8ec8a3227ce0.herokuapp.com/", "https://lostone-8ec8a3227ce0.herokuapp.com/api/")

    util.main.log('remote_node/util/transform_url_for_node', f'Returning url {url}')
    return url
