from fastapi import HTTPException

def ensure_capacity(current: int, capacity: int, allow_over_capacity: bool = False, resource: str = "recurso") -> None:
    if current >= capacity and not allow_over_capacity:
        raise HTTPException(409, f"A capacidade de {resource} foi atingida. Confirme explicitamente para excedê-la.")
