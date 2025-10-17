from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
import json
from pathlib import Path

app = FastAPI(title="ToDoList EBAC", version="1.0.0")

DATA_FILE = Path(__file__).parent / "data.json"
TASK_NOT_FOUND_MSG = "Tarefa não encontrada."

if not DATA_FILE.exists():
    DATA_FILE.write_text("[]")


class TodoItem(BaseModel):
    id: int = Field(..., description="ID único da tarefa", gt=0)
    title: str = Field(..., description="Título da tarefa", min_length=1, max_length=100)
    description: str = Field(..., description="Descrição da tarefa", min_length=1, max_length=500)
    done: bool = Field(default=False, description="Status de conclusão da tarefa")
    
    @field_validator('title', 'description')
    @classmethod
    def validate_not_empty_string(cls, v: str) -> str:
        if not v or v.strip() == "":
            raise ValueError('Campo não pode estar vazio')
        return v.strip()
    
    @classmethod
    def load_all(cls) -> List['TodoItem']:
        """Carrega todas as tarefas do arquivo JSON"""
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [cls(**item) for item in data]
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    @classmethod
    def save_all(cls, todos: List['TodoItem']) -> None:
        """Salva todas as tarefas no arquivo JSON"""
        data = [todo.model_dump() for todo in todos]
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    @classmethod
    def get_next_id(cls) -> int:
        """Obtém o próximo ID disponível"""
        todos = cls.load_all()
        return max((todo.id for todo in todos), default=0) + 1

class TodoCreate(BaseModel):
    title: str = Field(..., description="Título da tarefa", min_length=1, max_length=100)
    description: str = Field(..., description="Descrição da tarefa", min_length=1, max_length=500)
    done: Optional[bool] = Field(default=False, description="Status de conclusão da tarefa")
    
    @field_validator('title', 'description')
    @classmethod
    def validate_not_empty_string(cls, v: str) -> str:
        if not v or v.strip() == "":
            raise ValueError('Campo não pode estar vazio')
        return v.strip()

def read_data() -> List[TodoItem]:
    """Lê os dados e retorna uma lista de TodoItem"""
    return TodoItem.load_all()


def write_data(todos: List[TodoItem]) -> None:
    """Escreve os dados no arquivo"""
    TodoItem.save_all(todos)


@app.get("/todos", response_model=List[TodoItem])
def list_todos():
    return read_data()


@app.post("/todos", response_model=TodoItem)
def create_todo(todo: TodoCreate):
    """Cria uma nova tarefa"""
    todos = read_data()
    next_id = TodoItem.get_next_id()

    new_todo = TodoItem(
        id=next_id, 
        title=todo.title, 
        description=todo.description, 
        done=todo.done
    )
    todos.append(new_todo)
    write_data(todos)
    return new_todo


@app.put("/todos/{todo_id}", response_model=TodoItem)
def update_todo(todo_id: int, updated_todo: TodoCreate):
    """Atualiza uma tarefa existente"""
    todos = read_data()

    for i, todo in enumerate(todos):
        if todo.id == todo_id:
            # Cria um novo objeto TodoItem com os dados atualizados
            updated = TodoItem(
                id=todo_id,
                title=updated_todo.title,
                description=updated_todo.description,
                done=updated_todo.done
            )
            todos[i] = updated
            write_data(todos)
            return updated

    raise HTTPException(status_code=404, detail=TASK_NOT_FOUND_MSG)


@app.delete("/todos/{todo_id}")
def delete_todo(todo_id: int):
    """Remove uma tarefa"""
    todos = read_data()
    initial_count = len(todos)
    
    todos = [todo for todo in todos if todo.id != todo_id]

    if len(todos) == initial_count:
        raise HTTPException(status_code=404, detail=TASK_NOT_FOUND_MSG)

    write_data(todos)
    return {"message": "Tarefa removida com sucesso."}


@app.get("/todos/{todo_id}", response_model=TodoItem)
def get_todo(todo_id: int):
    """Obtém uma tarefa específica"""
    todos = read_data()
    
    for todo in todos:
        if todo.id == todo_id:
            return todo
    
    raise HTTPException(status_code=404, detail=TASK_NOT_FOUND_MSG)


@app.patch("/todos/{todo_id}/toggle", response_model=TodoItem)
def toggle_todo_status(todo_id: int):
    """Alterna o status de conclusão de uma tarefa"""
    todos = read_data()
    
    for i, todo in enumerate(todos):
        if todo.id == todo_id:
            # Cria um novo objeto com o status invertido
            updated = TodoItem(
                id=todo.id,
                title=todo.title,
                description=todo.description,
                done=not todo.done
            )
            todos[i] = updated
            write_data(todos)
            return updated
    
    raise HTTPException(status_code=404, detail=TASK_NOT_FOUND_MSG)


@app.get("/todos/status/{status}")
def get_todos_by_status(status: str):
    """Obtém tarefas filtradas por status (completed/pending)"""
    if status not in ["completed", "pending"]:
        raise HTTPException(status_code=400, detail="Status deve ser 'completed' ou 'pending'")
    
    todos = read_data()
    is_done = status == "completed"
    filtered_todos = [todo for todo in todos if todo.done == is_done]
    
    return {
        "status": status,
        "count": len(filtered_todos),
        "todos": filtered_todos
    }
