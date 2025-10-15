"""Test suite for shared I/O utilities module.

Tests verify that:
- File format detection works correctly
- Excel bytes detection works properly
- Universal data loader handles all input types
- Proper fallback handling for different file formats
"""
import pandas as pd
import pytest
from io import BytesIO
from pathlib import Path

from src.data.io_utils import looks_like_excel_bytes, detect_file_format, load_dataframe


def test_looks_like_excel_bytes_xlsx():
    """Test Excel detection for XLSX files (ZIP format)."""
    # XLSX files start with PK signature (ZIP archive)
    xlsx_signature = b'PK\x03\x04'
    buffer = BytesIO(xlsx_signature + b'\x00' * 100)
    assert looks_like_excel_bytes(buffer) is True
    # Verify buffer position is reset
    assert buffer.tell() == 0


def test_looks_like_excel_bytes_xls():
    """Test Excel detection for XLS files (BIFF format)."""
    # XLS files start with BIFF header
    xls_signature = b'\xD0\xCF\x11\xE0'
    buffer = BytesIO(xls_signature + b'\x00' * 100)
    assert looks_like_excel_bytes(buffer) is True
    # Verify buffer position is reset
    assert buffer.tell() == 0


def test_looks_like_excel_bytes_csv():
    """Test that CSV data is not detected as Excel."""
    csv_data = b'Name,Address,Phone\nJohn Doe,123 Main St,555-1234\n'
    buffer = BytesIO(csv_data)
    assert looks_like_excel_bytes(buffer) is False


def test_looks_like_excel_bytes_empty():
    """Test handling of empty buffer."""
    buffer = BytesIO(b'')
    assert looks_like_excel_bytes(buffer) is False


def test_detect_file_format_csv():
    """Test format detection for CSV files."""
    format_type, engine = detect_file_format(filename="data.csv")
    assert format_type == 'csv'
    assert engine is None


def test_detect_file_format_xlsx():
    """Test format detection for XLSX files."""
    format_type, engine = detect_file_format(filename="data.xlsx")
    assert format_type == 'xlsx'
    assert engine == 'openpyxl'


def test_detect_file_format_xls():
    """Test format detection for XLS files."""
    format_type, engine = detect_file_format(filename="data.xls")
    assert format_type == 'xls'
    assert engine == 'xlrd'


def test_detect_file_format_parquet():
    """Test format detection for Parquet files."""
    format_type, engine = detect_file_format(filename="data.parquet")
    assert format_type == 'parquet'
    assert engine is None


def test_detect_file_format_from_buffer():
    """Test format detection from buffer content when no filename."""
    xlsx_buffer = BytesIO(b'PK\x03\x04' + b'\x00' * 100)
    format_type, engine = detect_file_format(buffer=xlsx_buffer)
    assert format_type == 'xlsx'
    assert engine == 'openpyxl'


def test_load_dataframe_from_dataframe():
    """Test loading from existing DataFrame."""
    original_df = pd.DataFrame({
        'Name ': ['Alice', 'Bob'],  # Note trailing space
        ' Age': [30, 25]  # Note leading space
    })
    
    result_df = load_dataframe(original_df)
    
    # Should normalize column names
    assert 'Name' in result_df.columns
    assert 'Age' in result_df.columns
    assert len(result_df) == 2


def test_load_dataframe_from_csv_path(tmp_path):
    """Test loading from CSV file path."""
    csv_path = tmp_path / "test.csv"
    test_data = pd.DataFrame({
        'Name': ['Alice', 'Bob'],
        'Age': [30, 25]
    })
    test_data.to_csv(csv_path, index=False)
    
    result_df = load_dataframe(csv_path)
    
    assert len(result_df) == 2
    assert 'Name' in result_df.columns
    assert 'Age' in result_df.columns


def test_load_dataframe_from_csv_buffer():
    """Test loading from CSV buffer."""
    csv_data = b'Name,Age\nAlice,30\nBob,25\n'
    buffer = BytesIO(csv_data)
    
    result_df = load_dataframe(buffer, filename="test.csv")
    
    assert len(result_df) == 2
    assert 'Name' in result_df.columns
    assert 'Age' in result_df.columns


def test_load_dataframe_from_bytes():
    """Test loading from raw bytes."""
    csv_data = b'Name,Age\nAlice,30\nBob,25\n'
    
    result_df = load_dataframe(csv_data, filename="test.csv")
    
    assert len(result_df) == 2
    assert 'Name' in result_df.columns
    assert 'Age' in result_df.columns


def test_load_dataframe_file_not_found():
    """Test error handling for missing file."""
    with pytest.raises(FileNotFoundError):
        load_dataframe(Path("/nonexistent/file.csv"))


def test_load_dataframe_column_normalization():
    """Test that whitespace is stripped from column names."""
    # Create DataFrame with messy column names
    df = pd.DataFrame({
        '  Name  ': ['Alice'],
        'Age\t': [30],
        ' \nAddress ': ['123 Main St']
    })
    
    result_df = load_dataframe(df)
    
    # Verify all column names are stripped
    assert 'Name' in result_df.columns
    assert 'Age' in result_df.columns
    assert 'Address' in result_df.columns


def test_load_dataframe_from_parquet(tmp_path):
    """Test loading from Parquet file."""
    parquet_path = tmp_path / "test.parquet"
    test_data = pd.DataFrame({
        'Name': ['Alice', 'Bob'],
        'Age': [30, 25]
    })
    test_data.to_parquet(parquet_path)
    
    result_df = load_dataframe(parquet_path)
    
    assert len(result_df) == 2
    assert 'Name' in result_df.columns
    assert 'Age' in result_df.columns


def test_load_dataframe_unsupported_type():
    """Test error handling for unsupported input type."""
    # Use a truly unsupported type (object with no bytes conversion)
    class UnsupportedType:
        pass
    
    with pytest.raises(TypeError):
        load_dataframe(UnsupportedType())


def test_load_dataframe_memoryview():
    """Test loading from memoryview (Streamlit buffer type)."""
    csv_data = b'Name,Age\nAlice,30\nBob,25\n'
    mv = memoryview(csv_data)
    
    result_df = load_dataframe(mv, filename="test.csv")
    
    assert len(result_df) == 2
    assert 'Name' in result_df.columns


def test_load_dataframe_bytearray():
    """Test loading from bytearray."""
    csv_data = bytearray(b'Name,Age\nAlice,30\nBob,25\n')
    
    result_df = load_dataframe(csv_data, filename="test.csv")
    
    assert len(result_df) == 2
    assert 'Name' in result_df.columns
