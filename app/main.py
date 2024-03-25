from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from sqlmodel import Session, select

from app.models import EBPurchaser, EBRedeemer, Transaction
from app.database import engine

app = FastAPI()


def get_db():
    with Session(engine) as session:
        yield session


@app.get("/")
def read_root():
    return JSONResponse(content={"message": "Welcome to the Electoral Bond API"})


@app.get("/parties/list")
def get_party_list(db: Session = Depends(get_db)):
    parties = db.exec(select(EBRedeemer.party_name)).unique().all()
    return parties

@app.get("/parties")
def get_parties_summary(db: Session = Depends(get_db)):
    parties = get_party_list(db)
    party_summary = {}
    for party in parties:
        party_summary[party] = get_party_summary(party, db)
    return party_summary

@app.get("/parties/transactions")
def get_party_transactions_summary(db: Session = Depends(get_db)):
    parties = get_party_list(db)
    party_transactions = {}
    for party in parties:
        party_transactions[party] = get_party_transactions(party, db)
    return party_transactions

@app.get("/parties/{party_name}")
def get_party_summary(party_name: str, db: Session = Depends(get_db)):
    party = db.exec(
        select(Transaction).filter(Transaction.party_name == party_name)
    ).all()
    # Summarize the data
    total_amount = 0
    total_transactions = 0
    predata_bonds = 0
    predata_amount = 0
    # Amount Donated by Each Donor
    donor_donations = {}
    for transaction in party:
        if transaction.status == "Matched":
            total_amount += transaction.amount
            total_transactions += 1
            if transaction.purchaser_name in donor_donations:
                donor_donations[transaction.purchaser_name] += transaction.amount
            else:
                donor_donations[transaction.purchaser_name] = transaction.amount
        else:
            predata_bonds += 1
            predata_amount += transaction.amount
    return {
        "total_amount": total_amount,
        "total_transactions": total_transactions,
        "donor_donations": donor_donations,
        "predata_bonds": predata_bonds,
        "predata_amount": predata_amount,
    }

@app.get("/parties/{party_name}/transactions")
def get_party_transactions(party_name: str, db: Session = Depends(get_db)):
    transactions = db.exec(
        select(Transaction).filter(Transaction.party_name == party_name)
    ).all()
    return transactions


@app.get("/donors/list")
def get_donor_list(db: Session = Depends(get_db)):
    donors = db.exec(select(EBPurchaser.purchaser_name)).unique().all()
    return donors

@app.get("/donors")
def get_donors_summary(db: Session = Depends(get_db)):
    donors = get_donor_list(db)
    donor_summary = {}
    for donor in donors:
        donor_summary[donor] = get_donor_summary(donor, db)
    return donor_summary

@app.get("/donors/transactions")
def get_donor_transactions_summary(db: Session = Depends(get_db)):
    donors = get_donor_list(db)
    donor_transactions = {}
    for donor in donors:
        donor_transactions[donor] = get_donor_transactions(donor, db)
    return donor_transactions

@app.get("/donors/{donor_name}")
def get_donor_summary(donor_name: str, db: Session = Depends(get_db)):
    donor = db.exec(
        select(Transaction).filter(Transaction.purchaser_name == donor_name)
    ).all()
    # Summarize the data
    total_amount = 0
    total_transactions = 0
    expired_bonds = 0
    expired_amount = 0
    # Amount Donated to Each Party
    party_donations = {}
    for transaction in donor:
        if transaction.status == "Matched":
            total_amount += transaction.amount
            total_transactions += 1
            if transaction.party_name in party_donations:
                party_donations[transaction.party_name] += transaction.amount
            else:
                party_donations[transaction.party_name] = transaction.amount
        else:
            expired_bonds += 1
            expired_amount += transaction.amount
    return {
        "total_amount": total_amount,
        "total_transactions": total_transactions,
        "party_donations": party_donations,
        "expired_bonds": expired_bonds,
        "expired_amount": expired_amount
    }

@app.get("/donors/{donor_name}/transactions")
def get_donor_transactions(donor_name: str, db: Session = Depends(get_db)):
    transactions = db.exec(
        select(Transaction).filter(Transaction.purchaser_name == donor_name)
    ).all()
    return transactions

@app.get("/bond/{bond_id}")
def read_bond(bond_id: str, db: Session = Depends(get_db)):
    transaction = db.exec(
        select(Transaction).filter(Transaction.bond_id == bond_id)
    ).first()
    if transaction is None:
        return {"message": "Bond not found"}
    redeemer = db.exec(select(EBRedeemer).filter(EBRedeemer.bond_id == bond_id)).first()
    purchaser = db.exec(
        select(EBPurchaser).filter(EBPurchaser.bond_id == bond_id)
    ).first()
    return {"status": transaction.status, "redeemer": redeemer, "purchaser": purchaser}
