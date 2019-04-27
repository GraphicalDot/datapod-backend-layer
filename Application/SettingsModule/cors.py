
#!/usr/bin/env python


from functools import update_wrapper
from functools import wraps



def cors(f):
        @wraps(f) # to preserve name, docstring, etc.
        def wrapper(self, *args, **kwargs): # **kwargs for compability with functions that use them
                #print (self.request.headers)
                self.set_header("Access-Control-Allow-Origin",  "*")
                self.set_header("Access-Control-Allow-Headers", "Content-type, Authorization, Accept, X-Requested-With")
                self.set_header("Access-Control-Max-Age", 60)
                self.set_header("Access-Control-Allow-Methods",  "POST, GET, PUT, DELETE, OPTIONS, HEAD, TRACE")
                self.set_header("Access-Control-Allow-Credentials", "true")
                self.set_header("Access-Control-Allow-Headers", "X-Requested-With, Content-Type, Origin, Authorization, Accept, Client-Security-Token, Accept-Encoding")
                return f(self, *args, **kwargs)
        return wrapper