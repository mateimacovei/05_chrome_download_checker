import json
import os
from pathlib import Path


def is_windows_drive_path(path: str):
    return len(path) >= 3 and path[0].isalpha() and path[1] == ':' and path[2] in ('\\', '/')


def filter_config_for_os(config, os_name: str):
    if os_name == 'nt':
        return [entry for entry in config if is_windows_drive_path(entry['folder'])]

    return [entry for entry in config if entry['folder'].startswith('/')]


class MyFile:
    def __init__(self, path: str, name: str) -> None:
        self.path = path
        self.name = name
        self.name_without_ext = name.rsplit('.', maxsplit=1)[0]

    def __str__(self) -> str:
        return self.path+" "+self.name+" "+self.name_without_ext+"\n"


def load_json(path: str):
    json_file = open(path)
    data = json.load(json_file)
    json_file.close()
    return data


def get_files_in_folder(path: str):
    files = []
    try:
        with os.scandir(path) as entries:
            for entry in entries:
                try:
                    if entry.is_file():
                        file = MyFile(path, entry.name)
                        if file.name_without_ext != "":
                            files.append(file)
                except OSError:
                    continue
    except OSError:
        return []

    return files


def get_directories_in_folder(path: str):
    directories = []
    try:
        with os.scandir(path) as entries:
            for entry in entries:
                try:
                    if entry.is_dir(follow_symlinks=False):
                        directories.append(entry.path)
                except OSError:
                    continue
    except OSError:
        return []

    return directories


def recursive_get_files(directory: str, recursive: bool):
    files_found = []
    folders_to_scan = [directory]
    visited_dirs = set()

    # an empty list is evaluated to false
    while folders_to_scan:
        current_dir = folders_to_scan.pop()
        real_dir = os.path.realpath(current_dir)
        if real_dir in visited_dirs:
            continue
        visited_dirs.add(real_dir)

        files_found.extend(get_files_in_folder(current_dir))

        if(recursive):
            folders_to_scan.extend(get_directories_in_folder(current_dir))

    return files_found


def read_config_and_get_files():
    config_path = Path(__file__).resolve().parent / 'config' / 'folders.json'
    config = filter_config_for_os(load_json(config_path), os.name)

    files_found = []
    for folder_to_read in config:
        files_found.extend(recursive_get_files(
            folder_to_read['folder'], folder_to_read['recursive']))

    print("read all files")
    return files_found


# 'config/folders.json'
if __name__ == "__main__":
    from os import curdir

    data = load_json('config/folders_model.json')
    print("folder in model data", data[0]['folder'])

    print('rec files in current dir: ', [
          f.name_without_ext for f in recursive_get_files(curdir, True)])
    print('folders in current dir: ', get_directories_in_folder(curdir))
    # print([f.name_without_ext for f in recursive_get_files("E:\\01_Vault\\Phone photos", True)])
