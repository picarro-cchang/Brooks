"""
Copyright 2012 Picarro Inc.

Simple script for building only the .ini file output for the SSIM installer.
"""

from __future__ import with_statement

import os.path

import jinja2
import simplejson as json


def main():
    meta = {}
    with open('meta.json', 'r') as metaFp:
        meta.update(json.load(metaFp))


        env = jinja2.Environment(loader=jinja2.FileSystemLoader(
                os.path.join('.', 'templates')))
        t = env.get_template('Coordinator_SSIM.ini.j2')

        for k in meta:
            print "Generating coordinator for '%s'." % k
            standards = [col for col in meta[k]['columns'] if col[5] == 'True']
            with open("Coordinator_SSIM_%s.ini" % k, 'w') as coordFp:
                coordFp.write(t.render(analyzer=meta[k],
                                       standards=standards))


if __name__ == '__main__':
    main()
