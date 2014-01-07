"""
Copyright 2014 Picarro Inc.
"""

from __future__ import with_statement

import os
import subprocess
from os import path

import sqlalchemy
from sqlalchemy import orm
from OpenSSL import SSL
from OpenSSL import crypto

import Models


class SSLCertManager(object):

    DB = None

    SSL_CONF = path.join(path.dirname(__file__), 'openssl.cnf')
    CERT_DIR = path.join(path.dirname(__file__), 'certs')

    @staticmethod
    def getContextByIP(ipAddr):
        if not SSLCertManager.DB:
            engine = sqlalchemy.create_engine('sqlite:///certs.db')
            Models.Base.metadata.create_all(engine)
            SSLCertManager.DB = orm.sessionmaker(bind=engine)()


        certMgr = SSLCertManager(SSLCertManager.DB)
        if not certMgr.certExists(ipAddr) or certMgr.certExpired(ipAddr):
            self._generateCert(ipAddr)

        return certMgr.getContext(ipAddr)

    def __init__(self, db):
        self.db = db

    def certExists(self, ipAddr):
        return self.db.query(Models.SSLCert).filter(Models.SSLCert.ipAddress==ipAddr).count() == 1

    def certExpired(self, ipAddr):
        if not self.certExists(ipAddr):
            return True

        self._expandCert(ipAddr)
        cert = crypto.load_certificate(crypto.FILETYPE_PEM,
                                       file(path.join(SSLCertManager.CERT_DIR, "%s.pem" % ipAddr)).read())
        return cert.has_expired()

    def getContext(self, ipAddr):
        self._expandCert(ipAddr)

        ctx = SSL.Context(SSL.SSLv23_METHOD)
        ctx.use_privatekey_file(self._cert(ipAddr))
        ctx.use_certificate_file(self._cert(ipAddr))

        return ctx

    def _generateCert(self, ipAddr):
        cert = self._cert(ipAddr)

        if not path.exists(SSLCertManager.CERT_DIR):
            os.makedirs(SSLCertManager.CERT_DIR)

        if path.exists(cert):
            os.unlink(cert)

        assert not path.exists(cert)

        with open("%s.log" % cert, 'w') as certErrFp:
            subprocess.Popen(['openssl.exe', 'req', '-config', SSLCertManager.SSL_CONF, '-x509', '-nodes', '-days',
                              '365', '-subj', "/C=US/ST=California/L=Santa Clara/CN=%s" % ipAddr, '-newkey',
                              'rsa:1024', '-keyout', cert, '-out', cert], stderr=certErrFp).wait()

        assert path.exists(cert)

        self.db.add(Models.SSLCert(ipAddress=ipAddr, certificate=file(cert).read()))
        self.db.commit()

    def _expandCert(self, ipAddr):
        assert self.certExists(ipAddr)

        if not path.exists(SSLCertManager.CERT_DIR):
            os.makedirs(SSLCertManager.CERT_DIR)

        certRow = self.db.query(Models.SSLCert).filter(Models.SSLCert.ipAddress==ipAddr).one()
        with open(self._cert(ipAddr), 'w') as fp:
            fp.write(certRow.certificate)

    def _cert(self, ipAddr):
        return path.join(SSLCertManager.CERT_DIR, "%s.pem" % ipAddr)
