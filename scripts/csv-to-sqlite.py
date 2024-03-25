from datetime import datetime
from sqlmodel import SQLModel, create_engine, Session, select, Relationship
import pandas as pd

from typing import Optional
from datetime import date
from sqlmodel import Field

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
    status: str
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
    status: str

# open the csv files
redeemer_csv = open('data/electoral-bond-redeemers.csv', 'r')
purchaser_csv = open('data/electoral-bond-purchasers.csv', 'r')

# read the csv files
redeemer_df = pd.read_csv(redeemer_csv)
purchaser_df = pd.read_csv(purchaser_csv)

print('Redeemer Data')
print('----------------')
print(redeemer_df.head())

print('Purchaser Data')
print('----------')
print(purchaser_df.head())

# create the database
sqlite_file = 'data/electoral-bond-updated.sqlite'
engine = create_engine(f'sqlite:///{sqlite_file}')

# create the tables
SQLModel.metadata.create_all(engine)

# insert the data
with Session(engine) as session:
    print('Inserting data into the database')
    print('----------------------------------')
    print('Electoral Bond Redeemer Data')
    for index, row in redeemer_df.iterrows():
        beneficiary = EBRedeemer(
            id=row['Sr No.'],
            encashment_date=datetime.strptime(row['Date of Encashment'], '%d/%b/%Y').date(),
            party_name=row['Name of the Political Party'],
            party_account_no=row['Account no. of Political Party'],
            bond_id=f"{row['Prefix']}-{row['Bond Number']}",
            amount=int(row['Denominations'].replace(',', '')),
            branch_code=row['Pay Branch Code'],
            branch_teller=row['Pay Teller']
        )
        session.add(beneficiary)

    print('Electoral Bond Purchaser Data')
    for index, row in purchaser_df.iterrows():
        donor = EBPurchaser(
            id=row['Sr No.'],
            urn=row['Reference No (URN)'],
            journal_date=datetime.strptime(row['Journal Date'], '%d/%b/%Y').date(),
            purchase_date=datetime.strptime(row['Date of Purchase'], '%d/%b/%Y').date(),
            expiry_date=datetime.strptime(row['Date of Expiry'], '%d/%b/%Y').date(),
            purchaser_name=row['Name of the Purchaser'],
            bond_id=f"{row['Prefix']}-{row['Bond Number']}",
            amount=int(row['Denominations'].replace(',', '')),
            branch_code=row['Issue Branch Code'],
            branch_teller=row['Issue Teller'],
            status=row['Status']
        )
        session.add(donor)

    print('Committing the transaction')
    session.commit()

print('-----------------------------------------')
print('Linking the purchaser and redeemer data')
with Session(engine) as session:
    for index, row in purchaser_df.iterrows():
        bond_id = f"{row['Prefix']}-{row['Bond Number']}"
        matching_status = 'Not Matched - No Redeemer Data - Bond Expired/Not Redeemed' if row['Status'] == 'Expired' else 'Matched'
        transaction = MatchingStatus(
            status=matching_status,
            redeemer_id=session.exec(select(EBRedeemer.id).where(EBRedeemer.bond_id == bond_id)).first(),
            purchaser_id=session.exec(select(EBPurchaser.id).where(EBPurchaser.bond_id == bond_id)).first(),
            bond_id=bond_id
        )
        session.add(transaction)
    
    for index, row in redeemer_df.iterrows():
        bond_id = f"{row['Prefix']}-{row['Bond Number']}"
        matching_status = 'Not Matched - No Purchaser Data - Data Unavailable' if not session.get(EBPurchaser, bond_id) else 'Matched'
        if matching_status != 'Matched':
            transaction = MatchingStatus(
                status=matching_status,
                redeemer_id=session.exec(select(EBRedeemer.id).where(EBRedeemer.bond_id == bond_id)).first(),
                bond_id=bond_id
            )
            session.add(transaction)
    session.commit()

print('-----------------------------------------')
print('Merging the data')
with Session(engine) as session:
    transactions = session.exec(select(MatchingStatus)).all()
    for transaction in transactions:
        redeemer = session.exec(select(EBRedeemer).filter(EBRedeemer.id == transaction.redeemer_id)).first()
        purchaser = session.exec(select(EBPurchaser).filter(EBPurchaser.id == transaction.purchaser_id)).first()
        data = Transaction(
            bond_id=transaction.bond_id,
            purchaser_name=purchaser.purchaser_name if purchaser else None,
            party_name=redeemer.party_name if redeemer else None,
            amount=purchaser.amount if purchaser else redeemer.amount,
            encashment_date=redeemer.encashment_date if redeemer else None,
            purchase_date=purchaser.purchase_date if purchaser else None,
            expiry_date=purchaser.expiry_date if purchaser else None,
            status=transaction.status
        )
        session.add(data)
    session.commit()

# close the csv files
redeemer_csv.close()
purchaser_csv.close()
