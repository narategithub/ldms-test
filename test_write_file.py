#!/usr/bin/env python

import os
import sys
import argparse
from LDMS_Test import DockerCluster

if __name__ != "__main__":
    raise RuntimeError("This is not a module.")

execfile(os.getenv("PYTHONSTARTUP", "/dev/null"))

SCRIPTDIR = os.path.realpath(sys.path[0])
USER = os.getlogin()

ap = argparse.ArgumentParser(description = "Test container.write_file()")
ap.add_argument("--name",
                default = "{}-test-write-file".format(USER),
                help = "The cluster name")
ap.add_argument("--nfsdir",
                default = "{}/nfs-dir".format(SCRIPTDIR),
                help = "The directory on NFS for write file testing")
ap.add_argument("--image",
                default = "ovis-centos-build",
                help = "The docker image for each container in the cluster")

args = ap.parse_args()

if not os.path.exists(args.nfsdir):
    os.makedirs(args.nfsdir)

print "-- Getting/Creating a cluster --"
mounts = ["{}:/nfsdir:rw".format(args.nfsdir)]
cluster = DockerCluster.get(args.name, create = True, nodes = 1,
                            mounts = mounts, image = args.image)

[cont] = cluster.containers

print "-- Test writing files --"

#  utility to test writing files
def test_write_read(cont, path, txt):
    sz = len(txt)
    print " test writing", sz, "B, path:", path, "...",
    cont.write_file(path, txt)
    rtxt = cont.read_file(path)
    assert(txt == rtxt)
    print "OK"

# Simple short write
test_write_read(cont, "/tmp/file0", "Short Write")

# 4k write
txt = "0" * 4096
test_write_read(cont, "/tmp/file1", txt)

# 1M write
txt = "0" * (1024*1024)
test_write_read(cont, "/tmp/file2", txt)

# the same for NFS
test_write_read(cont, "/nfsdir/file0", "Short Write")
test_write_read(cont, "/nfsdir/file1", "0"*4096)
test_write_read(cont, "/nfsdir/file2", "0"*(1024*1024))

# Test error handling
print "-- Test write error handling --"

print " parent directory does not exist ...",
try:
    cont.write_file("/path/not/exist", "bla")
except RuntimeError, e:
    # expecting "No such file or directory"
    if not e.message.endswith("No such file or directory\n"):
        raise
    print "OK"

print " parent directory is a file ...",
try:
    cont.write_file("/tmp/file0/bla", "bla")
except RuntimeError, e:
    if not e.message.endswith("Not a directory\n"):
        raise
    print "OK"

print "-- Removing the cluster --"
cluster.remove()
