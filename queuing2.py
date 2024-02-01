from fastapi import FastAPI
from queue import Queue
from datetime import datetime, timedelta

app = FastAPI()

# Number of machines
num_machines = 3  # Change this to the desired number of machines

# Queues to store users waiting for each machine
user_queues = Queue()

# Dictionary to store user assignments and their wash times for each machine
user_assignments = {machine_id: {} for machine_id in range(num_machines)}


@app.post("/assign_machine")
async def assign_machine(user_name: str, wash_time: int):
    current_time = datetime.now()

    new_user = {
        "user_name": user_name,
        "wash_time": wash_time,
        "arrived_at": current_time,
    }

    # Assign the user to the first available machine
    for machine_id in range(num_machines):
        if not user_assignments[machine_id]:
            user_assignments[machine_id] = {**new_user, "assigned_at": current_time}
            return {
                "message": (
                    f"Assigned machine {machine_id} to user {user_name} for {wash_time} minutes"
                    f" from {current_time.strftime('%I:%M %p')}"
                )
            }

    # If no machine is available, add the user to the queue
    user_queues.put(new_user)

    # For the first user, calculate waiting time based on the user with the shortest wash time
    if user_queues.qsize() == 1:
        shortest_wash_time = min(user_assignments.values(), key=lambda x: x["wash_time"])["wash_time"]
        return {"message": f"Added to queue. Waiting time is {shortest_wash_time} minutes"}

    return {"message": "Added to queue"}


@app.get("/status")
async def check_status():
    # Get current time
    current_time = datetime.now()

    # Loop through the user_assignments
    for i, machine_user in enumerate(user_assignments.values()):
        # If a machine is assigned a user:
        if machine_user:
            # If user's assigned_at + wash_time is before current time:
            if machine_user["assigned_at"] + timedelta(minutes=machine_user["wash_time"]) < current_time:
                # - Remove them
                user_assignments[i] = {}
                # - If anyone is in the queue
                if user_queues.qsize() > 0:
                    #   - Assign the machine to the first person in the queue
                    user_assignments[i] = {**user_queues.get(), "assigned_at": current_time}

    return {
        "user_assignments": user_assignments,
        "user_queues": list(user_queues.queue),
    }


if __name__ == "_main_":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)