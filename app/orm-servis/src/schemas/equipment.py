# src/schemas/equipment.py


from pydantic import BaseModel


class EquipmentChartRead(BaseModel):
    # Equipment
    serial_number: str
    # HeaterType
    model: str
    price: float
    weight: float
