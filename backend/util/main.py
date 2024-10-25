import backend.settings

def standardize_url(url: str) -> str:
    '''
    Standardize URL to save in database

    This just removes trailing slashes.
    '''
    return url_remove_trailing_slash(url)

def url_remove_trailing_slash(url: str) -> str:
    '''
    Remove trailing slashes from a URL
    '''
    return url.rstrip('/')


def log(domain: str, message: str) -> None:
    '''
    Log a message to the console
    '''
    if backend.settings.LOG_LEVEL == 'DEBUG':
        print(f'[{domain}] {message}')


def removeQueryParamAll(url: str) -> str:
    '''
    Remove the `all=...` query parameter from a URL
    '''
    split = url.split('?')
    if len(split) < 2:
        return url
    queries = split[1].split('&')
    for i, query in enumerate(queries):
        if 'all' in query.split('=')[0]:
            queries.pop(i)
    new_url = split[0] + '?' + '&'.join(queries)
    new_url = new_url.rstrip('&')
    new_url = new_url.rstrip('?')
    return new_url


def id_from_url(url: str) -> str:
    '''
    if the string is a URL, return the last part of the URL
    e.g. https://example.com/api/authors/1234 -> 1234

    If not, return the string
    '''
    url = url.rstrip('/')
    if 'http' in url:
        return url.split('/')[-1]
    else:
        return url
