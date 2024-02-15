from fastapi import FastAPI, HTTPException
from databases import Database
from pydantic import BaseModel
from queue import Queue
from datetime import datetime, timedelta

app = FastAPI()

database_url = "mysql+async://root:my-secret-pw@localhost:3307/mydatabase"

#Create a Database instance
database = Database(database_url)
completed_users = []
#function for connection with the database
async def connect_to_database():
    await database.connect()

#function for disconnection with the database
async def close_database_connection():
    await database.connect()

class UserAssignment(BaseModel):
    user_name: str
    wash_time: int

class QueueUser(BaseModel):
    user_name: str
    wash_time: int
    arrived_at: datetime

MACHINE_NUMBER = 3

@app.post("/assign_machine")
async def assign_machine(request: UserAssignment):
    user_name = request.user_name
    wash_time = request.wash_time
    current_time = datetime.now()

    query_count = "SELECT COUNT(*) FROM user_assignments"
    await connect_to_database()
    count = await database.fetch_val(query_count)
    await close_database_connection()
    
    
    if count<MACHINE_NUMBER:
        assignment_time = datetime.now()
        insert_query = "INSERT INTO user_assignments (user_name, wash_time, arrived_at, assigned_at) VALUES (:username, :wash_time, :arrived_at, :assigned_at);"
        values = {"username": user_name, "wash_time": wash_time, "arrived_at": current_time, "assigned_at": assignment_time}
        await connect_to_database()
        await database.execute(query=insert_query, values=values)
        machine_id_query = "SELECT machine_id FROM user_assignments WHERE user_name = :username;"
        machine_id = await database.fetch_val(machine_id_query, values={"username": user_name})
        await close_database_connection()
        return {
            "message": (
            f"Assigned machine {machine_id} to user {user_name} for {wash_time} minutes"
            f" from {current_time.strftime('%I:%M %p')}"
            )}
    
    if count>=MACHINE_NUMBER:
        queue_add_query = "INSERT INTO user_queue (user_name, wash_time, arrived_at) VALUES (:username, :wash_time, :arrived_at);"
        values= {"username": user_name, "wash_time": wash_time, "arrived_at": current_time}
        await connect_to_database()
        await database.execute(queue_add_query, values)
        await close_database_connection()

        first_user = "SELECT waiting_time FROM user_queue WHERE "

        return {
            "message": ( "user added to queue")
        }
        

async def update_status():
    # Get current time
    current_time = datetime.now()

    # Connect to the database
    await connect_to_database()

    # Fetch user assignments from the database
    query_assignments = "SELECT * FROM user_assignments"
    assignments = await database.fetch_all(query_assignments)

    # Loop through the fetched assignments
    for assignment in assignments:
        machine_user = dict(assignment)
        machine_id = machine_user["machine_id"]

        # If user's assigned_at + wash_time is before current time:
        if machine_user["assigned_at"] + timedelta(minutes=machine_user["wash_time"]) < current_time:
            completed_users.append(machine_user["user_name"])

            # Remove the assignment from the database
            delete_query = "DELETE FROM user_assignments WHERE machine_id = :machine_id"
            await database.execute(delete_query, values={"machine_id": machine_id})

            # Check if anyone is in the queue
            query_queue = "SELECT * FROM user_queue ORDER BY arrived_at"
            queued_users = await database.fetch_all(query_queue)

            if queued_users:
                # Assign the machine to the first person in the queue
                next_user = queued_users[0]
                assign_time = datetime.now()

                insert_assignment_query = """
                    INSERT INTO user_assignments (machine_id, user_name, wash_time, arrived_at, assigned_at)
                    VALUES (:machine_id, :user_name, :wash_time, :arrived_at, :assigned_at)
                """
                values = {
                    "machine_id": machine_id,
                    "user_name": next_user["user_name"],
                    "wash_time": next_user["wash_time"],
                    "arrived_at": next_user["arrived_at"],
                    "assigned_at": assign_time
                }
                await database.execute(insert_assignment_query, values)

                # Remove the user from the queue
                delete_queue_query = "DELETE FROM user_queue WHERE id = :id"
                await database.execute(delete_queue_query, values={"id": next_user["id"]})

    # Close the database connection
    await close_database_connection()

    return completed_users

@app.get("/user_status")
async def check_user_status(user_name: str):

    await update_status()
    await connect_to_database()

    # Check if the user is assigned to a machine
    query_assignment = """
        SELECT machine_id, wash_time, arrived_at, assigned_at
        FROM user_assignments
        WHERE user_name = :user_name
    """
    assignment = await database.fetch_one(query_assignment, {"user_name": user_name})

    if assignment:
        machine_id, wash_time, arrived_at, assigned_at = assignment
        return {
            "user_name": user_name,
            "status": f"You are assigned to machine {machine_id}",
            "wash_time": wash_time,
            "arrived_at": arrived_at,
            "assigned_at": assigned_at.strftime("%I:%M %p")
        }

    # Check if the user is in the queue
    query_queue = """
        SELECT wash_time, arrived_at
        FROM user_queue
        WHERE user_name = :user_name
    """
    queue_user = await database.fetch_one(query_queue, {"user_name": user_name})

    if queue_user:
        wash_time, arrived_at = queue_user
        return {
            "user_name": user_name,
            "status": "You are in the queue",
            "wash_time": wash_time,
            "arrived_at": arrived_at
        }

    # Check if the user has completed their wash
    # query_completed = "SELECT user_name FROM completed_users WHERE user_name = :user_name"
    # completed_user = await database.fetch_one(query_completed, {"user_name": user_name})

    if user_name in completed_users:
        return {"message": "Wash successful. Pick up your clothes"}

    return {"message": "User not found"}




if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
