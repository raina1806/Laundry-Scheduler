from fastapi import FastAPI, HTTPException
from typing import Optional
from queue import Queue
import time

app = FastAPI()

# Number of machines
num_machines = 3  # Change this to the desired number of machines

# Queues to store users waiting for each machine
user_queues = {machine_id: Queue() for machine_id in range(num_machines)}

# Dictionary to store user assignments and their wash times for each machine
user_assignments = {machine_id: {} for machine_id in range(num_machines)}


@app.post("/assign_machine/{user_name}")
async def assign_machine(user_name: str, wash_time: int):
    # Assign the user to the first available machine or add to the queue
    for machine_id in range(num_machines):
        if not user_assignments[machine_id]:
            timestamp = int(time.time())
            user_assignments[machine_id] = {"user_name": user_name, "wash_time": wash_time, "timestamp": timestamp}
            return {"message": f"Assigned machine {machine_id} to user {user_name} for {wash_time} minutes"}

    # If no machine is available, add the user to the queue
    timestamp = int(time.time())
    user_queues[0].put({"user_name": user_name, "wash_time": wash_time, "timestamp": timestamp})

    # Calculate waiting time based on the user with the shortest wash time
    if user_queues[0].qsize() == 1:
        shortest_wash_time = min(entry["wash_time"] for entry in user_assignments.values() if entry) if \
        user_assignments[0] else float('inf')
        waiting_time = shortest_wash_time * user_queues[0].qsize()
        return {"message": f"Added to queue. Waiting time is {waiting_time} minutes"}

    return {"message": "Added to queue"}


@app.post("/finish_washing/{machine_id}")
async def finish_washing(machine_id: int):
    if machine_id < 0 or machine_id >= num_machines:
        raise HTTPException(status_code=400, detail="Invalid machine_id")

    if not user_assignments[machine_id]:
        raise HTTPException(status_code=400, detail=f"No user assigned to machine {machine_id}")

    # Get the user who finished washing
    finished_user = user_assignments[machine_id].pop("user_name")
    wash_time = user_assignments[machine_id].pop("wash_time")

    # Check if there are users in the queue
    if not user_queues[0].empty():
        # Get the next user in the queue
        next_user = user_queues[0].get()
        user_assignments[machine_id] = next_user
        next_user_name = next_user["user_name"]
        next_user_wash_time = next_user["wash_time"]

        return {
            "message": f"Finished washing. Machine {machine_id} available. Next user: {next_user_name}. Wash time: {next_user_wash_time} minutes"}

    return {"message": f"Finished washing. No users in the queue for machine {machine_id}. Machine available."}


@app.get("/status")
async def check_status():
    status = {"user_assignments": user_assignments, "user_queues": {k: list(q.queue) for k, q in user_queues.items()}}
    return status


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)