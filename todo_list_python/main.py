from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import json
from pathlib import Path

app = FastAPI(title="ToDoList EBAC", version="1.0.0")

DATA_FILE = Path(__file__).parent / "data.json"

if not DATA_FILE.exists():
    DATA_FILE.write_text("[]")


class TodoItem(BaseModel):
    id: int
    title: str
    description: str
    done: bool = False

class TodoCreate(BaseModel):
    title: str
    description: str
    done: Optional[bool] = False

def read_data() -> List[dict]:
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def write_data(data: List[dict]):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


@app.get("/todos", response_model=List[TodoItem])
def list_todos():
    return read_data()


@app.post("/todos", response_model=TodoItem)
def create_todo(todo: TodoCreate):
    data = read_data()
    next_id = max((item["id"] for item in data), default=0) + 1

    new_todo = TodoItem(id=next_id, title=todo.title, description=todo.description, done=todo.done)
    data.append(new_todo.dict())
    write_data(data)
    return new_todo


@app.put("/todos/{todo_id}", response_model=TodoItem)
def update_todo(todo_id: int, updated_todo: TodoCreate):
    data = read_data()

    for i, item in enumerate(data):
        if item["id"] == todo_id:
            data[i]["title"] = updated_todo.title
            data[i]["description"] = updated_todo.description
            data[i]["done"] = updated_todo.done
            write_data(data)
            return data[i]

    raise HTTPException(status_code=404, detail="Tarefa não encontrada.")


@app.delete("/todos/{todo_id}")
def delete_todo(todo_id: int):
    data = read_data()
    new_data = [item for item in data if item["id"] != todo_id]

    if len(new_data) == len(data):
        raise HTTPException(status_code=404, detail="Tarefa não encontrada.")

    write_data(new_data)
    return {"message": "Tarefa removida com sucesso."}
