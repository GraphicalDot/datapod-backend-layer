

```
r = requests.post("http://localhost:8000/user/login", data=json.dumps({"username": "graphicaldot", "password": "Groot9"}))

error:
	{'message': 'The username or password is incorrect',
	 'error': True,
	 'success': False}

success:
	{'error': False,
	 'success': True,
	 'message': 'Logged in successfully',
	 'data': None}
```

Change Password API:

```
r = requests.post("http://localhost:8000/user/change_password", data=json.dumps({"proposed_password": "Groo", "previous_password": "BIGwdi#"}))     
	
error:
	{'message': 'Password you have enetered is incorrect',
 	'error': True,
 	'success': False}


error:
	{'message': 'Uknown error An error occurred (LimitExceededException) when calling the ChangePassword operation: Attempt limit exceeded, please try after some time. ',
	 'error': True,
 	'success': False}

response:
	{'message': 'Password has been changed successfully ',
	 'error': True,
 	'success': False}
	
```

Forgot password

```
r = requests.post("http://localhost:8000/user/forgot_password", data=json.dumps({"username": "graphicaldot"}))

success: 
	{'error': False,
 	'success': True,
	 'message': None,
 	'data': 'Please check your Registered email id for validation code'}


```

Confirm validation code Forgot password

```
 r = requests.post("http://localhost:8000/user/confirm_forgot_password", data=json.dumps({"username": "graphicaldot", "proposed_password": "BIg98@#", "validation_c
    ...: ode": 611414}))

error:
	{'message': 'Password you have entered is incorrect',
	'error': True,
	'success': False}

error:

	{'message': 'Invalid Verification code', 'error': True, 'success': False}

error:
	{'message': 'Uknown error An error occurred (ExpiredCodeException) when calling the ConfirmForgotPassword operation: Invalid code provided, please request a code again. ',
	'error': True,
	'success': False,
	'Data': None}



success:
	{'message': 'Password has been updated successfully',
	'error': True,
	'success': False,
	'Data': None}
```