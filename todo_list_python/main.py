from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, Field, field_validator
from typing import Annotated, Optional
import sqlite3
import secrets
from pathlib import Path

app = FastAPI(title="ToDoList EBAC", version="1.0.0")

DB_FILE = Path(__file__).parent / "todos.db"
TASK_NOT_FOUND_MSG = "Tarefa não encontrada."

security = HTTPBasic()

# Credenciais fixas
USERS = {
    "admin": "admin123",
    "user": "user123"
}


def verify_credentials(credentials: Annotated[HTTPBasicCredentials, Depends(security)]):
    username = credentials.username
    password = credentials.password

    if username not in USERS or not secrets.compare_digest(password, USERS[username]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
            headers={"WWW-Authenticate": "Basic"},
        )

    return username


# =========================================
# DATABASE
# =========================================

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            done BOOLEAN NOT NULL DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()


init_db()

# =========================================
# MODELS
# =========================================

class TodoItem(BaseModel):
    id: int
    title: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=500)
    done: bool = False

    @field_validator('title', 'description')
    @classmethod
    def validate_not_empty_string(cls, v: str) -> str:
        if not v or v.strip() == "":
            raise ValueError("Campo não pode estar vazio")

        return v.strip()


class TodoCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=500)
    done: Optional[bool] = False

    @field_validator('title', 'description')
    @classmethod
    def validate_not_empty_string(cls, v: str) -> str:
        if not v or v.strip() == "":
            raise ValueError("Campo não pode estar vazio")

        return v.strip()


# =========================================
# ROUTES
# =========================================

@app.get("/todos")
def list_todos(
    username: Annotated[str, Depends(verify_credentials)],
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
    order_by: Optional[str] = Query(None),
    order_direction: Optional[str] = Query("asc")
):
    conn = get_connection()

    valid_fields = {"id", "title", "description", "done"}

    query = "SELECT * FROM todos"

    if order_by:
        if order_by not in valid_fields:
            raise HTTPException(
                status_code=400,
                detail=f"Campo '{order_by}' inválido."
            )

        direction = "DESC" if order_direction == "desc" else "ASC"

        query += f" ORDER BY {order_by} {direction}"

    offset = (page - 1) * size

    query += " LIMIT ? OFFSET ?"

    rows = conn.execute(query, (size, offset)).fetchall()

    total = conn.execute("SELECT COUNT(*) FROM todos").fetchone()[0]

    conn.close()

    items = [dict(row) for row in rows]

    return {
        "page": page,
        "size": size,
        "total": total,
        "total_pages": (total + size - 1) // size,
        "items": items
    }


@app.post("/todos", response_model=TodoItem)
def create_todo(
    todo: TodoCreate,
    username: Annotated[str, Depends(verify_credentials)]
):
    conn = get_connection()

    cursor = conn.execute(
        """
        INSERT INTO todos (title, description, done)
        VALUES (?, ?, ?)
        """,
        (todo.title, todo.description, todo.done)
    )

    conn.commit()

    todo_id = cursor.lastrowid

    row = conn.execute(
        "SELECT * FROM todos WHERE id = ?",
        (todo_id,)
    ).fetchone()

    conn.close()

    return dict(row)


@app.get("/todos/{todo_id}", response_model=TodoItem)
def get_todo(
    todo_id: int,
    username: Annotated[str, Depends(verify_credentials)]
):
    conn = get_connection()

    row = conn.execute(
        "SELECT * FROM todos WHERE id = ?",
        (todo_id,)
    ).fetchone()

    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail=TASK_NOT_FOUND_MSG)

    return dict(row)


@app.put("/todos/{todo_id}", response_model=TodoItem)
def update_todo(
    todo_id: int,
    updated_todo: TodoCreate,
    username: Annotated[str, Depends(verify_credentials)]
):
    conn = get_connection()

    cursor = conn.execute(
        """
        UPDATE todos
        SET title = ?, description = ?, done = ?
        WHERE id = ?
        """,
        (
            updated_todo.title,
            updated_todo.description,
            updated_todo.done,
            todo_id
        )
    )

    conn.commit()

    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail=TASK_NOT_FOUND_MSG)

    row = conn.execute(
        "SELECT * FROM todos WHERE id = ?",
        (todo_id,)
    ).fetchone()

    conn.close()

    return dict(row)


@app.delete("/todos/{todo_id}")
def delete_todo(
    todo_id: int,
    username: Annotated[str, Depends(verify_credentials)]
):
    conn = get_connection()

    cursor = conn.execute(
        "DELETE FROM todos WHERE id = ?",
        (todo_id,)
    )

    conn.commit()

    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail=TASK_NOT_FOUND_MSG)

    conn.close()

    return {"message": "Tarefa removida com sucesso."}


@app.patch("/todos/{todo_id}/toggle", response_model=TodoItem)
def toggle_todo_status(
    todo_id: int,
    username: Annotated[str, Depends(verify_credentials)]
):
    conn = get_connection()

    row = conn.execute(
        "SELECT * FROM todos WHERE id = ?",
        (todo_id,)
    ).fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail=TASK_NOT_FOUND_MSG)

    new_status = not bool(row["done"])

    conn.execute(
        "UPDATE todos SET done = ? WHERE id = ?",
        (new_status, todo_id)
    )

    conn.commit()

    updated = conn.execute(
        "SELECT * FROM todos WHERE id = ?",
        (todo_id,)
    ).fetchone()

    conn.close()

    return dict(updated)


@app.get("/todos/status/{status}")
def get_todos_by_status(
    status: str,
    username: Annotated[str, Depends(verify_credentials)]
):
    if status not in ["completed", "pending"]:
        raise HTTPException(
            status_code=400,
            detail="Status deve ser 'completed' ou 'pending'"
        )

    is_done = status == "completed"

    conn = get_connection()

    rows = conn.execute(
        "SELECT * FROM todos WHERE done = ?",
        (is_done,)
    ).fetchall()

    conn.close()

    return {
        "status": status,
        "count": len(rows),
        "todos": [dict(row) for row in rows]
    }