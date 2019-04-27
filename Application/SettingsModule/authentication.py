#!/usr/bin/env python3
from LoggingModule.logging import logger
from SettingsModule.settings import mongo_db, jwt_secret, app_super_admin, app_super_admin_pwd, credentials_collection
import jwt


#https://simplapi.wordpress.com/2014/03/26/python-tornado-and-decorator/, refrence for roles
# This actually check for the autorization, only one superdmin exists in this application till now.
# if the user_type is not superdmin then it must be called from the databse if that user exists or not
def _checkAuth(username, password, user_type=None):
    ''' Check user can access or not to this element '''
    # TODO: return None if user is refused
    # TODO: do database check here, to get user.
    #jwt.decode(encoded, 'secret', algorithms=['HS256'])
    if user_type == "superadmin":
    		if username == app_super_admin and password == app_super_admin_pwd:
    			return True
    		else:
    			return False

    else:
    		user = yield credentails_collection.find_one({'user_type': user_type, "username": username, "password": password})
    		if user:
    			return True
    		else: 
    			return False

    return {
        'login': 'okay',
        'password': 'okay',
        'role': 'okay'
    }
 
def auth(handler_class):
		def wrap_execute(handler_execute):
				def require_auth(handler, kwargs):
						auth_header = handler.request.headers.get('Authorization')
						print (handler.request.headers)
					
						if auth_header is None: #or not auth_header.startswith('Basic '):
								handler.set_status(401)
								handler.set_header('WWW-Authenticate', 'Basic realm=Restricted')
								handler._transforms = []
								handler.finish()
								return False
						
						try:
								auth_decoded = jwt.decode(auth_header, jwt_secret, algorithms=['HS256']) 
						except Exception as e:
								logger.info(e.__str__())
								handler.set_status(401)
								handler.set_header('WWW-Authenticate', 'Basic realm=Restricted')
								handler._transforms = []
								handler.finish()
								return False
						print (auth_decoded)
						auth_found      = _checkAuth(**auth_decoded)

						if not auth_found:
								handler.set_status(401)
								handler.set_header('WWW-Authenticate', 'Basic realm=Restricted')
								handler._transforms = []
								handler.finish()
								return False
						else:
								handler.request.headers.add('auth', auth_found)
						return True
				def _execute(self, transforms, *args, **kwargs):
						if not require_auth(self, kwargs):
								return False
						return handler_execute(self, transforms, *args, **kwargs)
				return _execute
		handler_class._execute = wrap_execute(handler_class._execute)
return handler_class