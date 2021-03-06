#!/usr/bin/env python
import sys, struct
from bup import options, git
from bup.helpers import *

suspended_w = None


def init_dir(conn, arg):
    git.init_repo(arg)
    debug1('bup server: bupdir initialized: %r\n' % git.repodir)
    conn.ok()


def set_dir(conn, arg):
    git.check_repo_or_die(arg)
    debug1('bup server: bupdir is %r\n' % git.repodir)
    conn.ok()

    
def list_indexes(conn, junk):
    git.check_repo_or_die()
    for f in os.listdir(git.repo('objects/pack')):
        if f.endswith('.idx'):
            conn.write('%s\n' % f)
    conn.ok()


def send_index(conn, name):
    git.check_repo_or_die()
    assert(name.find('/') < 0)
    assert(name.endswith('.idx'))
    idx = git.open_idx(git.repo('objects/pack/%s' % name))
    conn.write(struct.pack('!I', len(idx.map)))
    conn.write(idx.map)
    conn.ok()


def receive_objects_v2(conn, junk):
    global suspended_w
    git.check_repo_or_die()
    suggested = {}
    if suspended_w:
        w = suspended_w
        suspended_w = None
    else:
        w = git.PackWriter()
    while 1:
        ns = conn.read(4)
        if not ns:
            w.abort()
            raise Exception('object read: expected length header, got EOF\n')
        n = struct.unpack('!I', ns)[0]
        #debug2('expecting %d bytes\n' % n)
        if not n:
            debug1('bup server: received %d object%s.\n' 
                % (w.count, w.count!=1 and "s" or ''))
            fullpath = w.close()
            if fullpath:
                (dir, name) = os.path.split(fullpath)
                conn.write('%s.idx\n' % name)
            conn.ok()
            return
        elif n == 0xffffffff:
            debug2('bup server: receive-objects suspended.\n')
            suspended_w = w
            conn.ok()
            return
            
        shar = conn.read(20)
        crcr = struct.unpack('!I', conn.read(4))[0]
        n -= 20 + 4
        buf = conn.read(n)  # object sizes in bup are reasonably small
        #debug2('read %d bytes\n' % n)
        if len(buf) < n:
            w.abort()
            raise Exception('object read: expected %d bytes, got %d\n'
                            % (n, len(buf)))
        oldpack = w.exists(shar)
        # FIXME: we only suggest a single index per cycle, because the client
        # is currently too dumb to download more than one per cycle anyway.
        # Actually we should fix the client, but this is a minor optimization
        # on the server side.
        if not suggested and \
          oldpack and (oldpack == True or oldpack.endswith('.midx')):
            # FIXME: we shouldn't really have to know about midx files
            # at this layer.  But exists() on a midx doesn't return the
            # packname (since it doesn't know)... probably we should just
            # fix that deficiency of midx files eventually, although it'll
            # make the files bigger.  This method is certainly not very
            # efficient.
            oldpack = w.objcache.packname_containing(shar)
            debug2('new suggestion: %r\n' % oldpack)
            assert(oldpack)
            assert(oldpack != True)
            assert(not oldpack.endswith('.midx'))
            w.objcache.refresh()
        if not suggested and oldpack:
            assert(oldpack.endswith('.idx'))
            (dir,name) = os.path.split(oldpack)
            if not (name in suggested):
                debug1("bup server: suggesting index %s\n" % name)
                conn.write('index %s\n' % name)
                suggested[name] = 1
        else:
            nw, crc = w._raw_write([buf], sha=shar)
            _check(w, crcr, crc, 'object read: expected crc %d, got %d\n')
            _check(w, n, nw, 'object read: expected %d bytes, got %d\n')
    # NOTREACHED
    

def _check(w, expected, actual, msg):
    if expected != actual:
        w.abort()
        raise Exception(msg % (expected, actual))


def read_ref(conn, refname):
    git.check_repo_or_die()
    r = git.read_ref(refname)
    conn.write('%s\n' % (r or '').encode('hex'))
    conn.ok()


def update_ref(conn, refname):
    git.check_repo_or_die()
    newval = conn.readline().strip()
    oldval = conn.readline().strip()
    git.update_ref(refname, newval.decode('hex'), oldval.decode('hex'))
    conn.ok()


cat_pipe = None
def cat(conn, id):
    global cat_pipe
    git.check_repo_or_die()
    if not cat_pipe:
        cat_pipe = git.CatPipe()
    try:
        for blob in cat_pipe.join(id):
            conn.write(struct.pack('!I', len(blob)))
            conn.write(blob)
    except KeyError, e:
        log('server: error: %s\n' % e)
        conn.write('\0\0\0\0')
        conn.error(e)
    else:
        conn.write('\0\0\0\0')
        conn.ok()


optspec = """
bup server
"""
o = options.Options('bup server', optspec)
(opt, flags, extra) = o.parse(sys.argv[1:])

if extra:
    o.fatal('no arguments expected')

debug2('bup server: reading from stdin.\n')

commands = {
    'init-dir': init_dir,
    'set-dir': set_dir,
    'list-indexes': list_indexes,
    'send-index': send_index,
    'receive-objects-v2': receive_objects_v2,
    'read-ref': read_ref,
    'update-ref': update_ref,
    'cat': cat,
}

# FIXME: this protocol is totally lame and not at all future-proof.
# (Especially since we abort completely as soon as *anything* bad happens)
conn = Conn(sys.stdin, sys.stdout)
lr = linereader(conn)
for _line in lr:
    line = _line.strip()
    if not line:
        continue
    debug1('bup server: command: %r\n' % line)
    words = line.split(' ', 1)
    cmd = words[0]
    rest = len(words)>1 and words[1] or ''
    if cmd == 'quit':
        break
    else:
        cmd = commands.get(cmd)
        if cmd:
            cmd(conn, rest)
        else:
            raise Exception('unknown server command: %r\n' % line)

debug1('bup server: done\n')
