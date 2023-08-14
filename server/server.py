""" SOCcer API """
from typing import Annotated, Literal
from os import environ, makedirs
from fastapi import FastAPI, Form, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import EmailStr
from dotenv import load_dotenv
from worker import create_job, submit_job
from utils import get_logger

load_dotenv()
app = FastAPI(
    title = "SOCcer API",
    version = "2.3.6",
    openapi_url = "/api/openapi.json",
    docs_url = "/api/docs",
)
logger = get_logger(__name__)


# Mounts the jobs folder to the /jobs endpoint
jobs_folder = environ.get("JOBS_FOLDER", "jobs")
makedirs(jobs_folder, exist_ok=True)
app.mount("/api/jobs", StaticFiles(directory = jobs_folder))


@app.exception_handler(Exception)
async def default_exception_handler(request, exc: Exception):
    """ Handles all uncaught exceptions """
    logger.error(str(exc))
    return JSONResponse({"error": "Invalid parameters"}, status_code=400)


@app.get("/api/ping")
async def ping():
    """ Health check endpoint """
    return True


@app.post("/api/submit")
async def submit(
    model: Annotated[Literal['1.0', '1.9', '2.0'], Form()],
    file: Annotated[UploadFile, File()],
    email: Annotated[EmailStr, Form()] = None,
    background: Annotated[bool, Form()] = None,
):
    """ Creates and submits a job """
    job_id = await create_job(model, file, email, background, environ)
    await submit_job(job_id, environ)
    return {"id": job_id}
