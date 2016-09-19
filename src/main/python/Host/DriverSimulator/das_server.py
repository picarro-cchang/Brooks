#!/usr/bin/python
#
"""
File Name: das_server.py
Purpose: Implementation of a remote procedure call system to a simulated analyzer
    for testing user interfaces

File History:
    17-May-2016  sze       Initial version

Copyright (c) 2016 Picarro, Inc. All rights reserved
"""

import configobj
import cPickle
import ctypes
import Host.Simulators.DasServer.interface as interface
from flask import abort, Flask, make_response, jsonify, Response, request, url_for
from flask.ext.restful import Api, reqparse, Resource, fields, marshal
from flask.ext.httpauth import HTTPBasicAuth
import inspect
import json
import logging
import math
import os
import types

auth = HTTPBasicAuth()
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
app = Flask(__name__, static_url_path='', static_folder='../js/flux_webpack/src/')
app.add_url_rule('/', 'root', lambda: app.send_static_file('index.html'))
api = Api(app)
app.config.update(SEND_FILE_MAX_AGE_DEFAULT=0)

das_registers = interface.INTERFACE_NUMBER_OF_REGISTERS * [0]
fpga_registers = 512*[0]

def coerce(value):
    try:
        value = int(value)
    except ValueError:
        try:
            value = float(value)
        except ValueError:
            pass
    return value

def _value(valueOrName):
    """Convert valueOrName into an value, raising an exception if the name is not found"""
    if isinstance(valueOrName, types.StringType):
        try:
            valueOrName = getattr(interface, valueOrName)
        except AttributeError:
            raise AttributeError("Value identifier not recognized %s" % valueOrName)
    return valueOrName

def _reg_index(indexOrName):
    """Convert a name or index into an integer index, raising an exception if the name is not found"""
    if isinstance(indexOrName, types.IntType):
        return indexOrName
    else:
        try:
            return interface.registerByName[indexOrName.strip().upper()]
        except KeyError:
            raise ValueError("Unknown register name %s" % (indexOrName,))

def wrDasReg(regIndexOrName, value, convert=True):
    if convert:
        value = _value(value)
    index = _reg_index(regIndexOrName)
    if 0 <= index < len(das_registers):
        ri = interface.registerInfo[index]
        if ri.type in [ctypes.c_uint, ctypes.c_int, ctypes.c_long]:
            das_registers[index] = int(value)
        elif ri.type == ctypes.c_float:
            das_registers[index] = float(value)
        else:
            raise ValueError("Type %s of register %s is not known" % (ri.type, regIndexOrName,))
    else:
        raise IndexError('Register index not in range')

def rdDasReg(regIndexOrName):
    index = _reg_index(regIndexOrName)
    if 0 <= index < len(das_registers):
        return das_registers[index]
    else:
        raise IndexError('Register index not in range')

def wrFPGA(baseIndexOrName,regIndexOrName,value,convert=True):
    base = _value(baseIndexOrName)
    reg = _value(regIndexOrName)
    if convert:
        value = _value(value)
    fpga_registers[base + reg] = int(value)

def rdFPGA(baseIndexOrName,regIndexOrName):
    base = _value(baseIndexOrName)
    reg = _value(regIndexOrName)
    return fpga_registers[base + reg]

def initSimulator():
    this_dir = os.path.dirname(os.path.abspath(inspect.getsourcefile(lambda: 0)))
    with open(os.path.join(this_dir, "Master.ini"), "r") as mp:
        config = configobj.ConfigObj(mp)
        for key, value in config["DAS_REGISTERS"].items():
            value = float(value)
            wrDasReg(key, value)
        for secname in config:
            if secname.startswith("FPGA"):
                for key, value in config[secname].items():
                    wrFPGA(secname, key, int(value))

initSimulator()

@auth.get_password
def get_password(username):
    raise NotImplementedError

@auth.error_handler
def unauthorized():
    # return 403 instead of 401 to prevent browsers from displaying the default
    # auth dialog
    return make_response(jsonify({'message': 'Unauthorized access'}), 403)

def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

@app.route('/shutdown', methods=['POST'])
def shutdown():
    shutdown_server()
    return 'Server shutting down...'

class ParamFormsAPI(Resource):
    def get(self):
        return {'param_forms': interface.parameter_forms}

class RegisterAPI(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('dsp', type=str, action="append", required=False)
        parser.add_argument('fpga', type=str, action="append", required=False)
        request_dict = parser.parse_args()
        try:
            response = []
            if request_dict['dsp'] is not None:
                for item in request_dict['dsp']:
                    atoms = [_value(coerce(atom.strip())) for atom in item.split(",")]
                    if len(atoms) in (1,):
                        index = sum(atoms)
                        response.append(dict(type='dsp', index=index, value=rdDasReg(index)))
                    else:
                        raise ValueError('Invalid arguments for reading dsp register')
            if request_dict['fpga'] is not None:
                for item in request_dict['fpga']:
                    atoms = [_value(coerce(atom.strip())) for atom in item.split(",")]
                    if len(atoms) in (1, 2):
                        index = sum(atoms)
                        response.append(dict(type='fpga', index=index, value=rdFPGA(index, 0)))
                    else:
                        raise ValueError('Invalid arguments for reading fpga register')
            return {'register': response}
        except AttributeError:
            return {'error': 'Cannot find symbol in get register'}
        except ValueError, e:
            return {'error': 'ValueError: ' + e.message}
        except Exception, e:
            return {'error': 'Uncaught exception in get register ' + e.message}

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('dsp', type=str, action="append", required=False)
        parser.add_argument('fpga', type=str, action="append", required=False)
        request_dict = parser.parse_args()
        try:
            response = []
            if request_dict['dsp'] is not None:
                for item in request_dict['dsp']:
                    atoms = [_value(coerce(atom.strip())) for atom in item.split(",")]
                    if len(atoms) in (2,):
                        wrDasReg(atoms[0], atoms[1])
                        response.append(dict(type='dsp', index=atoms[0], value=rdDasReg(atoms[0])))
                    else:
                        raise ValueError('Invalid arguments for writing dsp register')
            if request_dict['fpga'] is not None:
                for item in request_dict['fpga']:
                    atoms = [_value(coerce(atom.strip())) for atom in item.split(",")]
                    if len(atoms) in (2, 3):
                        index = sum(atoms[:-1])
                        wrFPGA(index, 0, atoms[-1])
                        response.append(dict(type='fpga', index=index, value=rdFPGA(index, 0)))
                    else:
                        raise ValueError('Invalid arguments for fpga register')
            return {'register': response}
        except AttributeError:
            return {'error': 'Cannot post symbol in get register'}
        except ValueError, e:
            return {'error': 'ValueError: ' + e.message}
        except Exception, e:
            return {'error': 'Uncaught exception in get register ' + e.message}

api.add_resource(ParamFormsAPI, '/api/v1.0/driver/paramforms', endpoint='paramforms')
api.add_resource(RegisterAPI, '/api/v1.0/driver/register', endpoint='register')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 3001)), debug=True)
