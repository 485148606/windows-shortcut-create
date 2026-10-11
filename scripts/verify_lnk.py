# -*- coding: utf-8 -*-
"""Verify a .lnk by loading it through the shell's own IShellLink COM parser.
Pure ctypes - no pywin32 needed. Proves the file is spec-valid and resolvable.
"""
import ctypes
from ctypes import wintypes, POINTER, c_void_p, byref, c_uint

ole32 = ctypes.OleDLL('ole32')
CLSCTX_INPROC_SERVER = 1
CLSID_ShellLink = '{00021401-0000-0000-C000-000000000046}'
IID_IShellLinkW = '{000214F9-0000-0000-C000-000000000046}'
IID_IPersistFile = '{0000010b-0000-0000-C000-000000000046}'
SLGP_RAWPATH = 0x4


class GUID(ctypes.Structure):
    _fields_ = [('Data1', wintypes.DWORD), ('Data2', wintypes.WORD),
                ('Data3', wintypes.WORD), ('Data4', ctypes.c_ubyte * 8)]


def guid(s):
    g = GUID()
    ole32.CLSIDFromString(ctypes.c_wchar_p(s), byref(g))
    return g


def vt_call(ptr, index, restype, *argtypes):
    """Return a bound function for vtable slot `index`."""
    vtable = ctypes.cast(ptr, POINTER(POINTER(c_void_p)))[0]
    fn_addr = vtable[index]
    proto = ctypes.WINFUNCTYPE(restype, c_void_p, *argtypes)
    return proto(fn_addr)


def verify(path):
    ole32.CoInitialize(None)
    clsid, iid = guid(CLSID_ShellLink), guid(IID_IShellLinkW)
    psl = c_void_p()
    hr = ole32.CoCreateInstance(byref(clsid), None, CLSCTX_INPROC_SERVER,
                                byref(iid), byref(psl))
    if hr != 0:
        return 'CoCreateInstance failed hr=%#x' % hr

    # QueryInterface -> IPersistFile  (slot 0)
    iid_pf = guid(IID_IPersistFile)
    ppf = c_void_p()
    qi = vt_call(psl, 0, ctypes.HRESULT, POINTER(GUID), POINTER(c_void_p))
    hr = qi(psl, byref(iid_pf), byref(ppf))
    if hr != 0:
        return 'QueryInterface(IPersistFile) failed hr=%#x' % hr

    # IPersistFile::Load (slot 5), STGM_READ = 0
    load = vt_call(ppf, 5, ctypes.HRESULT, ctypes.c_wchar_p, wintypes.DWORD)
    hr = load(ppf, path, 0)
    if hr != 0:
        return 'Load FAILED hr=%#x  <-- .lnk is invalid' % hr

    # IPersistFile::Load parses the whole .lnk through the shell's own reader.
    # If it returns S_OK the file is structurally valid & resolvable.
    load = vt_call(ppf, 5, ctypes.HRESULT, ctypes.c_wchar_p, wintypes.DWORD)
    hr = load(ppf, path, 0)
    if hr != 0:
        return 'Load FAILED hr=%#x  <-- .lnk is invalid' % hr

    # best-effort field dump (vtable: 3 GetPath | 7 GetWorkingDirectory | 10 GetArguments)
    out = []
    try:
        buf = ctypes.create_unicode_buffer(520)
        getpath = vt_call(psl, 3, ctypes.HRESULT, ctypes.c_wchar_p,
                          c_void_p, wintypes.DWORD)
        getpath(psl, buf, None, SLGP_RAWPATH)
        out.append('  target  : %s' % buf.value)
    except Exception as e:
        out.append('  (GetPath unavailable: %s)' % e)
    try:
        abuf = ctypes.create_unicode_buffer(2048)
        getargs = vt_call(psl, 10, ctypes.HRESULT, ctypes.c_wchar_p, ctypes.c_int)
        getargs(psl, abuf, 2048)
        out.append('  args    : %s' % abuf.value)
    except Exception as e:
        out.append('  (GetArguments unavailable: %s)' % e)

    return 'Load S_OK - valid .lnk\n' + '\n'.join(out)


if __name__ == '__main__':
    import sys
    for p in sys.argv[1:]:
        print('==', p)
        print(verify(p))
