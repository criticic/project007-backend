import tabula
import pandas as pd

# Read the PDF file
redeemerPDF = 'data/electoral-bond-redeemers.pdf'
purchaserPDF = 'data/electoral-bond-purchasers.pdf'

# Extract the tables from the PDF
redeemerTables = tabula.read_pdf(redeemerPDF, pages='all', multiple_tables=True)
purchaserTables = tabula.read_pdf(purchaserPDF, pages='all', multiple_tables=True)

# Merge tables into a single dataframe
redeemeryDF = pd.concat(redeemerTables)
purchaserDF = pd.concat(purchaserTables)

# Save the data as csv
redeemeryDF.to_csv('data/electoral-bond-redeemers.csv', index=False)
purchaserDF.to_csv('data/electoral-bond-purchasers.csv', index=False)