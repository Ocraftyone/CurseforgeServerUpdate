import pathlib
from os import listdir, system
from subprocess import run
from sys import exit
from time import sleep
import platform

from requests import get
from ruamel.yaml import YAML

SERVER_PROPERTIES = "setup/server.properties"

SERVER_SETUP_CONFIG = "server-setup-config.yaml"

system_type = platform.system().lower()
close_key = "C"
clear_command = lambda: print("Error")
if system_type == "windows":
    close_key = "C"
    clear_command = lambda: system("cls")
elif system_type == "linux":
    close_key = "Z"
    clear_command = lambda: system("clear")
key_exist = False
while not key_exist:
    try:
        clear_command.__call__()
        with open("api_key.txt", "r") as file:
            api_key = file.readline()
            if api_key == "":
                raise FileNotFoundError
            key_exist = True
    except FileNotFoundError:
        pathlib.Path("api_key.txt").touch()
        print("Please provide a CFCore API key in the api_key.txt file or paste it below")
        api_key = input(f"Press enter to continue or Ctrl + {close_key} to exit: ")
        if api_key != "":
            with open("api_key.txt", "w") as file:
                file.write(api_key)
        clear_command.__call__()
headers = {
    'Accept': 'application/json',
    'x-api-key': api_key
}

MODPACK_ID = 426926

print("Requesting modpack data...\n")
r = get(f'https://api.curseforge.com/v1/mods/{MODPACK_ID}', headers=headers)

if r.status_code != 200:
    print("Error requesting data from API:", r.status_code)
    exit(1)

json_data = r.json()["data"]
file_id = 0
file_name = ""
game_version = ""
file_url = ""
display_name = ""
for i in json_data["latestFilesIndexes"]:
    if i["gameVersion"] == "1.18.2" and i["releaseType"] == 1:
        file_id = i["fileId"]
        file_name = i["filename"]
        game_version = i["gameVersion"]
        for x in json_data["latestFiles"]:
            if x["id"] == file_id:
                display_name = x["displayName"]
        break

if file_id != 0:
    r = get(f'https://api.curseforge.com/v1/mods/{MODPACK_ID}/files/{file_id}/download-url', headers=headers)
    if r.status_code != 200:
        print("Error requesting data from API:", r.status_code)
        exit(1)
    file_url = str(r.json()["data"]).replace(" ", "+").replace("edge", "media")
else:
    print("API did not provide a valid file ID")
    exit(1)

if file_url != "" and input(
        f"File Name: {file_name}\nMinecraft Version: {game_version}\nFile Url: {file_url}\n\nAre you sure you want to update the server to this version? (y/N) ").lower() == "y":
    with open(SERVER_SETUP_CONFIG, "r") as f:
        yaml = YAML()
        data = yaml.load(f)
        data["install"]["modpackUrl"] = file_url
    with open(SERVER_SETUP_CONFIG, "w") as f:
        yaml.dump(data, f)

    try:
        with open(SERVER_PROPERTIES, "r") as f:
            properties_list = f.readlines()
            for value in properties_list:
                if "motd=" in value:
                    motd_index = properties_list.index(value)
                    break
        properties_list[motd_index] = f"motd=Current Version: {display_name}\n"
        with open(SERVER_PROPERTIES, "w") as f:
            f.writelines(properties_list)
    except FileNotFoundError:
        print("\nserver.properties not found in expected place. skipping...")

    print("\nChange applied. Restart the server to apply the changes.")
    if input("Restart the server now? (y/N) ").lower() == "y":
        files = listdir("/var/run/screen/S-opc")
        found = False
        for file in files:
            if ".mc" in file:
                print(f"Existing session found: {file}")
                found = True
                break
        if found:
            run(["screen", "-S", "mc", "-X", "stuff", "stop\n"])
            print("Allowing server to shutdown...")
            sleep(20)
            print("Starting the server...")
            run(["screen", "-S", "mc", "-X", "stuff", "quit\n"])
        else:
            system("./start")
            run(["screen", "-S", "mc", "-X", "stuff", "quit\n"])
            print("Starting the server...")

    exit("Success")
else:
    exit("Aborting...")
