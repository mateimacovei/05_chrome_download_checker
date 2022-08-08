import json
from os import listdir
from os.path import isfile, isdir, join


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
    files = [MyFile(path, f) for f in listdir(path) if isfile(join(path, f))]
    return [f for f in files if f.name_without_ext != ""]


def get_directories_in_folder(path: str):
    contents = [join(path, f) for f in listdir(path)]
    directories = [d for d in contents if isdir(d)]
    return directories


def recursive_get_files(directory: str, recursive: bool):
    files_found = get_files_in_folder(directory)

    if(recursive):
        folders_to_scan = get_directories_in_folder(directory)

        # an empty list is evaluated to false
        while folders_to_scan:
            current_dir = folders_to_scan.pop()
            files_found.extend(get_files_in_folder(current_dir))
            folders_to_scan.extend(get_directories_in_folder(current_dir))

    return files_found


def read_config_and_get_files():
    config = load_json('config/folders.json')

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
