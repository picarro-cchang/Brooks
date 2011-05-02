#!/usr/bin/python
#
# FILE:
#   jsonRpc.py
#
# DESCRIPTION:
#   Simple Python Client for calling JSON RPC routines
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   29-Apr-2011  sze  Initial version.
#
#  Copyright (c) 2011 Picarro, Inc. All rights reserved
#
import urllib2,uuid,thread,base64
try:
    import simplejson as json
except:
    import json

class _Method(object):
    # from jsonrpclib
    def __init__(self, send, name):
        self.__send = send
        self.__name = name
    def __getattr__(self, name):
        return _Method(self.__send, "%s.%s" % (self.__name, name))
    def __call__(self, *args):
        return self.__send(self.__name, args)

class Proxy():
    def __init__(self, service_url, auth_user = None, auth_password = None):
        self.service_url = service_url
        self.auth_user = auth_user
        self.auth_password = auth_password
    def call(self, method, params=None, success=None, failure=None):
        if success != None or failure != None:
            thread.start_new_thread(self.__call,(method, params, success, failure))
        else:
            result = self.__call(method,params)
            if ('error' in result) and result['error'] != None:
                raise Exception(result['error'])
                return None
            else:
                return result['result']
    def __call(self, method, params=None, success=None, failure=None):
        try:
            id = str(uuid.uuid1())
            data = json.dumps({'method':method, 'params':params, 'id':id})
            req = urllib2.Request(self.service_url)
            if self.auth_user != None and self.auth_password != None:
                authString = base64.encodestring('%s:%s' % (self.auth_user, self.auth_password))[:-1]
                req.add_header("Authorization", "Basic %s" % authString)
            req.add_header("Content-type", "application/json")
            f = urllib2.urlopen(req, data)
            response = f.read()
            data = json.loads(response)
        except IOError, (strerror):
            data = dict(result=None,error=dict(message='Network error. ' + str(strerror),code=None,data=None), id=id)
        except ValueError, (strerror):
            data = dict(result=None,error=dict(message='JSON format error. ' + str(strerror),code=None,data=None), id=id)

        if ("error" in data) and data["error"] != None:
            if failure != None:
                failure(data['error'])
        else:
            if success != None:
                success(data['result'])
        return data
    def __getattr__(self, name):
        return _Method(self.call, name)
