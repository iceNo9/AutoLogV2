import ctypes
from ctypes.wintypes import DWORD, LPCWSTR, HANDLE

kernel32 = ctypes.WinDLL('kernel32')

PAGE_READWRITE = 0x04
FILE_MAP_ALL_ACCESS = 0xF001F
INVALID_HANDLE_VALUE = -1

CreateFileMappingW = kernel32.CreateFileMappingW
CreateFileMappingW.argtypes = (HANDLE, ctypes.c_void_p, DWORD, DWORD, DWORD, LPCWSTR)
CreateFileMappingW.restype = HANDLE

MapViewOfFile = kernel32.MapViewOfFile
MapViewOfFile.argtypes = (HANDLE, DWORD, DWORD, DWORD, ctypes.c_size_t)
MapViewOfFile.restype = ctypes.c_void_p

UnmapViewOfFile = kernel32.UnmapViewOfFile
UnmapViewOfFile.argtypes = (ctypes.c_void_p,)
UnmapViewOfFile.restype = bool

CloseHandle = kernel32.CloseHandle
CloseHandle.argtypes = (HANDLE,)
CloseHandle.restype = bool


def create_shared_memory(size=ctypes.sizeof(ctypes.c_int), name='Global\\MySharedMemory'):
    h_file_mapping = CreateFileMappingW(INVALID_HANDLE_VALUE, None, PAGE_READWRITE, 0, size, name)
    if h_file_mapping == INVALID_HANDLE_VALUE:
        raise Exception("Failed to create file mapping.")

    address = MapViewOfFile(h_file_mapping, FILE_MAP_ALL_ACCESS, 0, 0, size)
    if not address:
        CloseHandle(h_file_mapping)
        raise Exception("Failed to map view of file.")

    return address, h_file_mapping


def set_integer_in_shared_memory(address, value=0):
    ctypes.c_int.from_address(address).value = value


def read_integer_from_shared_memory(address):
    return ctypes.c_int.from_address(address).value


class CmdModule:
    def __init__(self):
        self.address, self.h_file_mapping = create_shared_memory()
        self.enable = True

    def set_shared_memory(self, value):
        try:
            if self.enable:
                set_integer_in_shared_memory(self.address, value)
        finally:
            UnmapViewOfFile(self.address)
            CloseHandle(self.h_file_mapping)
            self.enable = False
