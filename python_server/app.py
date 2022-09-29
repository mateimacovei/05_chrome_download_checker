from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from file_scanner import read_config_and_get_files, MyFile

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# init
files_found = read_config_and_get_files()


@app.get("/ping", status_code=200)
async def ping():
    return "hi"


@app.get("/refresh", status_code=200)
async def refresh_files():
    # not working
    files_found = read_config_and_get_files()
    return files_found

@app.get("/all", status_code=200)
async def get_all():
    return files_found


@app.get("/contains")
async def find_file_name_containing(name: str):
    return [f for f in files_found if f.name_without_ext.find(name) != -1]
