# Task Progress

An exploration of [Server-sent Events (SSE)](https://dev.to/karanpratapsingh/system-design-long-polling-websockets-server-sent-events-sse-1hip), [MongoDB](https://pymongo.readthedocs.io/en/stable/) and [BackgroundTasks](https://fastapi.tiangolo.com/tutorial/background-tasks/) in [FastAPI](https://fastapi.tiangolo.com/)

### Installation

Python environment required (see [pyenv](https://github.com/pyenv/pyenv#readme) install) then `pip install -r requirements.txt` to get the (few) required libraries.

### Running

In a terminal window, at the command prompt launch the service with `./tasks.py` (or `python tasks.py` if that doesn't work).  As with most FastAPI apps, the endpoints served are available at http://localhost:8000/docs.  

The webpage for demonstrating the server-sent events functionality is served from the URL  http://localhost:8000/ ( which is actually http://localhost:8000/static/tasks.html ).

You just enter a name for the task and how many seconds you want it to run.  Then when you hit the "Create Task" button, a POST request is made to the server to start the task, and the task gives progress feedback every second to an EventSource in JavaScript that is also registered to the progress URL on the server.  When the task is complete, the progress connection is broken and the web page shows the final status.

(Hit the browser refresh button to play again, this is merely a simple demonstration app.)

