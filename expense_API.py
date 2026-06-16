from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status, Depends
from pydantic import BaseModel
from typing import Optional
import sqlite3

DB_PATH = "expenses.db"



def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # دسترسی به ستون‌ها با نام
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT    NOT NULL,
            amount      REAL    NOT NULL
        )
    """)
    conn.commit()
    conn.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()   # startup
    yield # shutdown


app = FastAPI(
    title="Expense Manager API",
    description="مدیریت هزینه‌ها با SQLite",
    version="2.0.0",
    lifespan=lifespan,
)


# --- Schemas ---

class ExpenseCreate(BaseModel):
    description: str
    amount: float


class ExpenseUpdate(BaseModel):
    description: Optional[str] = None
    amount: Optional[float] = None


class ExpenseResponse(BaseModel):
    id: int
    description: str
    amount: float


# --- Routes ---

@app.post(
    "/expenses",
    response_model=ExpenseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="ایجاد هزینه جدید",
)
def create_expense(expense: ExpenseCreate, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.execute(
        "INSERT INTO expenses (description, amount) VALUES (?, ?)",
        (expense.description, expense.amount),
    )
    db.commit()
    row = db.execute(
        "SELECT * FROM expenses WHERE id = ?", (cursor.lastrowid,)
    ).fetchone()
    return dict(row)


@app.get(
    "/expenses",
    response_model=list[ExpenseResponse],
    status_code=status.HTTP_200_OK,
    summary="دریافت همه هزینه‌ها",
)
def get_all_expenses(db: sqlite3.Connection = Depends(get_db)):
    rows = db.execute("SELECT * FROM expenses").fetchall()
    return [dict(row) for row in rows]


@app.get(
    "/expenses/{expense_id}",
    response_model=ExpenseResponse,
    status_code=status.HTTP_200_OK,
    summary="دریافت یک هزینه با شناسه",
)
def get_expense(expense_id: int, db: sqlite3.Connection = Depends(get_db)):
    row = db.execute(
        "SELECT * FROM expenses WHERE id = ?", (expense_id,)
    ).fetchone()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"هزینه با شناسه {expense_id} یافت نشد.",
        )
    return dict(row)


@app.put(
    "/expenses/{expense_id}",
    response_model=ExpenseResponse,
    status_code=status.HTTP_200_OK,
    summary="ویرایش یک هزینه با شناسه",
)
def update_expense(
    expense_id: int,
    updates: ExpenseUpdate,
    db: sqlite3.Connection = Depends(get_db),
):
    row = db.execute(
        "SELECT * FROM expenses WHERE id = ?", (expense_id,)
    ).fetchone()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"هزینه با شناسه {expense_id} یافت نشد.",
        )

    current = dict(row)
    new_description = updates.description if updates.description is not None else current["description"]
    new_amount = updates.amount if updates.amount is not None else current["amount"]

    db.execute(
        "UPDATE expenses SET description = ?, amount = ? WHERE id = ?",
        (new_description, new_amount, expense_id),
    )
    db.commit()

    updated = db.execute(
        "SELECT * FROM expenses WHERE id = ?", (expense_id,)
    ).fetchone()
    return dict(updated)


@app.delete(
    "/expenses/{expense_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="حذف یک هزینه با شناسه",
)
def delete_expense(expense_id: int, db: sqlite3.Connection = Depends(get_db)):
    row = db.execute(
        "SELECT id FROM expenses WHERE id = ?", (expense_id,)
    ).fetchone()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"هزینه با شناسه {expense_id} یافت نشد.",
        )

    db.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    db.commit()