'''
Utility functions/classes for tests
''' 

import django.test.testcases


class LiveServerThreadWithReuse(django.test.testcases.LiveServerThread):
    """
    This miniclass overrides _create_server to allow port reuse. This avoids creating
    "address already in use" errors for tests that have been run subsequently.

    https://stackoverflow.com/a/51756256
    """

    def _create_server(self, connections_override=None):
        return self.server_class(
            (self.host, self.port),
            django.test.testcases.QuietWSGIRequestHandler,
            allow_reuse_address=True,
            connections_override=connections_override,
        )
