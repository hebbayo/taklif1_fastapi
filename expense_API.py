from fastapi import FastAPI, HTTPException,status
from pydantic import BaseModel
from typing import Optional

app= FastAPI(
    title="Expense manager API",
    description="مدیریت هزینه ها بدون دیتابیس -ذخیره سازی در حافظه",
    version="1.0.0",
)


expenses: dict[int, dict]={}

next_id: int=1



class ExpenseCreate(BaseModel):
    description:str
    amount: float
    
    
    
class ExpenseUpdate(BaseModel):
    description: Optional[str]=None
    amount: Optional[float]=None
    
class ExpenseResponse(BaseModel):
    id:int
    description: str
    amount: float
    
    
    
@app.post("/expenses",response_model=ExpenseResponse,status_code=status.HTTP_201_CREATED,summary="ایجاد هزینه جدید")
def create_expense(expense:ExpenseCreate):
    global next_id
    
    new_expense={
        "id":next_id,
        "description":expense.description,
        "amount":expense.amount,        
    }
    expenses[next_id]= new_expense
    next_id+=1
    
    return new_expense

@app.get("/expenses",response_model=list[ExpenseResponse],status_code=status.HTTP_200_OK,
         summary="دریافت همه هزینه ها",)


def get_all_expenses():
    return list(expenses.values())



@app.get("/expenses/{expense_id}",
         response_model=ExpenseResponse,status_code=status.HTTP_200_OK,summary="دریافت یک هزینه با شناسه",)
def get_expense(expense_id: int):
    expense= expenses.get(expense_id)
    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"هزینه با شناسه {expense_id}یافت نشد",)
    return expense


@app.put("/expenses/{expense_id}",
         response_model=ExpenseResponse,
         status_code=status.HTTP_200_OK,summary="ویرایش یک هزینه با شناسه",)
def update_expense(expense_id:int,updates:ExpenseUpdate):
    expense= expenses.get(expense_id)
    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"هزینه با شناسه {expense_id}یافت نشد.")
    if updates.description is not None:
        expense["description"]=updates.description
    if updates.amount is not None:
        expense["amount"]= updates.amount
            
    return  expense

@app.delete("/expenses/{expense_id:}",status_code=status.HTTP_204_NO_CONTENT,summary="حذف یک هزینه با شناسه",)
def delete_expense(expense_id:int):
    if expense_id not in expenses:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"هزینه با شناسه {expense_id} یافت نشد",)
    del expenses[expense_id]