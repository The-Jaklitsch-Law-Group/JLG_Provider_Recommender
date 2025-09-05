## Convert Excel (XLSX) to Parquet

import pandas as pd

print("Import Complete")

df = pd.read_excel("./data/raw/Referrals_App_Outbound.xlsx")

str_cols = [
    "Dr/Facility Referred To Full Name",
    "Dr/Facility Referred To Address 1 Line 1",
    "Dr/Facility Referred To Address 1 City",
    "Dr/Facility Referred To Address 1 State",
    "Dr/Facility Referred To Address 1 Zip",
    "Dr/Facility Referred To Phone 1",
]

for col in str_cols:
    df[col] = df[col].astype(str)

print("Completed datatype conversion: string")

dt_cols = ["Create Date", "Date of Intake", "Sign Up Date"]

for col in dt_cols:
    df[col] = pd.to_datetime(df[col])

print("Completed datatype conversion: datetime")

num_cols = ["Project ID", "Dr/Facility Referred To's Details: Latitude", "Dr/Facility Referred To's Details: Longitude"]

for col in num_cols:
    df[col] = pd.to_numeric(df[col], downcast="float")

print("Completed datatype conversion: numeric")

df.to_parquet("./data/processed/Referrals_App_Outbound.parquet")
