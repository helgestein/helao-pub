import os
import sys
sys.path.append("../action")
import kadi_action as ka


if __name__ == "__main__":
    ka.url = "http://127.0.0.1:13376"
    ka.addCollection("demo","uploading a bunch of initial echem data to see how it looks","public")
    for filename in os.listdir(r"D:\kadiupload"):
        ident = filename.split("_")[0]
        if not ka.recordExists(ident):
            ka.makeRecordFromFile(filename,r"D:\kadiupload",visibility="public")
        ka.addRecordToCollection("demo",ident)