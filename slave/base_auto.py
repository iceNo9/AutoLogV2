# $language="python3"
# $interface="1.0"

# coding=utf8

import ctypes
import time
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


def set_signal_in_shared_memory(address, signal=0):
    ctypes.c_int.from_address(address).value = signal


def read_signal_from_shared_memory(address):
    return ctypes.c_int.from_address(address).value


def main():
    status = 1
    size = ctypes.sizeof(ctypes.c_int)  # 获取整数大小
    address, h_file_mapping = create_shared_memory(size)
    set_signal_in_shared_memory(address, 1)

    try:
        while True:
            signal = read_signal_from_shared_memory(address)
            if signal != status:
                status = signal
                if signal == 0:
                    execute_action_disconnect()
                elif signal == 1:
                    execute_action_connect()

            # if status:# 串口连接时执行操作，例如查找关键词输入指令

            time.sleep(0.1)  # 延迟以避免频繁检查（根据实际需求调整）
    finally:
        UnmapViewOfFile(address)
        CloseHandle(h_file_mapping)


def execute_action_connect():
    crt.GetScriptTab().Session.Disconnect()


def execute_action_disconnect():
    crt.GetScriptTab().Session.Connect()


main()
