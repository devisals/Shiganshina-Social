from django.shortcuts import render
import requests
from .models import RemoteNode
# Create your views here.

class RemoteNodeView():
    def connect_to_nodes():
        nodes = RemoteNode.objects.filter(disabled=False)
        for node in nodes:
            try:
                response = requests.get(node.url, auth=(node.displayName, node.password))
                if response.status_code == 200:
                    # Process successful response from the node
                    print(f"Connected to {node.name}")
                else:
                    # Handle non-200 status codes
                    print(f"Failed to connect to {node.name}. Status code: {response.status_code}")
            except requests.RequestException as e:
                # Handle network errors or other exceptions
                print(f"Error connecting to {node.name}: {e}")