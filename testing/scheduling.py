from fastapi import BackgroundTasks, Depends, FastAPI
import uvicorn
import time
app = FastAPI()

def doMeasurement(message: str):
    time.sleep(10)
    print('did measuremen {}'.format(message))

@app.post("/send-notification/{message}")
def sendMeasurement(message: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(doMeasurement, message)
    return {"message": message}

if __name__ == "__main__":
    uvicorn.run(app, host='127.0.0.1', port=12345)


#this should work with an action where code is properly blocking. this dry run executes things in the right order at least
