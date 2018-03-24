import requests

HOST_SESSION = requests.Session()
DB_SERVER_URL = "http://127.0.0.1:3600/api/v1.0/"
USER_NAME = None
SESSION_TOKEN = None

def _send_request(action, api, payload):
    """
    action: requests.get or post
    use_token: set to True if the api requires token for authentication
    """
    action_func = getattr(HOST_SESSION, action)
    if SESSION_TOKEN is not None:
        header = {'Authentication': SESSION_TOKEN}
    else:
        header = {}
    try:
        response = action_func(DB_SERVER_URL + api, data=payload, headers=header)
        return response.json()
    except Exception, err:
        return {"error": str(err)}

def login(username, password, requester):
    global USER_NAME, SESSION_TOKEN
    payload = {'command': "log_in_user",
            'requester': requester,
            'username': username,
            'password': password }
    return_dict = _send_request("post", "account", payload)
    if "error" not in return_dict:
        USER_NAME = username
        SESSION_TOKEN = return_dict["token"]
    return return_dict

def logout():
    global USER_NAME, SESSION_TOKEN
    if USER_NAME is None: 
        return {"error": "Cannot logout before login!"}

    payload = {'command': "log_out_user",
            'requester': "qtLauncher",
            'username': USER_NAME }
    return_dict = _send_request("post", "account", payload)
    if "error" not in return_dict:
        USER_NAME = None
        SESSION_TOKEN = None
    return return_dict

def log(action):
    if USER_NAME is None or SESSION_TOKEN is None:
        return {"error": "Cannot log before login!"}

    payload = {'username': USER_NAME,
               'action': action }
    return _send_request("post", "action", payload)    