from datetime import date
from sqlmodel import Field, SQLModel
from typing import Optional


class EBRedeemer(SQLModel, table=True):
    id: int = Field(unique=True)
    encashment_date: date
    party_name: str
    party_account_no: str
    bond_id: str = Field(primary_key=True)
    amount: int
    branch_code: int
    branch_teller: int


class EBPurchaser(SQLModel, table=True):
    id: int = Field(unique=True)
    urn: str
    journal_date: date
    purchase_date: date
    expiry_date: date
    purchaser_name: str
    bond_id: str = Field(primary_key=True)
    amount: int
    branch_code: int
    branch_teller: int
    status: str


class MatchingStatus(SQLModel, table=True):
    status: str  # Either "Matched", "Not Matched - No Redeemer Data - Bond Expired/Not Redeemed" or "Not Matched - No Purchaser Data - Data Unavailable"
    redeemer_id: Optional[int] = Field(default=None, foreign_key="ebredeemer.id")
    purchaser_id: Optional[int] = Field(default=None, foreign_key="ebpurchaser.id")
    bond_id: str = Field(primary_key=True)


class Transaction(SQLModel, table=True):
    bond_id: str = Field(primary_key=True)
    purchaser_name: Optional[str]
    party_name: Optional[str]
    amount: int
    encashment_date: Optional[date]
    purchase_date: Optional[date]
    expiry_date: Optional[date]
    status: str  # Either "Matched", "Not Matched - No Redeemer Data - Bond Expired/Not Redeemed" or "Not Matched - No Purchaser Data - Data Unavailable"
