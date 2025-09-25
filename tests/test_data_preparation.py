import pandas as pd

from src.data.preparation import process_and_save_cleaned_referrals


def test_process_and_save_cleaned_referrals(tmp_path):
    raw_path = tmp_path / "Referrals_App_Full_Contacts.xlsx"
    processed_dir = tmp_path / "processed"

    processed_dir.mkdir(parents=True, exist_ok=True)
    stale_file = processed_dir / "cleaned_inbound_referrals.parquet"
    pd.DataFrame({"Full Name": ["Legacy Provider"], "referral_type": ["legacy"]}).to_parquet(stale_file)

    df = pd.DataFrame(
        [
            {
                "Project ID": 1001,
                "Date of Intake": pd.Timestamp("2024-01-15"),
                "Referral Source": "Referral - Doctor's Office",
                "Referred From Full Name": "Dr. Primary",
                "Referred From's Work Phone": "301-555-1234",
                "Referred From's Work Address": "1 Main St, Annapolis, MD",
                "Referred From's Details: Latitude": "38.9784",
                "Referred From's Details: Longitude": "-76.4922",
                "Secondary Referral Source": "Referral - Doctor's Office",
                "Secondary Referred From Full Name": "Dr. Secondary",
                "Secondary Referred From's Work Phone": "4105550000",
                "Secondary Referred From's Work Address": "2 Side St, Baltimore, MD",
                "Secondary Referred From's Details: Latitude": "39.2904",
                "Secondary Referred From's Details: Longitude": "-76.6122",
                "Dr/Facility Referred To Full Name": "Clinic Destination",
                "Dr/Facility Referred To's Work Phone": "2025559876",
                "Dr/Facility Referred To's Work Address": "10 Care Blvd, Washington, DC",
                "Dr/Facility Referred To's Details: Latitude": "38.9072",
                "Dr/Facility Referred To's Details: Longitude": "-77.0369",
            },
            {
                "Project ID": 1002,
                "Date of Intake": 45500,  # Excel serial date -> 2024-08-09
                "Referral Source": "Referral - Doctor's Office",
                "Referred From Full Name": "Dr. Solo",
                "Referred From's Work Phone": "",
                "Referred From's Work Address": "3 Another Rd, Bowie, MD",
                "Referred From's Details: Latitude": "39.0068",
                "Referred From's Details: Longitude": "-76.7791",
                "Secondary Referral Source": pd.NA,
                "Secondary Referred From Full Name": pd.NA,
                "Secondary Referred From's Work Phone": pd.NA,
                "Secondary Referred From's Work Address": pd.NA,
                "Secondary Referred From's Details: Latitude": pd.NA,
                "Secondary Referred From's Details: Longitude": pd.NA,
                "Dr/Facility Referred To Full Name": "Therapy Partners",
                "Dr/Facility Referred To's Work Phone": pd.NA,
                "Dr/Facility Referred To's Work Address": "20 Wellness Ave, Greenbelt, MD",
                "Dr/Facility Referred To's Details: Latitude": "39.0046",
                "Dr/Facility Referred To's Details: Longitude": "-76.8755",
            },
        ]
    )

    df.to_excel(raw_path, index=False)

    summary = process_and_save_cleaned_referrals(raw_path, processed_dir)

    assert summary.inbound_count == 3  # two primary + one secondary inbound
    assert summary.outbound_count == 2
    assert summary.all_count == 5
    assert summary.issue_records == {}

    inbound = pd.read_parquet(processed_dir / "cleaned_inbound_referrals.parquet")
    outbound = pd.read_parquet(processed_dir / "cleaned_outbound_referrals.parquet")
    combined = pd.read_parquet(processed_dir / "cleaned_all_referrals.parquet")

    assert set(outbound["referral_type"].unique()) == {"outbound"}
    assert set(inbound["referral_type"].unique()) == {"inbound"}
    assert set(combined["referral_type"].unique()) == {"inbound", "outbound"}
    assert "Legacy Provider" not in inbound["Full Name"].values

    formatted_phone = inbound.loc[inbound["Full Name"] == "Dr. Primary", "Work Phone"].iloc[0]
    assert formatted_phone == "(301) 555-1234"

    lat = float(outbound.loc[outbound["Full Name"] == "Clinic Destination", "Latitude"].iloc[0])
    assert lat == 38.9072