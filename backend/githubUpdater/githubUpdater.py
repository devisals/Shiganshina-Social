from post.models import Post
from restapi.models import User
import requests
import util.main as util


def generateSummary(event):
    ''' 
    Generate a summary string from the github event to be used as the post content
    Should read like a sentence.
    '''
    try:
        start = 'GitHub Activity: '
        if event['type'] == 'PushEvent':
            content = f"Pushed to {event['repo']['name']}: {event['payload']['commits'][0]['message']}."
        elif event['type'] == 'CreateEvent':
            content = f"Created a {event['payload']['ref_type']} {event['payload']['ref']} in {event['repo']['name']}."
        elif event['type'] == 'DeleteEvent':
            content = f"Deleted a {event['payload']['ref_type']} {event['payload']['ref']} in {event['repo']['name']}."
        elif event['type'] == 'ForkEvent':
            content = f"Forked {event['repo']['name']} to {event['payload']['forkee']['full_name']}."
        elif event['type'] == 'IssueCommentEvent':
            content = f"Commented on issue #{event['payload']['issue']['number']} in {event['repo']['name']}."
        elif event['type'] == 'IssuesEvent':
            content = f"{event['payload']['action']} issue #{event['payload']['issue']['number']} in {event['repo']['name']}."
        elif event['type'] == 'PullRequestEvent':
            content = f"{event['payload']['action']} pull request #{event['payload']['number']} in {event['repo']['name']}."
        elif event['type'] == 'PullRequestReviewEvent':
            content = f"{event['payload']['action']} a review on pull request #{event['payload']['pull_request']['number']} in {event['repo']['name']}."
        elif event['type'] == 'PullRequestReviewCommentEvent':
            content = f"Commented on a review on pull request #{event['payload']['pull_request']['number']} in {event['repo']['name']}."
        elif event['type'] == 'ReleaseEvent':
            content = f"Released {event['payload']['release']['name']} in {event['repo']['name']}."
        elif event['type'] == 'WatchEvent':
            content = f"Starred {event['repo']['name']}."
        else:
            return None
        return start + content
    except:
        util.log('generateSummary', 'Error generating summary')
        util.log('generateSummary', event)
        raise

def updateGithubSingle(author_id):
    '''
    Updates the posts in the database with the posts from the GitHub API
    '''
    github_url = User.objects.get(pk=author_id).github
    github_id =  github_url.rstrip('/').split('/')[-1]

    response = requests.get(f'https://api.github.com/users/{github_id}/events/public')
    if response.status_code != 200:
        util.log('updateGithubSingle', f'Could not get events for {github_id} from GitHub API: {response.status_code}')
        return []
    events = response.json()

    new_posts = []

    for event in events:
        summary = generateSummary(event)
        if summary is None:
            continue
        post_id = author_id + '-' + event['id']

        try:
            Post.objects.get(pk=post_id)
        except Post.DoesNotExist:
            date = event['created_at']
            post_data = {
                'id': post_id,
                'author': User.objects.get(pk=author_id),
                'title': f'Github Activity: {github_id}',
                'description': '',
                'content': summary,
                'source': event['repo']['url'],
                'origin': event['repo']['url'],
                'visibility': 'PUBLIC',
                'isGithub': True,
            }
            new = Post.objects.create(**post_data)
            new.published = event['created_at']
            new.save()
            new_posts.append(new)

    return new_posts

def updateGithubAll():
    # Get all authors
    authors = User.objects.filter(is_active=True, is_remote=False, is_node=False)
    new_posts = []
    for author in authors:
        # ensure that the author's github is a valid github url
        if 'github.com/' not in author.github:
            continue
        added = updateGithubSingle(author.id)
        new_posts.extend(added)
    return new_posts