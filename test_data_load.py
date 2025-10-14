"""Quick diagnostic script to test data loading."""
import sys
import traceback

print("Testing data ingestion...")

try:
    from src.data.ingestion import DataIngestionManager, DataSource
    
    manager = DataIngestionManager()
    print("✓ DataIngestionManager created")
    
    # Test loading provider data
    print("\nAttempting to load PROVIDER_DATA...")
    df = manager.load_data(DataSource.PROVIDER_DATA, show_status=False)
    
    print(f"Result: {len(df)} rows")
    if df.empty:
        print("⚠️  WARNING: DataFrame is empty")
    else:
        print(f"✓ Columns: {list(df.columns)[:5]}...")  # First 5 columns
        
except Exception as e:
    print(f"\n❌ ERROR: {type(e).__name__}: {e}")
    traceback.print_exc()

print("\nTesting providers.py loader...")
try:
    from src.utils.providers import load_and_validate_provider_data
    
    df2 = load_and_validate_provider_data()
    print(f"Result: {len(df2)} rows")
    if df2.empty:
        print("⚠️  WARNING: DataFrame is empty")
    else:
        print(f"✓ Columns: {list(df2.columns)[:5]}...")
        
except Exception as e:
    print(f"\n❌ ERROR: {type(e).__name__}: {e}")
    traceback.print_exc()

print("\nTesting app_logic loader...")
try:
    from src.app_logic import load_application_data
    
    provider_df, referrals_df = load_application_data()
    print(f"Provider result: {len(provider_df)} rows")
    print(f"Referrals result: {len(referrals_df)} rows")
    
    if provider_df.empty:
        print("⚠️  WARNING: Provider DataFrame is empty")
    else:
        print(f"✓ Provider columns: {list(provider_df.columns)[:5]}...")
        
except Exception as e:
    print(f"\n❌ ERROR: {type(e).__name__}: {e}")
    traceback.print_exc()

print("\nDone.")
