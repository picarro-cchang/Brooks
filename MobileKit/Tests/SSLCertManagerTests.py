"""
Copyright 2014 Picarro Inc.
"""

import sys
import os
from os import path

import sqlalchemy
from sqlalchemy import orm
from OpenSSL import SSL

sys.path.append(path.abspath(path.join('..', 'AnalyzerServer')))
import SSLCertManager
import Models


class TestSSLCertManager(object):

    def setup_method(self, m):
        if path.exists('certs.db'):
            os.unlink('certs.db')

        engine = sqlalchemy.create_engine('sqlite:///certs.db')
        Models.Base.metadata.create_all(engine)
        self.db = orm.sessionmaker(bind=engine)()
        self.mgr = SSLCertManager.SSLCertManager(self.db)

    def teardown_method(self, m):
        self.db.close()

    def testGenerateCert(self):
        self.mgr._generateCert('127.0.0.1')
        assert self.db.query(Models.SSLCert).filter(Models.SSLCert.ipAddress=='127.0.0.1').count() == 1

    def testValidPemExistsForGoodIP(self):
        self.mgr._generateCert('127.0.0.1')
        assert self.mgr.certExists('127.0.0.1')
        assert not self.mgr.certExpired('127.0.0.1')

    def testNoPemForInvalidIP(self):
        assert not self.mgr.certExists('255.255.255.255')

    def testContextForValidIP(self):
        self.mgr._generateCert('127.0.0.1')
        ctx = SSLCertManager.SSLCertManager.getContextByIP('127.0.0.1')
        assert ctx is not None
        assert isinstance(ctx, SSL.Context)


