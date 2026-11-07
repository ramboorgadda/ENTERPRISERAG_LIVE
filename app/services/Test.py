
@staticmethod
def add(a: int, b: int) -> int:
    return a + b

from fastapi import FastAPI

app = FastAPI()

@app.get("/add")
def add_endpoint(a: int, b: int) -> int:
    return add(a, b)
