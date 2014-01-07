"""
Copyright 2014 Picarro, Inc.
"""

import sqlalchemy
from sqlalchemy.ext import declarative


Base = declarative.declarative_base()


class SSLCert(Base):
    __tablename__ = 'sslCerts'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    ipAddress = sqlalchemy.Column(sqlalchemy.String, unique=True, index=True)
    certificate = sqlalchemy.Column(sqlalchemy.Text)

    def __repr__(self):
        return "<SSLCert '%s'>" % self.ipAddress
