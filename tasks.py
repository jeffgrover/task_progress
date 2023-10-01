#!/usr/bin/env python

from io import StringIO
from fastapi import FastAPI, BackgroundTasks, HTTPException, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pymongo import MongoClient
from datetime import datetime
from typing import List, Optional
from uvicorn import run
from uuid import uuid4
from asyncio import sleep
from csv_data import CSV, Buckets, Operations, distribute_data, generate_csv

app = FastAPI()

# Mount the "static" folder as a static directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# MongoDB Configuration
client = MongoClient("mongodb://localhost:27017/")
db = client["taskdb"]
collection = db["tasks"]


class TaskModel:
    def __init__(self, name: str, number: int, id: Optional[str] = None, start: Optional[datetime] = None,
                 end: Optional[datetime] = None, progress: Optional[int] = None):
        self.id = id
        self.name = name
        self.number = number
        self.start = start
        self.end = end
        self.progress = progress


async def count_to_number(task_id: str, number: int, bg_task: BackgroundTasks):
    start_time = datetime.now()
    for i in range(1, number + 1):
        # Update progress in MongoDB
        collection.update_one({"id": task_id}, {"$set": {"progress": i}})
        # Send progress to the browser via SSE (Server Sent Events)
        bg_task.add_task(send_sse_event, task_id, i)
        await sleep(1)
    end_time = datetime.now()
    # Update the end timestamp in MongoDB
    collection.update_one({"id": task_id}, {"$set": {"end": end_time}})


def send_sse_event(task_id: str, progress: int):
    # In a real application, you would use a library like aiohttp to send SSE events to the browser.
    # For simplicity, we'll print the events here.
    print(f"SSE Event for Task {task_id}: Progress {progress}", flush=True)


@app.get("/", tags=["static content"])
async def read_index():
    return FileResponse('static/tasks.html')


@app.get("/favicon.ico", tags=["static content"])
async def read_favicon():
    return FileResponse('static/task.png')


@app.post("/tasks", tags=["tasks"])
async def create_task(task_data: dict, bg_task: BackgroundTasks):
    name = task_data.get("name")
    number = task_data.get("number")

    # Generate a unique ID for the task
    task_id = str(uuid4())

    # Create a new task document in MongoDB
    task = TaskModel(name=name, number=number, id=task_id, start=datetime.now())
    collection.insert_one(task.__dict__)

    # Start the background task to count
    bg_task.add_task(count_to_number, task_id, number, bg_task)

    return {"task_id": task_id}


@app.get("/tasks", tags=["tasks"])
async def get_tasks():
    tasks = list(collection.find({}, {"_id": 0, "id": 1, "name": 1}))
    return tasks


@app.get("/tasks/{task_id}", tags=["tasks"])
async def get_task(task_id: str):
    task = collection.find_one({"id": task_id}, {"_id": 0})
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return 


@app.get("/tasks/{task_id}/progress", tags=["tasks"])
async def task_progress_sse(task_id: str):
    async def sse_stream():
        max_number_reached = False
        while not max_number_reached:
            task = collection.find_one({"id": task_id}, {"_id": 0})
            if task is None or task.get("progress") is None:
                yield "data: Task not found or progress not available\n\n"
            else:
                progress = task["progress"]
                yield f"data: {progress}\n\n"

                # Check if the maximum number has been reached
                max_number = task["number"]
                if progress >= max_number:
                    max_number_reached = True

            await sleep(1)

        # Send a final SSE event to signal the end
        yield "data: Task completed\n\n"

    return StreamingResponse(sse_stream(), media_type="text/event-stream")


#-----------------------------------------------------------------------------------------------------------
@app.post(
    "/csv",
    description="Generate synthetic .csv data",
    tags=["csv data"],
    response_class=FileResponse,
    responses={400: {}},
)
def generate_sample_csv(csv_params: CSV):

    # TODO:  Write CSV directly to StreamingResponse in generator code
    # Something like this:
    # response = StreamingResponse(iter([stream.getvalue()]),
    #                              media_type="text/csv"
    #                             )
    # response.headers["Content-Disposition"] = "attachment; filename=export.csv"
    # return response
    # Debug:
    # return StreamingResponse(iter(StringIO("RECEIVED:\n\n" + json.dumps(sample, default=str, indent=2))))

    content = generate_csv(csv_params)
    response = StreamingResponse(content, media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=sample-data.csv"
    return response


@app.post(
    "/hist",
    description="Compute histogram distribution on sample .csv data",
    tags=["csv data"],
    response_model=Buckets,
    responses={400: {}},
)
def distribute_csv_data(file: UploadFile, operation: Operations, entities: str, values :str, num_buckets: int = 100):
    contents = file.file.read()
    buffer = StringIO(contents.decode('utf-8'))
    labels, values = distribute_data(buffer, operation, entities, values, num_buckets)
    response = Buckets(names=list(labels), counts=list(values))
    return response

if __name__ == "__main__":
   run("tasks:app", host="127.0.0.1", port=8000, reload=True)
