# -*- coding: utf-8 -*-
"""
    ripped from https://github.com/mitsuhiko/python-pbkdf2
    until he pulls https://github.com/mitsuhiko/python-pbkdf2/pull/4
    or adds PY3 himself

    :copyright: (c) Copyright 2011 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
from binascii import hexlify
import hmac
import hashlib
from struct import Struct
from operator import xor
from itertools import starmap

from pyramid.compat import (
    PY3,
    bytes_
    )

if not PY3:  # pragma: no cover
    from itertools import izip as zip


_pack_int = Struct('>I').pack


def hexlify_(s):  # pragma: no cover
    if PY3:
        return str(hexlify(s), encoding="utf8")
    else:
        return s.encode('hex')


def range_(*args):   # pragma: no cover
    if PY3:
        return range(*args)
    else:
        return xrange(*args)


def pbkdf2_hex(data, salt, iterations=1000, keylen=24, hashfunc=None):
    """Like :func:`pbkdf2_bin` but returns a hex encoded string."""
    return hexlify_(pbkdf2_bin(data, salt, iterations, keylen, hashfunc))


def pbkdf2_bin(data, salt, iterations=1000, keylen=24, hashfunc=None):
    """Returns a binary digest for the PBKDF2 hash algorithm of `data`
    with the given `salt`.  It iterates `iterations` time and produces a
    key of `keylen` bytes.  By default SHA-1 is used as hash function,
    a different hashlib `hashfunc` can be provided.
    """
    hashfunc = hashfunc or hashlib.sha1
    mac = hmac.new(bytes_(data), None, hashfunc)

    def _pseudorandom(x, mac=mac):
        h = mac.copy()
        h.update(bytes_(x))
        if PY3:  # pragma: no cover
            return [x for x in h.digest()]
        else:  # pragma: no cover
            return map(ord, h.digest())
    buf = []
    for block in range_(1, -(-keylen // mac.digest_size) + 1):
        rv = u = _pseudorandom(bytes_(salt) + _pack_int(block))
        for i in range_(iterations - 1):
            if PY3:  # pragma: no cover
                u = _pseudorandom(bytes(u))
            else:  # pragma: no cover
                u = _pseudorandom(''.join(map(chr, u)))
            rv = starmap(xor, zip(rv, u))
        buf.extend(rv)
    if PY3:  # pragma: no cover
        return bytes(buf)[:keylen]
    else:  # pragma: no cover
        return ''.join(map(chr, buf))[:keylen]
