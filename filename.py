from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI()

class Machine:
    def __init__(self, id):
        self.id = id
        self.allocated_user = None
        self.waiting_time = 0

n_machines = 3
machines = [Machine(i) for i in range(n_machines)]
queue = []

class UserRequest(BaseModel):
    user_name: str
    wash_time: int  # Time it would take for their wash

@app.post("/user")
def user_arrival(request: UserRequest):
    user = request.user_name
    wash_time = request.wash_time

    available_machine = find_available_machine()
    if available_machine is not None:
        allocate_machine(user, wash_time, available_machine)
        return {"message": f"{user} allocated Machine-{available_machine.id}"}
    else:
        queue.append((user, wash_time))
        return {"message": f"{user} added to the queue"}

@app.post("/machine/release")
def machine_release():
    for machine in machines:
        if machine.allocated_user is not None:
            released_user = machine.allocated_user
            machine.allocated_user = None
            machine.waiting_time = 0
            schedule_next_wash()
            return {"message": f"{released_user} released Machine-{machine.id}"}
    return {"message": "No machines to release"}

def find_available_machine():
    for machine in machines:
        if machine.allocated_user is None:
            return machine
    return None

def allocate_machine(user, wash_time, machine):
    machine.allocated_user = user
    machine.waiting_time = wash_time
    schedule_next_wash()

def schedule_next_wash():
    queue.sort(key=lambda x: x[1])  # Sort the queue based on wash_time
    for machine in machines:
        if machine.allocated_user is None and queue:
            next_user, wash_time = queue.pop(0)
            allocate_machine(next_user, wash_time, machine)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
