from nameko.rpc import rpc
from nameko.web.handlers import http

class GreeterService(object):
    name = "greeter_service"

    @http('GET', '/greet')
    @rpc
    def greet(self, name):
        """
            Greet health check
        """
        return u"Hello {name}!".format(name=name)