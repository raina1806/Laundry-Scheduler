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
completed_users = []


@app.post("/assign_machine")
async def assign_machine(user_name: str, wash_time: int):
    current_time = datetime.now()
    new_user = {
        "user_name": user_name,
        "wash_time": wash_time,
        "arrived_at": current_time.strftime("%I:%M %p"),  # Convert to 12-hour format
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


def update_status():
    # Get current time
    current_time = datetime.now()

    # Loop through the user_assignments
    for i, machine_user in enumerate(user_assignments.values()):
        # If a machine is assigned a user:
        if machine_user:
            # If user's assigned_at + wash_time is before current time:
            if machine_user["assigned_at"] + timedelta(minutes=machine_user["wash_time"]) < current_time:
                completed_users.append(user_assignments[i].get("user_name"))
                # - Remove them
                user_assignments[i] = {}
                # - If anyone is in the queue
                if user_queues.qsize() > 0:
                    #   - Assign the machine to the first person in the queue
                    user_assignments[i] = {**user_queues.get(), "assigned_at": current_time}
                    # Remove the waiting time from the assigned user
                    user_assignments[i].pop("waiting_time", None)
                    user_assignments[i].pop("machine_available_at", None)

    return user_assignments


@app.get("/status")
async def check_status():
    current_time = datetime.now()

    # Update all statuses
    update_status()

    status_response = {
        "user_assignments": user_assignments,
        "user_queues": [],
    }

    # Add waiting time for the first user in the queue
    if user_queues.qsize() > 0:
        shortest_wash_time = min(user_assignments.values(), key=lambda x: x["wash_time"])["wash_time"]
        user_queues.queue[0]["waiting_time"] = shortest_wash_time
        user_queues.queue[0]["machine_available_at"] = (current_time + timedelta(minutes=shortest_wash_time)).strftime(
            "%I:%M %p"
        )  # Add timestamp for waiting time
        status_response["user_queues"] = list(user_queues.queue)

    return status_response


@app.get("/user_status")
async def check_user_status(user_name: str):
    update_status()

    user_status = {"user_name": user_name}

    # Loop through the user_assignments
    for machine_id, machine_user in user_assignments.items():
        # If a machine is assigned a user and it matches the specified user_name:
        if machine_user.get("user_name") == user_name:
            return {
                **user_status,
                "status": f"You are assigned to machine machine: {machine_id}",
                "wash_time": machine_user.get("wash_time"),
                "arrived_at": machine_user.get("arrived_at"),
                "assigned_at": machine_user.get("assigned_at").strftime("%I:%M %p"),
            }

    # If the user is not found in the current assignments, check the queue
    for i, queued_user in enumerate(user_queues.queue):
        if queued_user.get("user_name") == user_name:
            user_status = {
                **user_status,
                "status": f"You are in Queue position {i + 1} ",
                "wash_time": queued_user.get("wash_time"),
                "arrived_at": queued_user.get("arrived_at"),
            }
            if i == 0:
                return {
                    **user_status,
                    "waiting_time": queued_user.get("waiting_time"),
                    "machine_available_at": queued_user.get("machine_available_at"),
                }
            return user_status

    if user_name in completed_users:
        return {"message": "Wash successful. Pick up your clothes"}

    return {"message": "User not found"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)