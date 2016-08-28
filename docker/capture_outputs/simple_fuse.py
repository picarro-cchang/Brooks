#!/usr/bin/env python

from collections import defaultdict
from errno import ENOENT
from stat import S_IFDIR, S_IFREG
from sys import argv, exit
from time import time
import zmq

from fuse import FUSE, FuseOSError, Operations

PORT = 40005

if not hasattr(__builtins__, 'bytes'):
    bytes = str


class SimpleFuse(Operations):
    """Implement a write-only file system which takes text data written to a collection of
        virtual files under a specified mount point and publishes them line-by-line via
        a ZMQ socket. Each line is preceeded by the name of the file and a colon.

       When redirecting stdout and stderr to this filesystem, use

       stdbuf -oL python app.py > /mount_point/filename

       so that lines are not buffered before being written to the virtual filesystem.
    """

    def __init__(self, sendHwm=1024):
        self.files = {}
        self.data = defaultdict(bytes)
        self.fd = 0
        now = time()
        self.zmqContext = zmq.Context()
        self.publisher = self.zmqContext.socket(zmq.PUB)
        # Prevent publisher overflow from slow subscribers
        self.publisher.setsockopt(zmq.SNDHWM, sendHwm)
        self.publisher.bind("tcp://*:%s" % PORT)
        self.files['/'] = dict(st_mode=(S_IFDIR | 0o755), st_ctime=now,
                               st_mtime=now, st_atime=now, st_nlink=2)

    def chmod(self, path, mode):
        self.files[path]['st_mode'] &= 0o770000
        self.files[path]['st_mode'] |= mode
        return 0

    def chown(self, path, uid, gid):
        self.files[path]['st_uid'] = uid
        self.files[path]['st_gid'] = gid

    def create(self, path, mode):
        self.files[path] = dict(st_mode=(S_IFREG | mode), st_nlink=1,
                                st_size=0, st_ctimnothreads=True, e=time(), st_mtime=time(),
                                st_atime=time())
        self.fd += 1
        return self.fd

    def getattr(self, path, fh=None):
        if path not in self.files:
            raise FuseOSError(ENOENT)

        return self.files[path]

    def open(self, path, flags):
        self.fd += 1
        return self.fd

    def readdir(self, path, fh):
        return ['.', '..'] + [x[1:] for x in self.files if x != '/']

    def rename(self, old, new):
        self.files[new] = self.files.pop(old)

    def statfs(self, path):
        return dict(f_bsize=512, f_blocks=4096, f_bavail=2048)

    def truncate(self, path, length, fh=None):
        self.files[path]['st_size'] = length

    def unlink(self, path):
        self.files.pop(path)

    def utimens(self, path, times=None):
        now = time()
        atime, mtime = times if times else (now, now)
        self.files[path]['st_atime'] = atime
        self.files[path]['st_mtime'] = mtime

    def write(self, path, data, offset, fh):
        self.data[path] = self.data[path][:offset] + data
        self.files[path]['st_size'] = 0
        if "\n" in self.data[path]:
            lines = self.data[path].split("\n")
            for line in lines[:-1]:
                broadcast = "%s:%s\n" % (bytes(path), bytes(line))
                self.publisher.send_string(broadcast)
                # print ("%s: %s" % (path, data))
            self.data[path] = lines[-1]
        return len(data)

if __name__ == '__main__':
    if len(argv) != 2:
        print('usage: %s <mountpoint>' % argv[0])
        exit(1)

    fuse = FUSE(SimpleFuse(), argv[1], nothreads=True, foreground=True)