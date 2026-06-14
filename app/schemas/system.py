from pydantic import BaseModel


class TaxUpdate(BaseModel):
    tax_percent: float