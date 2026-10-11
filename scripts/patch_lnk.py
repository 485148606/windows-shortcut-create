# -*- coding: utf-8 -*-
"""Patch an existing, system-created Chrome .lnk into a 'Pavo AI' shortcut.

Why: hand-built .lnk files (make_lnk.py) omit LinkTargetIDList, which some
Windows shells resolve poorly. Patching a genuine Chrome shortcut keeps the
system-generated IDList/LinkInfo intact and only injects:
  - LinkFlags |= HasArguments (0x20)
  - one ARGUMENTS StringData entry (inserted in spec order, before ICON_LOCATION)
"""
import struct
import sys

SRC = r'C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Google Chrome.lnk'
ICON = r'C:\Program Files\Google\Chrome\Application\chrome.exe'

FLAG_HAS_ARGUMENTS = 0x20

ORDER = [  # (flag, label) in spec order
    (0x4, 'NAME'),
    (0x8, 'RELATIVE_PATH'),
    (0x10, 'WORKING_DIR'),
    (0x20, 'ARGUMENTS'),
    (0x40, 'ICON_LOCATION'),
]


def ustr(s):
    return struct.pack('<H', len(s)) + s.encode('utf-16-le')


def read_ustr(d, off):
    n = struct.unpack_from('<H', d, off)[0]
    start = off + 2
    return d[start:start + n * 2].decode('utf-16-le'), start + n * 2


def parse(data):
    """Return (flags, [(label, value)], extra_offset) or raise."""
    hdr_size = struct.unpack_from('<I', data, 0)[0]
    assert hdr_size == 0x4C, hdr_size
    flags = struct.unpack_from('<I', data, 20)[0]
    off = 0x4C

    if flags & 0x1:  # HasLinkTargetIDList
        idl_size = struct.unpack_from('<H', data, off)[0]
        off += 2 + idl_size
    if flags & 0x2:  # HasLinkInfo
        li_size = struct.unpack_from('<I', data, off)[0]
        off += li_size
    out = []
    for bit, label in ORDER:
        if flags & bit:
            val, off = read_ustr(data, off)
            out.append((label, val))
    return flags, out, off


def main():
    args = '--user-data-dir="C:\\Users\\Administrator\\.cache\\chrome-devtools-mcp\\chrome-profile" --remote-debugging-port=9222 https://app.pavo-ai.cn/'
    out_path = sys.argv[1] if len(sys.argv) > 1 else r'D:\workbuddy\2026-09-24-13-23-04\pavo\Pavo AI.lnk'

    d = bytearray(open(SRC, 'rb').read())
    print('--- BEFORE ---')
    print(parse(bytes(d)))

    flags = struct.unpack_from('<I', d, 20)[0]
    struct.pack_into('<I', d, 20, flags | FLAG_HAS_ARGUMENTS)

    pat = ustr(ICON)
    i = bytes(d).find(pat)
    if i < 0:
        raise SystemExit('ICON_LOCATION StringData not found')
    # sanity: the ARGUMENTS entry must land between WORKING_DIR and ICON_LOCATION
    d[i:i] = ustr(args)

    open(out_path, 'wb').write(bytes(d))
    print('--- AFTER ---')
    flags2, items, extra_off = parse(bytes(d))
    for k, v in items:
        print(' %-14s %r' % (k, v))
    print(' flags = %#x' % flags2)
    print(' extra offset = %d, file size = %d' % (extra_off, len(d)))
    print('written', out_path)


if __name__ == '__main__':
    main()
