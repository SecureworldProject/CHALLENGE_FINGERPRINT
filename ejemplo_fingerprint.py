#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time     :   6/24/2019 9:03 PM
# @Author   :   Luspock
# @File     :   fingerprint.py

# ESTE CODIGO FUENTE ES SOLO UN EJEMPLO PARA APRENDER A HACER EL CHALLENGE
# HAY QUE EJECUTARLO EN MODO USUARIO ADMINISTRADOR de lo contrario el lector de huella no hace nada
# ademas, aqui se usa "myFP.verify()" que ofrece un resultado de tipo parental
# para modo empresarial habria que usar algo parecido a myFP.identify()
# lo que pasa que lo he probado y sale muy poca info, habria que sacar informacion
# biometrica, pero no se si es posible sacar eso.



import ctypes
from ctypes import wintypes
from dataclasses import dataclass

import lock
import random
import os 

SECURITY_MAX_SID_SIZE = 68
WINBIO_TYPE_FINGERPRINT = 0x00000008
WINBIO_POOL_SYSTEM = 0x00000001
WINBIO_FLAG_DEFAULT = 0x00000000
WINBIO_ID_TYPE_SID = 3

# Error Info
WINBIO_E_NO_MATCH = 0x80098005

lib = ctypes.WinDLL(r"C:\Windows\System32\winbio.dll")


class GUID(ctypes.Structure):
    _fields_ = [("Data1", wintypes.DWORD),
                ("Data2", wintypes.WORD),
                ("Data3", wintypes.WORD),
                ("Data4", wintypes.BYTE * 8)
                ]


class AccountSid(ctypes.Structure):
    _fields_ = [("Size", wintypes.ULONG),
                ("Data", ctypes.c_ubyte * SECURITY_MAX_SID_SIZE)
                ]


class Value(ctypes.Union):
    _fields_ = [("NULL", wintypes.ULONG),
                ("Wildcard", wintypes.ULONG),
                ("TemplateGuid", GUID),
                ("AccountSid", AccountSid)
                ]


class WINBIO_IDENTITY(ctypes.Structure):
    _fields_ = [("Type", ctypes.c_uint32),
                ("Value", Value)]


class TOKEN_INFORMATION_CLASS:
    TokenUser = 1
    TokenGroups = 2
    TokenPrivileges = 3


class SID_IDENTIFIER_AUTHORITY(ctypes.Structure):
    _fields_ = [("Value", wintypes.BYTE*6)]


# https://www.csie.ntu.edu.tw/~r92094/c++/Win_Header/WINNT.H
class SID(ctypes.Structure):
    _fields_ = [("Revision", wintypes.BYTE),
                ("SubAuthorityCount", wintypes.BYTE),
                ("IdentifierAuthority", SID_IDENTIFIER_AUTHORITY),
                ("SubAuthority", wintypes.DWORD)]


class SID_AND_ATTRIBUTES(ctypes.Structure):
    _fields_ = [("Sid", ctypes.POINTER(SID)),
                ("Attributes", wintypes.DWORD)]


class TOEKN_USER(ctypes.Structure):
    _fields_ = [("User", SID_AND_ATTRIBUTES)]


class FingerPrint:
    def __init__(self):
        self.session_handle = ctypes.c_uint32()
        self.unit_id = ctypes.c_uint32()

        # important  represent which finger you are using
        # full definition is in winbio_types.h
        self.subfactor = ctypes.c_ubyte(0xf5)       # WINBIO_FINGER_UNSPECIFIED_POS_01

        # WINBIO_ID_TYPE_SID = 3
        self.identity = WINBIO_IDENTITY()
        self.IsOpen = False

    def open(self):
        if self.IsOpen:
            return
        ret = lib.WinBioOpenSession(WINBIO_TYPE_FINGERPRINT,  # finger print
                                    WINBIO_POOL_SYSTEM,
                                    WINBIO_FLAG_DEFAULT,
                                    None,
                                    0,
                                    None,
                                    ctypes.byref(self.session_handle))  # pool   system
        if ret & 0xffffffff != 0x0:
            print("Open Failed!")
            return False
        self.IsOpen = True
        return True

    def locate_unit(self):
        ret = lib.WinBioLocateSensor(self.session_handle, ctypes.byref(self.unit_id))
        print(self.unit_id)
        if ret & 0xffffffff != 0x0:
            print("Locate Failed!")
            return False
        return True

    def identify(self):
        reject_detail = ctypes.c_uint32()
        ret = lib.WinBioIdentify(self.session_handle, ctypes.byref(self.unit_id), ctypes.byref(self.identity),
                                 ctypes.byref(self.subfactor),
                                 ctypes.byref(reject_detail))
        """
        if ret & 0xffffffff != 0x0:
            print(hex(ret & 0xffffffff))
            raise Exception("Identify Error")
        """
        print(f"Unit ID\t:{hex(self.unit_id.value)}")
        print(f"Sub Factor\t:{hex(self.subfactor.value)}")
        print(f"Identity Type\t: {self.identity.Type}")
        print(f"Identity AccountSid Data\t: {list(self.identity.Value.AccountSid.Data)[0:self.identity.Value.AccountSid.Size]}")
        print(f"Identity AccountSid Size\t: {self.identity.Value.AccountSid.Size}")
        print(f"Rejected Details:\t{hex(reject_detail.value)}")

    def verify(self):
        match = ctypes.c_bool(0)
        reject_detail = ctypes.c_uint32()
        # get identity
        self.get_current_user_identity()
        ret = lib.WinBioVerify(self.session_handle, ctypes.byref(self.identity),
                               self.subfactor, ctypes.byref(self.subfactor),
                               ctypes.byref(match), ctypes.byref(reject_detail))
        if ret & 0xffffffff == WINBIO_E_NO_MATCH or ret & 0xffffffff == 0:
            return match.value
        else:
            print(hex(ret & 0xffffffff))
            raise Exception("Identify Error")

    def close(self):
        if not self.IsOpen:
            return
        lib.WinBioCloseSession(self.session_handle)
        self.session_handle = 0

    def get_current_user_identity(self):
        self.get_token_information()

    @staticmethod
    def get_process_token():
        """
        Get the current process token
        """
        #  Reference
        #  https://gist.github.com/schlamar/7024668
        GetCurrentProcess = ctypes.windll.kernel32.GetCurrentProcess
        GetCurrentProcess.restype = wintypes.HANDLE
        OpenProcessToken = ctypes.windll.advapi32.OpenProcessToken
        OpenProcessToken.argtypes = (wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE))
        OpenProcessToken.restype = wintypes.BOOL
        token = wintypes.HANDLE()

        # https://github.com/Alexpux/mingw-w64/blob/master/mingw-w64-tools/widl/include/winnt.h
        # TOKEN_READ = STANDARD_RIGHTS_READ | TOKEN_QUERY = 0x00020000 | 0x0008 = 0x20008
        # TOKEN_ALL_ACCESS = 0xf01ff

        TOKEN_READ = 0x20008
        res = OpenProcessToken(GetCurrentProcess(), TOKEN_READ, token)
        if not res > 0:
            raise RuntimeError("Couldn't get process token")
        return token

    def get_token_information(self):
        """
        Get token info associated with the current process.
        """
        GetTokenInformation = ctypes.windll.advapi32.GetTokenInformation
        GetTokenInformation.argtypes = [
            wintypes.HANDLE,  # TokenHandle
            ctypes.c_uint,  # TOKEN_INFORMATION_CLASS value
            wintypes.LPVOID,  # TokenInformation
            wintypes.DWORD,  # TokenInformationLength
            ctypes.POINTER(wintypes.DWORD),  # ReturnLength
            ]
        GetTokenInformation.restype = wintypes.BOOL

        CopySid = ctypes.windll.advapi32.CopySid
        CopySid.argtypes = [
            wintypes.DWORD,     # nDestinationSidLength
            ctypes.c_void_p,    # pDestinationSid,
            ctypes.c_void_p     # pSourceSid
        ]
        CopySid.restype = wintypes.BOOL

        GetLengthSid = ctypes.windll.advapi32.GetLengthSid
        GetLengthSid.argtypes = [
            ctypes.POINTER(SID)  # PSID
        ]
        GetLengthSid.restype = wintypes.DWORD

        return_length = wintypes.DWORD(0)
        buffer = ctypes.create_string_buffer(SECURITY_MAX_SID_SIZE)

        res = GetTokenInformation(self.get_process_token(),
                                  TOKEN_INFORMATION_CLASS.TokenUser,
                                  buffer,
                                  SECURITY_MAX_SID_SIZE,
                                  ctypes.byref(return_length)
                                  )
        assert res > 0, "Error in second GetTokenInformation (%d)" % res

        token_user = ctypes.cast(buffer, ctypes.POINTER(TOEKN_USER)).contents
        CopySid(SECURITY_MAX_SID_SIZE,
                self.identity.Value.AccountSid.Data,
                token_user.User.Sid
                )
        self.identity.Type = WINBIO_ID_TYPE_SID
        self.identity.Value.AccountSid.Size = GetLengthSid(token_user.User.Sid)


def executeChallenge():
    myFP = FingerPrint()
    try:
        print("Python: Starting executeChallenge()")
        dataPath=os.environ['SECUREMIRROR_CAPTURES']
        print("storage folder is :",dataPath)


        lock.lockIN("huella_Dactilar")

        lock.lockOUT("huella_Dactilar")



        myFP.open()
        print("Please touch the fingerprint sensor")
        #myFP.identify()

        if props_dict['metodo']=='empresarial':
            if myFP.verify():
                print("Hello! Master")
                cad=1
            else:
                print("Sorry! Man")
                cad=random.randint(2, 100)
        elif props_dict['metodo']=='parental':
             if myFP.verify():
                print("Hello! Master")
                cad=1
             else:
                print("Sorry! Man")
                cad=0
        print('resultado del Challenge: ', cad)
        #y generamos el resultado
        cad="%d"%(cad)
        key = bytes(cad,'utf-8')
        key_size = len(key)
        result = (key, key_size)
        print("result:", result)
        
        
    finally:
        myFP.close()

    return result


props_dict = {}
DEBUG_MODE = True

# funcion init devuelve un 0 que es valido ya que suponemos que el usuario va a tener siempre 8un teclado con el que pueda escribir
def init(props):
    global props_dict
    print("Python: starting challenge init()")
    #cargamos el json que le pasemos y lo guardamos en la variable global
    props_dict = props
    return 0


if __name__ == '__main__':
     midict = {"metodo":'empresarial'}
     init(midict)
     executeChallenge()