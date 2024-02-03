from fastapi import FastAPI
from pydantic import BaseModel
from queue import Queue
from datetime import datetime, timedelta
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Number of machines
num_machines = 3
user_queues = Queue()
user_assignments = {machine_id: {} for machine_id in range(num_machines)}

class UserRequest(BaseModel):
    user_name: str
    wash_time: int

@app.post("/assign_machine")
async def assign_machine(request: UserRequest):
    user_name = request.user_name
    wash_time = request.wash_time
    current_time = datetime.now()

    new_user = {
        "user_name": user_name,
        "wash_time": wash_time,
        "arrived_at": current_time,
    }

    for machine_id in range(num_machines):
        if not user_assignments[machine_id]:
            user_assignments[machine_id] = {**new_user, "assigned_at": current_time}
            return {
                "message": (
                    f"Assigned machine {machine_id} to user {user_name} for {wash_time} minutes"
                    f" from {current_time.strftime('%I:%M %p')}"
                )
            }

    user_queues.put(new_user)

    if user_queues.qsize() == 1:
        shortest_wash_time = min(user_assignments.values(), key=lambda x: x["wash_time"])["wash_time"]
        return {"message": f"Added to queue. Waiting time is {shortest_wash_time} minutes"}

    return {"message": "Added to queue"}

@app.get("/status")
async def check_status():
    current_time = datetime.now()

    for i, machine_user in enumerate(user_assignments.values()):
        if machine_user:
            if machine_user["assigned_at"] + timedelta(minutes=machine_user["wash_time"]) < current_time:
                user_assignments[i] = {}
                if user_queues.qsize() > 0:
                    user_assignments[i] = {**user_queues.get(), "assigned_at": current_time}

    return {
        "user_assignments": user_assignments,
        "user_queues": list(user_queues.queue),
    }

if _name_ == "_main_":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
