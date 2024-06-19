import socket


class Middleware:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        # Do something with the request
        response = self.app(environ, start_response)
        # Do something with the response
        return response
