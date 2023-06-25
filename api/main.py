from fastapi import FastAPI

app = FastAPI()

@app.get('/test')
async def hello():
    return {'message': 'Running ChronoScheduler!'}

@app.get('/timetable')
async def view_result():
    return {'message': '時間割をいい感じに表示するページ'}