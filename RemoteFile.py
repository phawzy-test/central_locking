import client

class RemoteFile:
    def __init__(self, filename, *args, *kwargs):
        self.filename = filename
        self.args = args
        self.kwargs = kwargs
    def __enter__(self):
        o = client.demand_resource(self.filename)
        o["lock"].acquire(timeout=kwargs['timeout'])
    def __exit__(self):
        client.release_resource(self.filename)
    def read(self, n=0):
        pass
