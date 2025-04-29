from nicegui import ui
import re
from config import CONST
from user import process
from time import sleep

class Admin:

    def __init__(self):
        pass
   

    @staticmethod
    def email(fc, address=None, pswd=None):
        
        if fc == "add" and address and len(pswd) >= 6:
            output = process("email", fc, address, pswd)
            if output["rc"] == 0:
                    ui.notify("A New user added", type='positive')
            else: ui.notify("Something wrong", type='negative')


        elif fc == "list":
            output = process("email", fc)
            if output["rc"] == 0:
                    address_list = output["stdout"]             
                    address_list =  re.findall(r'^\* ([^\s]+)', address_list, re.MULTILINE)
                    return address_list
            else: ui.notify("Something wrong", type='negative')
        
        elif fc == "del":
            address = address[-1]
            output = process("email", fc, "-y", address)
            if output["rc"] == 0:
                    ui.notify(f"User {address} deleted", type='positive')
            else: ui.notify("Something wrong", type='negative')

    @staticmethod
    def quota(fc, address, quota=None):
        if fc == "set" and quota:
            address = address[-1]
            output = process("quota", fc, address, str(quota)+"M")
            if output["rc"] == 0:
                    ui.notify(f"Quota {quota}MiB added to address: {address}", type="positive")
            else: ui.notify("Something wrong", type='negative')
        elif fc == "del" and address:
            address = address[-1]
            output = process("quota", fc, address)
            if output["rc"] == 0:
                    ui.notify(f"Quota deleted to address: {address}", type="positive")
            else: ui.notify("Something wrong", type='negative')


    @staticmethod
    def quota_users(func):
        quota_users = []
        for i in func:
             if i["quota"] != "~":
                  quota_users.append(i["email"])
        return quota_users