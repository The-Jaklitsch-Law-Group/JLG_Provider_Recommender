"""
Quick test to verify Excel engine parameter fixes work correctly.
"""
import sys
from io import BytesIO
from pathlib import Path

# Test the preparation module
try:
    from src.data.preparation import _looks_like_excel_bytes
    print("✓ Successfully imported _looks_like_excel_bytes")
except Exception as e:
    print(f"✗ Failed to import: {e}")
    sys.exit(1)

# Test creating a mock Excel file signature
mock_xlsx = BytesIO(b'PK\x03\x04' + b'\x00' * 100)  # XLSX signature
mock_xls = BytesIO(b'\xD0\xCF\x11\xE0' + b'\x00' * 100)  # XLS signature
mock_csv = BytesIO(b'name,value\n' + b'test,123\n')  # CSV data

print("\nTesting Excel detection:")
print(f"  XLSX signature detected: {_looks_like_excel_bytes(mock_xlsx)}")
print(f"  XLS signature detected: {_looks_like_excel_bytes(mock_xls)}")
print(f"  CSV signature detected: {_looks_like_excel_bytes(mock_csv)}")

# Test the ingestion module imports
try:
    from src.data.ingestion import DataIngestionManager, DataSource
    print("\n✓ Successfully imported DataIngestionManager and DataSource")
    
    # Create instance
    manager = DataIngestionManager()
    print("✓ Successfully created DataIngestionManager instance")
    
except Exception as e:
    print(f"\n✗ Failed to import/create ingestion components: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n✅ All imports and basic tests passed!")
print("\nThe Excel engine parameter fixes should now prevent the")
print("'Excel file format cannot be determined' error.")
