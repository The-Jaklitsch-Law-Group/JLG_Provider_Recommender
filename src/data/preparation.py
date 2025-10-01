"""Utilities for preparing cleaned referral datasets from raw Excel exports."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, MutableMapping, Optional, Sequence, Union, cast, overload, BinaryIO
from io import BytesIO

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class PreparationSummary:
    """Summary metadata returned after regenerating cleaned datasets."""

    inbound_count: int
    outbound_count: int
    all_count: int
    saved_files: MutableMapping[str, Path] = field(default_factory=dict)
    skipped_configs: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    issue_records: MutableMapping[str, pd.DataFrame] = field(default_factory=dict)


@dataclass(slots=True)
class PreferredProvidersSummary:
    """Summary metadata returned after processing preferred providers data."""

    total_count: int
    cleaned_count: int
    missing_geo_count: int
    saved_file: Optional[Path] = None
    missing_records: Optional[pd.DataFrame] = None
    warnings: List[str] = field(default_factory=list)


_PHONE_DIGITS = 10
_EXCEL_ORIGIN = "1899-12-30"


def _clean_phone_number(value: Any) -> Any:
    if pd.isna(value):
        return pd.NA
    digits = "".join(ch for ch in str(value) if ch.isdigit())
    if len(digits) == _PHONE_DIGITS:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    stripped = str(value).strip()
    return stripped or pd.NA


def _clean_address(value: Any) -> Any:
    if pd.isna(value):
        return pd.NA
    text = str(value).strip()
    if not text:
        return pd.NA
    text = text.replace(", ,", ",").replace("  ", " ")
    return text


def _clean_geocode(value: Any) -> float:
    if pd.isna(value):
        return np.nan
    try:
        coerced = float(str(value).replace("--", "-"))
    except (TypeError, ValueError):
        return np.nan
    if -180 <= coerced <= 180:
        return coerced
    return np.nan


def _normalize_date_series(series: pd.Series) -> pd.Series:
    if series is None:
        return pd.Series(dtype="datetime64[ns]")
    series = series.copy()
    # First try direct conversion (handles pandas/ISO timestamps)
    converted = pd.to_datetime(series, errors="coerce")

    # Attempt Excel serial conversion for numeric leftovers
    if converted.isna().any():
        numeric_mask = series.apply(lambda x: isinstance(x, (int, float))) & series.notna()
        if numeric_mask.any():
            converted_numeric = pd.to_datetime(series[numeric_mask], unit="D", origin=_EXCEL_ORIGIN, errors="coerce")
            converted.loc[numeric_mask] = converted_numeric

    return converted


def _select_and_rename(df: pd.DataFrame, column_mapping: Mapping[str, str]) -> tuple[pd.DataFrame, List[str]]:
    selected = pd.DataFrame(index=df.index)
    missing_sources: List[str] = []
    for source_col, target_col in column_mapping.items():
        if source_col in df.columns:
            selected[target_col] = df[source_col]
        else:
            selected[target_col] = pd.Series(pd.NA, index=df.index)
            missing_sources.append(source_col)
    return selected, missing_sources


def _clean_referral_frame(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if "Work Phone" in df.columns:
        df["Work Phone"] = df["Work Phone"].map(_clean_phone_number)
    if "Work Address" in df.columns:
        df["Work Address"] = df["Work Address"].map(_clean_address)
    if "Latitude" in df.columns:
        df["Latitude"] = df["Latitude"].map(_clean_geocode)
    if "Longitude" in df.columns:
        df["Longitude"] = df["Longitude"].map(_clean_geocode)

    if "Date of Intake" in df.columns:
        df.sort_values(by=["Date of Intake", "Full Name"], inplace=True, na_position="last")
        try:
            df.set_index("Date of Intake", inplace=True)
        except KeyError:
            pass

    return df


def _apply_filters(df: pd.DataFrame, filters: Optional[Sequence[Callable[[pd.DataFrame], pd.Series]]]) -> pd.DataFrame:
    if not filters:
        return df

    filtered = df
    for filter_fn in filters:
        mask = filter_fn(filtered)
        if not isinstance(mask, pd.Series):
            mask = pd.Series(mask, index=filtered.index)
        mask = mask.fillna(False).astype(bool)
        filtered = filtered.loc[mask]

    return filtered


def _process_referral_data(
    df_all: pd.DataFrame,
    column_mapping: Mapping[str, str],
    filters: Optional[Sequence[Callable[[pd.DataFrame], pd.Series]]] = None,
) -> tuple[pd.DataFrame, List[str]]:
    selected, missing = _select_and_rename(df_all, column_mapping)
    selected = _apply_filters(selected, filters)
    selected = _clean_referral_frame(selected)
    return selected, missing


_REFERRAL_CONFIGS: Dict[str, Dict[str, Any]] = {
    "primary_inbound": {
        "columns": {
            "Project ID": "Project ID",
            "Date of Intake": "Date of Intake",
            "Referral Source": "Referral Source",
            "Referred From Full Name": "Full Name",
            "Referred From's Work Phone": "Work Phone",
            "Referred From's Work Address": "Work Address",
            "Referred From's Details: Latitude": "Latitude",
            "Referred From's Details: Longitude": "Longitude",
        },
        "filters": [
            lambda df: df["Referral Source"] == "Referral - Doctor's Office",
            lambda df: df["Full Name"].notna(),
            lambda df: df["Work Address"].notna(),
        ],
    },
    "secondary_inbound": {
        "columns": {
            "Project ID": "Project ID",
            "Date of Intake": "Date of Intake",
            "Secondary Referral Source": "Referral Source",
            "Secondary Referred From Full Name": "Full Name",
            "Secondary Referred From's Work Phone": "Work Phone",
            "Secondary Referred From's Work Address": "Work Address",
            "Secondary Referred From's Details: Latitude": "Latitude",
            "Secondary Referred From's Details: Longitude": "Longitude",
        },
        "filters": [
            lambda df: df["Referral Source"] == "Referral - Doctor's Office",
            lambda df: df["Full Name"].notna(),
            lambda df: df["Work Address"].notna(),
        ],
    },
    "outbound": {
        "columns": {
            "Project ID": "Project ID",
            "Date of Intake": "Date of Intake",
            "Dr/Facility Referred To Full Name": "Full Name",
            "Dr/Facility Referred To's Work Phone": "Work Phone",
            "Dr/Facility Referred To's Work Address": "Work Address",
            "Dr/Facility Referred To's Details: Latitude": "Latitude",
            "Dr/Facility Referred To's Details: Longitude": "Longitude",
        },
        "filters": [lambda df: df["Full Name"].notna()],
    },
}


def _normalize_input_dataframe(df_all: pd.DataFrame) -> pd.DataFrame:
    df_all = df_all.copy()

    if "Date of Intake" in df_all.columns:
        df_all["Date of Intake"] = _normalize_date_series(df_all["Date of Intake"])

    if "Create Date" in df_all.columns:
        df_all["Create Date"] = _normalize_date_series(df_all["Create Date"])

    if "Date of Intake" in df_all.columns and "Create Date" in df_all.columns:
        df_all["Date of Intake"] = df_all["Date of Intake"].fillna(df_all["Create Date"])

    return df_all


def _combine_inbound(primary: pd.DataFrame, secondary: pd.DataFrame) -> pd.DataFrame:
    if primary.empty and secondary.empty:
        return pd.DataFrame(columns=primary.columns if not primary.empty else secondary.columns)
    combined = pd.concat([primary, secondary], ignore_index=False)
    combined["referral_type"] = "inbound"
    if "Referral Source" not in combined.columns:
        combined["Referral Source"] = "Referral - Doctor's Office"
    else:
        combined["Referral Source"] = combined["Referral Source"].fillna("Referral - Doctor's Office")
    return combined


def _prepare_outbound(outbound: pd.DataFrame) -> pd.DataFrame:
    outbound = outbound.copy()
    if outbound.empty:
        return outbound
    outbound["referral_type"] = "outbound"
    if "Referral Source" not in outbound.columns:
        outbound["Referral Source"] = "Outbound Referral"
    else:
        outbound["Referral Source"] = outbound["Referral Source"].fillna("Outbound Referral")
    return outbound


def _validate_output(df: pd.DataFrame, label: str) -> List[str]:
    warnings: List[str] = []
    expected_columns = {"Full Name", "Work Address", "Work Phone", "Latitude", "Longitude", "Project ID"}
    missing = expected_columns.difference(df.columns)
    if missing:
        warn_msg = f"{label}: missing expected columns: {', '.join(sorted(missing))}"
        logger.warning(warn_msg)
        warnings.append(warn_msg)
    return warnings


def _collect_dataset_issues(df: pd.DataFrame, checks: Sequence[tuple[str, str]]) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    issue_frames: List[pd.DataFrame] = []
    base = df.reset_index(drop=False)
    base["__original_index__"] = df.index

    for column, reason in checks:
        if column not in df.columns:
            continue

        series = df[column]
        missing_mask = series.isna()
        if series.dtype == object:
            missing_mask = missing_mask | series.astype(str).str.strip().isin(["", "nan", "None", "NaN"])

        mask_values = missing_mask.to_numpy()
        if not mask_values.any():
            continue

        failing = base.loc[mask_values].copy()
        failing["__issue__"] = reason
        issue_frames.append(failing)

    if not issue_frames:
        return pd.DataFrame()

    issues = pd.concat(issue_frames, ignore_index=True)
    return issues


@overload
def process_and_save_cleaned_referrals(
    raw_input: Union[Path, str],
    processed_dir: Path | str,
    *,
    filename: Optional[str] = None,
) -> PreparationSummary: ...

@overload
def process_and_save_cleaned_referrals(
    raw_input: Any,  # For all other types (bytes, BytesIO, DataFrame, buffers)
    processed_dir: Path | str,
    *,
    filename: Optional[str] = None,
) -> PreparationSummary: ...

def process_and_save_cleaned_referrals(
    raw_input: Union[Path, str, BytesIO, bytes, BinaryIO, pd.DataFrame, Any],  # Any for Streamlit buffers
    processed_dir: Path | str,
    *,
    filename: Optional[str] = None,
) -> PreparationSummary:
    """Generate cleaned parquet datasets from raw referral data.
    
    Args:
        raw_input: Can be:
            - Path/str: Path to Excel file (existing behavior)
            - BytesIO/bytes: Raw Excel file data in memory
            - pd.DataFrame: Already loaded DataFrame
        processed_dir: Directory to save processed Parquet files
        filename: Optional filename for logging (used with BytesIO/bytes/DataFrame inputs)
    
    Returns:
        PreparationSummary with processing results and file locations
    """

    processed_path = Path(processed_dir)
    processed_path.mkdir(parents=True, exist_ok=True)

    # Handle different input types
    if isinstance(raw_input, pd.DataFrame):
        logger.info("Processing DataFrame with %d rows (source: %s)", len(raw_input), filename or "unknown")
        df_all = raw_input.copy()
    elif not isinstance(raw_input, (Path, str, pd.DataFrame)):
        # Handle any buffer-like object (BytesIO, bytes, Streamlit buffer, etc.)
        logger.info("Loading raw referrals from memory (source: %s)", filename or "uploaded file")
        
        # Convert buffer types to BytesIO for pandas compatibility
        excel_buffer: BytesIO
        
        if isinstance(raw_input, BytesIO):
            excel_buffer = raw_input
        elif isinstance(raw_input, bytes):
            excel_buffer = BytesIO(raw_input)
        elif type(raw_input).__name__ == 'memoryview':
            # Handle memoryview objects (from Streamlit getbuffer())
            excel_buffer = BytesIO(bytes(raw_input))  # type: ignore
        elif isinstance(raw_input, bytearray):
            excel_buffer = BytesIO(raw_input)
        else:
            # Last resort: assume it's some kind of buffer
            try:
                excel_buffer = BytesIO(bytes(raw_input))  # type: ignore
            except Exception as e:
                raise TypeError(f"Cannot convert {type(raw_input)} to BytesIO for Excel processing: {e}")
        
        try:
            df_all = pd.read_excel(excel_buffer, sheet_name="Referrals_App_Full_Contacts")
        except ValueError:
            # Reset position and try again
            excel_buffer.seek(0)
            df_all = pd.read_excel(excel_buffer)
    else:
        # Handle Path/str (existing behavior)
        if isinstance(raw_input, (Path, str)):
            raw_path = Path(raw_input)
            if not raw_path.exists():
                raise FileNotFoundError(f"Raw referral file not found: {raw_path}")
            logger.info("Loading raw referrals from %s", raw_path)
            try:
                df_all = pd.read_excel(raw_path, sheet_name="Referrals_App_Full_Contacts")
            except ValueError:
                df_all = pd.read_excel(raw_path)
        else:
            raise TypeError(f"Unsupported input type: {type(raw_input)}")
    
    df_all = _normalize_input_dataframe(df_all)

    skipped_configs: List[str] = []
    results: Dict[str, pd.DataFrame] = {}

    column_warnings: List[str] = []

    for key, config in _REFERRAL_CONFIGS.items():
        try:
            columns_map = cast(Mapping[str, str], config["columns"])
            filter_seq = cast(Optional[Sequence[Callable[[pd.DataFrame], pd.Series]]], config.get("filters"))
            processed, missing_columns = _process_referral_data(df_all, columns_map, filter_seq)
            if missing_columns:
                message = f"{key} missing columns: {', '.join(missing_columns)}"
                logger.warning(message)
                column_warnings.append(message)
        except KeyError as exc:
            logger.error("Skipping %s due to missing data: %s", key, exc)
            skipped_configs.append(key)
            processed = pd.DataFrame()
        results[key] = processed

    inbound_combined = _combine_inbound(results.get("primary_inbound", pd.DataFrame()), results.get("secondary_inbound", pd.DataFrame()))
    outbound = _prepare_outbound(results.get("outbound", pd.DataFrame()))

    combined = pd.concat([inbound_combined, outbound], ignore_index=False).sort_index()
    if "Project ID" in combined.columns:
        combined["Project ID"] = combined["Project ID"].astype("Int64")

    saved_files: Dict[str, Path] = {}

    inbound_path = processed_path / "cleaned_inbound_referrals.parquet"
    outbound_path = processed_path / "cleaned_outbound_referrals.parquet"
    all_path = processed_path / "cleaned_all_referrals.parquet"

    for path in (inbound_path, outbound_path, all_path):
        if path.exists():
            path.unlink()

    inbound_combined.to_parquet(inbound_path, compression="snappy")
    outbound.to_parquet(outbound_path, compression="snappy")
    combined.to_parquet(all_path, compression="snappy")

    saved_files.update({"inbound": inbound_path, "outbound": outbound_path, "all": all_path})

    warnings = []
    warnings.extend(column_warnings)
    warnings.extend(_validate_output(inbound_combined, "Inbound referrals"))
    warnings.extend(_validate_output(outbound, "Outbound referrals"))
    warnings.extend(_validate_output(combined, "Combined referrals"))

    checks = [
        ("Full Name", "Missing provider name"),
        ("Work Address", "Missing work address"),
        ("Latitude", "Missing latitude"),
        ("Longitude", "Missing longitude"),
    ]

    issue_records = {
        key: issues
        for key, issues in (
            ("inbound", _collect_dataset_issues(inbound_combined, checks)),
            ("outbound", _collect_dataset_issues(outbound, checks)),
            ("all", _collect_dataset_issues(combined, checks)),
        )
        if not issues.empty
    }

    summary = PreparationSummary(
        inbound_count=len(inbound_combined),
        outbound_count=len(outbound),
        all_count=len(combined),
        saved_files=saved_files,
        skipped_configs=skipped_configs,
        warnings=warnings,
        issue_records=issue_records,
    )

    logger.info(
        "Saved cleaned datasets: inbound=%d, outbound=%d, all=%d",
        summary.inbound_count,
        summary.outbound_count,
        summary.all_count,
    )
    return summary


def process_referral_data(
    raw_input: Union[Path, str, BytesIO, bytes, BinaryIO, pd.DataFrame, Any],
    *,
    filename: Optional[str] = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, PreparationSummary]:
    """Process referral data and return DataFrames without saving to disk.
    
    This function is useful for data validation, preview, or analysis
    without creating files on disk.
    
    Args:
        raw_input: Same input types as process_and_save_cleaned_referrals
        filename: Optional filename for logging (used with BytesIO/bytes/DataFrame inputs)
        
    Returns:
        Tuple of (inbound_df, outbound_df, combined_df, summary) containing processed data
    """
    import tempfile
    
    # Use a temporary directory that we won't actually write to
    with tempfile.TemporaryDirectory() as temp_dir:
        # Process the data but capture DataFrames before they're saved
        if isinstance(raw_input, pd.DataFrame):
            logger.info("Processing DataFrame with %d rows (source: %s)", len(raw_input), filename or "unknown")
            df_all = raw_input.copy()
        elif not isinstance(raw_input, (Path, str, pd.DataFrame)):
            # Handle any buffer-like object (BytesIO, bytes, Streamlit buffer, etc.)
            logger.info("Loading raw referrals from memory (source: %s)", filename or "uploaded file")
            
            # Convert buffer types to BytesIO for pandas compatibility
            excel_buffer: BytesIO
            
            if isinstance(raw_input, BytesIO):
                excel_buffer = raw_input
            elif isinstance(raw_input, bytes):
                excel_buffer = BytesIO(raw_input)
            elif type(raw_input).__name__ == 'memoryview':
                # Handle memoryview objects (from Streamlit getbuffer())
                excel_buffer = BytesIO(bytes(raw_input))  # type: ignore
            elif isinstance(raw_input, bytearray):
                excel_buffer = BytesIO(raw_input)
            else:
                # Last resort: assume it's some kind of buffer
                try:
                    excel_buffer = BytesIO(bytes(raw_input))  # type: ignore
                except Exception as e:
                    raise TypeError(f"Cannot convert {type(raw_input)} to BytesIO for Excel processing: {e}")
            
            try:
                df_all = pd.read_excel(excel_buffer, sheet_name="Referrals_App_Full_Contacts")
            except ValueError:
                # Reset position and try again
                excel_buffer.seek(0)
                df_all = pd.read_excel(excel_buffer)
        else:
            # Handle Path/str
            if isinstance(raw_input, (Path, str)):
                raw_path = Path(raw_input)
                if not raw_path.exists():
                    raise FileNotFoundError(f"Raw referral file not found: {raw_path}")
                logger.info("Loading raw referrals from %s", raw_path)
                try:
                    df_all = pd.read_excel(raw_path, sheet_name="Referrals_App_Full_Contacts")
                except ValueError:
                    df_all = pd.read_excel(raw_path)
            else:
                raise TypeError(f"Unsupported input type: {type(raw_input)}")
        
        df_all = _normalize_input_dataframe(df_all)
        
        # Process the data using the same logic as the main function
        skipped_configs: List[str] = []
        results: Dict[str, pd.DataFrame] = {}
        column_warnings: List[str] = []

        for key, config in _REFERRAL_CONFIGS.items():
            try:
                columns_map = cast(Mapping[str, str], config["columns"])
                filter_seq = cast(Optional[Sequence[Callable[[pd.DataFrame], pd.Series]]], config.get("filters"))
                processed, missing_columns = _process_referral_data(df_all, columns_map, filter_seq)
                if missing_columns:
                    message = f"{key} missing columns: {', '.join(missing_columns)}"
                    logger.warning(message)
                    column_warnings.append(message)
            except KeyError as exc:
                logger.error("Skipping %s due to missing data: %s", key, exc)
                skipped_configs.append(key)
                processed = pd.DataFrame()
            results[key] = processed

        inbound_combined = _combine_inbound(
            results.get("primary_inbound", pd.DataFrame()), 
            results.get("secondary_inbound", pd.DataFrame())
        )
        outbound = _prepare_outbound(results.get("outbound", pd.DataFrame()))
        combined = pd.concat([inbound_combined, outbound], ignore_index=False).sort_index()
        
        if "Project ID" in combined.columns:
            combined["Project ID"] = combined["Project ID"].astype("Int64")

        # Create summary without saved_files
        warnings = []
        warnings.extend(column_warnings)
        warnings.extend(_validate_output(inbound_combined, "Inbound referrals"))
        warnings.extend(_validate_output(outbound, "Outbound referrals"))
        warnings.extend(_validate_output(combined, "Combined referrals"))

        checks = [
            ("Full Name", "Missing provider name"),
            ("Work Address", "Missing work address"),
            ("Latitude", "Missing latitude"),
            ("Longitude", "Missing longitude"),
        ]

        issue_records = {
            key: issues
            for key, issues in (
                ("inbound", _collect_dataset_issues(inbound_combined, checks)),
                ("outbound", _collect_dataset_issues(outbound, checks)),
                ("all", _collect_dataset_issues(combined, checks)),
            )
            if not issues.empty
        }

        summary = PreparationSummary(
            inbound_count=len(inbound_combined),
            outbound_count=len(outbound),
            all_count=len(combined),
            saved_files={},  # No files saved
            skipped_configs=skipped_configs,
            warnings=warnings,
            issue_records=issue_records,
        )
        
        logger.info(
            "Processed datasets (not saved): inbound=%d, outbound=%d, all=%d",
            summary.inbound_count,
            summary.outbound_count,
            summary.all_count,
        )
        
        return inbound_combined, outbound, combined, summary


def _load_excel(raw_input: Any, filename: Optional[str] = None) -> pd.DataFrame:
    """Load Excel data from various input types."""
    if isinstance(raw_input, pd.DataFrame):
        logger.info("Processing DataFrame with %d rows (source: %s)", len(raw_input), filename or "unknown")
        return raw_input.copy()
    elif isinstance(raw_input, (Path, str)):
        raw_path = Path(raw_input)
        if not raw_path.exists():
            raise FileNotFoundError(f"File not found: {raw_path}")
        logger.info("Loading Excel file from %s", raw_path)
        return pd.read_excel(raw_path)
    else:
        # Handle buffer-like objects
        logger.info("Loading Excel data from memory (source: %s)", filename or "uploaded file")
        if isinstance(raw_input, BytesIO):
            excel_buffer = raw_input
        elif isinstance(raw_input, bytes):
            excel_buffer = BytesIO(raw_input)
        elif isinstance(raw_input, (memoryview, bytearray)):
            excel_buffer = BytesIO(bytes(raw_input))
        else:
            raise TypeError(f"Unsupported input type: {type(raw_input)}")
        return pd.read_excel(excel_buffer)


def process_and_save_preferred_providers(
    raw_input: Union[Path, str, BytesIO, bytes, BinaryIO, pd.DataFrame, Any],
    processed_dir: Path | str,
    *,
    filename: Optional[str] = None,
) -> PreferredProvidersSummary:
    """Process preferred providers data and save cleaned Parquet file.
    
    Args:
        raw_input: Can be:
            - Path/str: Path to Excel file
            - BytesIO/bytes: Raw Excel file data in memory
            - pd.DataFrame: Already loaded DataFrame
        processed_dir: Directory to save processed Parquet file
        filename: Optional filename for logging (used with BytesIO/bytes/DataFrame inputs)
    
    Returns:
        PreferredProvidersSummary with processing results and file location
    """
    
    processed_path = Path(processed_dir).resolve()
    processed_path.mkdir(parents=True, exist_ok=True)

    # Use the helper function to load the data
    df = _load_excel(raw_input, filename)

    # Process the data following the notebook logic
    total_count = len(df)
    
    # Remove duplicates
    df = df.drop_duplicates(ignore_index=True)
    
    # Identify records missing latitude/longitude
    lat_col = "Contact's Details: Latitude"
    lon_col = "Contact's Details: Longitude"
    
    warnings = []
    missing_records = None
    
    if {lat_col, lon_col}.issubset(df.columns):
        missing_records = df[df[[lat_col, lon_col]].isna().any(axis=1)]
        df_cleaned = df.dropna(subset=[lat_col, lon_col])
    else:
        warnings.append(f"Missing expected geo columns: {lat_col}, {lon_col}")
        missing_records = pd.DataFrame()
        df_cleaned = df.copy()

    missing_geo_count = len(missing_records) if missing_records is not None else 0
    cleaned_count = len(df_cleaned)
    
    # Save cleaned data to parquet
    output_path = processed_path / "cleaned_preferred_providers.parquet"
    if output_path.exists():
        output_path.unlink()
    
    df_cleaned.to_parquet(output_path, index=False, compression="snappy")
    
    logger.info(
        "Saved cleaned preferred providers: %d records (dropped %d missing geo data)",
        cleaned_count,
        missing_geo_count,
    )
    
    return PreferredProvidersSummary(
        total_count=total_count,
        cleaned_count=cleaned_count,
        missing_geo_count=missing_geo_count,
        saved_file=output_path,
        missing_records=missing_records,
        warnings=warnings,
    )


__all__ = ["PreparationSummary", "PreferredProvidersSummary", "process_and_save_cleaned_referrals", "process_referral_data", "process_and_save_preferred_providers"]
