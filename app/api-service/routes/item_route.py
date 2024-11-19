from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.item import Item
from services.database import get_db
from pydantic import BaseModel
from typing import List

router = APIRouter()

# Схемы Pydantic для валидации данных
class ItemBase(BaseModel):
    name: str
    description: str

class ItemCreate(ItemBase):
    pass

class ItemOut(ItemBase):
    id: int

    class Config:
        orm_mode = True

# Создание нового элемента
@router.post("/items/", response_model=ItemOut)
def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    db_item = Item(name=item.name, description=item.description)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

# Получение всех элементов
@router.get("/items/", response_model=List[ItemOut])
def read_items(db: Session = Depends(get_db)):
    return db.query(Item).all()

# Получение элемента по ID
@router.get("/items/{item_id}", response_model=ItemOut)
def read_item(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item

# Обновление элемента
@router.put("/items/{item_id}", response_model=ItemOut)
def update_item(item_id: int, item: ItemCreate, db: Session = Depends(get_db)):
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    db_item.name = item.name
    db_item.description = item.description
    db.commit()
    db.refresh(db_item)
    return db_item

# Удаление элемента
@router.delete("/items/{item_id}", response_model=ItemOut)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(db_item)
    db.commit()
    return db_item
