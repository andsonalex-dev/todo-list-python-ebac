TODO List API - EBAC
====================

API REST para gerenciamento de tarefas utilizando **FastAPI** e **Pydantic BaseModel**.

Tecnologias Utilizadas
----------------------

- **Python 3.10+**
- **FastAPI** - Framework web moderno e rápido
- **Pydantic v2** - Validação de dados e serialização
- **Poetry** - Gerenciamento de dependências
- **Uvicorn** - Servidor ASGI

Características do Pydantic Implementadas
-----------------------------------------

- **BaseModel** para todos os modelos de dados
- **Validações customizadas** com field_validator
- **Field** com descrições e validações (min_length, max_length, gt)
- **model_dump()** para serialização (Pydantic v2)
- **Métodos de classe** para operações CRUD
- **Validação automática** de tipos e dados
- **Limpeza automática** de strings (strip)

Instalação
----------

1. Clone o repositório::

    git clone <repo-url>
    cd todo-list-python

2. Instale as dependências::

    poetry install

3. Execute a aplicação::

    poetry run uvicorn todo_list_python.main:app --reload

A API estará disponível em: http://localhost:8000

Documentação da API
------------------

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Endpoints Disponíveis
---------------------

- **GET** ``/todos`` - Lista todas as tarefas
- **POST** ``/todos`` - Cria uma nova tarefa
- **GET** ``/todos/{todo_id}`` - Obtém uma tarefa específica
- **PUT** ``/todos/{todo_id}`` - Atualiza uma tarefa
- **DELETE** ``/todos/{todo_id}`` - Remove uma tarefa
- **PATCH** ``/todos/{todo_id}/toggle`` - Alterna status de conclusão
- **GET** ``/todos/status/{status}`` - Lista tarefas por status (completed/pending)

Modelos de Dados
----------------

**TodoItem**::

    {
        "id": 1,
        "title": "Título da tarefa",
        "description": "Descrição detalhada",
        "done": false
    }

**TodoCreate**::

    {
        "title": "Título da tarefa",
        "description": "Descrição detalhada", 
        "done": false  // opcional
    }

Validações Implementadas
------------------------

- **title**: 1-100 caracteres, não pode estar vazio
- **description**: 1-500 caracteres, não pode estar vazio
- **id**: deve ser maior que 0
- **Limpeza automática**: remoção de espaços extras


Curso EBAC - Projeto atualizado com Pydantic BaseModel