"""SOCcer Worker Module"""
from typing import Literal
from os import cpu_count, path, rename, environ, makedirs
from json import load, dump
from sys import argv
from uuid import uuid4
from datetime import datetime, timezone
from asyncio import create_subprocess_exec, subprocess, run
from boto3 import client
from fastapi import UploadFile
from pydantic import EmailStr
from dotenv import load_dotenv
from utils import get_logger, send_mail, render_template

load_dotenv()

logger = get_logger(__name__)

def get_filepaths(job_id: str, env: dict):
    """ Returns the manifest for a given job """
    models_folder = env.get("MODELS_FOLDER", "models")
    jobs_folder = env.get("JOBS_FOLDER", "jobs")
    job_folder = path.join(jobs_folder, job_id)
    makedirs(job_folder, exist_ok=True)

    return {
        "models": models_folder,
        "jobs": jobs_folder,
        "job": job_folder,  
        "params": path.join(job_folder, "params.json"),
        "input": path.join(job_folder, "input.csv"),
        "results": path.join(job_folder, "results.csv"),
        "results_v1": path.join(job_folder, "SoccerResults-input.csv"),
        "plot": path.join(job_folder, "results.png")
    }

async def create_job(
    model: Literal['1.1', '1.9', '2.0'], 
    file: UploadFile, 
    email: EmailStr, 
    background: bool,
    env: dict
):
    """ Creates a soccer job """

    job_id = str(uuid4())
    filepaths = get_filepaths(job_id, env)
    input_filepath = filepaths["input"]
    params_filepath = filepaths["params"]
    
    if file.size > 10000:
        background = True

    params = {
        "id": job_id,
        "model": model,
        "filename": file.filename,
        "filesize": file.size,
        "email": email,
        "background": bool(background),
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")
    }

    logger.info("Created job %s", job_id)
    logger.info(params)

    # write file to input_filepath
    with open(input_filepath, mode="wb") as input_file:
        input_file.write(await file.read())

    # write params to params_filepath
    with open(params_filepath, mode="w", encoding="utf-8") as params_file:
        dump(params, params_file)

    return job_id

async def submit_job(job_id: str, env: dict):
    """ Submits a job """
    params = get_params(job_id, env)
    
    if params.get('background'):
        logger.info("Running background job %s", job_id)
        return await run_background_soccer(job_id, env)
    
    return await run_soccer(job_id, env)


def get_params(job_id: str, env: dict):
    """ Returns the parameters for a given job """

    filepaths = get_filepaths(job_id, env)

    with open(filepaths["params"], mode="r", encoding="utf-8") as params_file:
        return load(params_file)

async def run_background_soccer(job_id: str, env: dict):
    """ Runs SOCcer in the background """

    command = [ "python3", "worker.py", job_id ]

    if env.get("ECS_WORKER_TASK"):
        ecs_client = client('ecs')
        ecs_client.run_task(
            cluster = env.get("ECS_CLUSTER"),
            count = 1,
            launchType = "FARGATE",
            networkConfiguration = {
                "awsvpcConfiguration": {
                    "securityGroups": env.get("SECURITY_GROUP_IDS").split(","),
                    "subnets": env.get("SUBNET_IDS").split(",")
                }
            },
            taskDefinition = env.get("ECS_WORKER_TASK"),
            overrides = {
                "containerOverrides": [
                    {
                        "name": "worker",
                        "command": command
                    }
                ]
            }
        )
    else:
        soccer_process = await create_subprocess_exec(
            *command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        stdout, stderr = await soccer_process.communicate()

        if soccer_process.returncode != 0:
            raise ValueError(stderr.decode())
        
        return stdout
    
    return True

async def run_soccer(job_id: str, env: dict) -> str:
    """ Runs the SOCcer classifier against the provided job id """

    logger.info("Running SOCcer for job %s", job_id)
    
    filepaths = get_filepaths(job_id, env)
    params = get_params(job_id, env)
    email = params['email']
    model = params['model']

    try:
        args = {
            "1.0": [
                "-Dgov.nih.cit.soccer.wordnet.dir=wordnet",
                f"-Dgov.nih.cit.soccer.output.dir={filepaths['job']}",
                "-cp",
                path.join("jars", "SOCcer-v1.0.jar"),
                "gov.nih.cit.soccer.Soccer",
                filepaths["input"],
                str(cpu_count())
            ],
            "1.9": [
                "-cp",
                path.join("jars", "SOCcer-v2.0.jar"),
                "gov.nih.cit.soccer.SOCcer",
                path.join(filepaths["models"], "soccer-model-v1.9.bin"),
                filepaths["input"],
                filepaths["results"],
                str(cpu_count())
            ],
            "2.0": [
                "-cp",
                path.join("jars", "SOCcer-v2.0.jar"),
                "gov.nih.cit.soccer.SOCcer",
                path.join(filepaths["models"], "soccer-model-v2.0.bin"),
                filepaths["input"],
                filepaths["results"],
                str(cpu_count())
            ]
        }.get(model)

        logger.info("Running command: java %s", " ".join(args))

        soccer_process = await create_subprocess_exec(
            "java", 
            *args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        stdout, stderr = await soccer_process.communicate()
        
        if soccer_process.returncode != 0:
            raise ValueError(stderr.decode())

        if model == "1.0":
            rename(filepaths["results_v1"], filepaths["results"])

        # generate results plot
        plot_process = await create_subprocess_exec(
            "Rscript",
            "plot.R",
            filepaths["results"],
            filepaths["plot"],
        )

        await plot_process.communicate()

        # send email
        if email:
            logger.info("Sending success email to user: %s", email)

            send_mail(
                sender = env.get("EMAIL_ADMIN"),
                recipient = email,
                subject = "SOCcer Results",
                contents = render_template(
                    "templates/user_email.html",
                    {
                        "filename": params["filename"],
                        "model": params["model"],
                        "timestamp": params["timestamp"],
                        "results_url": f"{env.get('BASE_URL')}{env.get('APPLICATION_PATH', '')}?id={job_id}",
                        "email_admin": env.get("EMAIL_ADMIN")
                    }
                ),
                env = env
            )

        return stdout.decode()
    
    except Exception as error:

        logger.exception("Error running SOCcer for job %s", job_id)

        if email:
            # send user error email

            logger.info("Sending error email to user: %s", email)

            send_mail(
                sender = env.get("EMAIL_ADMIN"),
                recipient = email,
                subject = "SOCcer Error",
                contents = render_template(
                    "templates/user_error_email.html",
                    {
                        "filename": params["filename"],
                        "model": params["model"],
                        "timestamp": params["timestamp"],
                        "job_id": params["id"],
                        "email_admin": env.get("EMAIL_ADMIN"),
                        "error": str(error)
                    }
                ),
                env = env
            )

            # send admin error email

            logger.info("Sending error email to admin: %s", env.get("EMAIL_ADMIN"))

            send_mail(
                sender = env.get("EMAIL_ADMIN"),
                recipient = env.get("EMAIL_ADMIN"),
                subject = "SOCcer Error",
                contents = render_template(
                    "templates/admin_error_email.html",
                    {
                        "job_id": params["id"],
                        "params": str(params),
                        "error": str(error),
                        "stdout": str(stdout),
                        "stderr": str(stderr)
                    }
                ),
                env = env
            )
        
        raise error


if __name__ == "__main__":
    job_id = argv[1]
    logger.info("Starting SOCcer worker for job %s", job_id)
    run(run_soccer(job_id, environ))
