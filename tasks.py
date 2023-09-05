#!/usr/bin/env python

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pymongo import MongoClient
from datetime import datetime
from typing import Optional
from uvicorn import run
from uuid import uuid4
from asyncio import sleep

app = FastAPI()

# Mount the "static" folder as a static directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# MongoDB Configuration
client = MongoClient("mongodb://localhost:27017/")
db = client["taskdb"]
collection = db["tasks"]


class TaskModel:
    def __init__(self, name: str, number: int, uuid: Optional[str] = None, start: Optional[datetime] = None,
                 end: Optional[datetime] = None, progress: Optional[int] = None):
        self.id = uuid
        self.name = name
        self.number = number
        self.start = start
        self.end = end
        self.progress = progress


# This "worker" function is run as a BackGroundTask, updating DB with progress
async def count_to_number(task_id: str, number: int, bg_task: BackgroundTasks):
    for i in range(1, number + 1):
        # Update progress in MongoDB
        collection.update_one({"id": task_id}, {"$set": {"progress": i}})
        await sleep(1)
    end_time = datetime.now()
    # Update the end timestamp in MongoDB
    collection.update_one({"id": task_id}, {"$set": {"end": end_time}})


@app.get("/")
async def read_index():
    return FileResponse('static/tasks.html')


@app.get("/favicon.ico")
async def read_favicon():
    return FileResponse('static/task.png')


@app.post("/tasks")
async def create_task(task_data: dict, bg_task: BackgroundTasks):
    name = task_data.get("name")
    number = task_data.get("number")

    # Generate a unique ID for the task
    task_id = str(uuid4())

    # Create a new task document in MongoDB
    task = TaskModel(name=name, number=number, uuid=task_id, start=datetime.now())
    collection.insert_one(task.__dict__)

    # Start the background task to count
    bg_task.add_task(count_to_number, task_id, number, bg_task)

    return {"task_id": task_id}


@app.get("/tasks")
async def get_tasks():
    tasks = list(collection.find({}, {"_id": 0, "id": 1, "name": 1}))
    return tasks


@app.get("/tasks/{task_id}")
async def get_task(task_id: str):
    task = collection.find_one({"id": task_id}, {"_id": 0})
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


# This generator function (note: yield()) produces server-sent events by polling db
@app.get("/tasks/{task_id}/progress")
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


if __name__ == "__main__":
    run("tasks:app", host="127.0.0.1", port=8000, reload=True)
