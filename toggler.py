import winreg
import shutil
import os

DISABLED = ".disabled"

def disable(item):
    if item["type"] == "registry":
        with winreg.OpenKey(
            item["root"], item["path"], 0, winreg.KEY_SET_VALUE
        ) as key:
            winreg.DeleteValue(key, item["name"])

    elif item["type"] == "file":
        src = item["path"]
        if os.path.exists(src):
            shutil.move(src, src + DISABLED)

def enable(item):
    if item["type"] == "registry":
        with winreg.OpenKey(
            item["root"], item["path"], 0, winreg.KEY_SET_VALUE
        ) as key:
            winreg.SetValueEx(
                key,
                item["name"],
                0,
                item["value_type"],
                item["value"]
            )

    elif item["type"] == "file":
        src = item["path"] + DISABLED
        if os.path.exists(src):
            shutil.move(src, item["path"])
