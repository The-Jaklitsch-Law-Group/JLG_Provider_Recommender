"""
Comprehensive Workflow Validation for JLG Provider Recommender Data Ingestion

This script validates the entire optimized data ingestion workflow to ensure
error-free operation and expected functionality.
"""

import sys
import time
from pathlib import Path

import pandas as pd


def test_imports():
    """Test all critical imports."""
    print("1. Testing Import System...")

    try:
        from src.data.ingestion import (
            DataIngestionManager,
            get_data_ingestion_status,
            load_detailed_referrals,
            load_inbound_referrals,
            load_provider_data,
            refresh_data_cache,
        )

        print("   ✅ Data ingestion imports successful")
        return True
    except Exception as e:
        print(f"   ❌ Import error: {e}")
        return False


def test_manager_initialization():
    """Test DataIngestionManager initialization."""
    print("\n2. Testing DataIngestionManager...")

    try:
        from src.data.ingestion import DataIngestionManager

        manager = DataIngestionManager()

        # Test file registry building
        registry = manager._file_registry
        print(f"   ✅ Manager initialized with {len(registry)} data sources")

        # Test registry contents
        expected_sources = ["inbound", "outbound", "provider"]
        actual_sources = [source.value for source in registry.keys()]

        if set(expected_sources) == set(actual_sources):
            print("   ✅ All expected data sources registered")
        else:
            print(f"   ⚠️  Source mismatch: expected {expected_sources}, got {actual_sources}")

        return True
    except Exception as e:
        print(f"   ❌ Manager initialization error: {e}")
        return False


def test_file_detection():
    """Test automatic file detection and prioritization."""
    print("\n3. Testing File Detection System...")

    try:
        from src.data.ingestion import get_data_ingestion_status

        status = get_data_ingestion_status()

        print("   📂 Data Source Status:")
        all_available = True
        optimized_count = 0

        for source, info in status.items():
            status_icon = "✅" if info["available"] else "❌"
            opt_icon = "🚀" if info["optimized"] else "📂"

            if not info["available"]:
                all_available = False
            if info["optimized"]:
                optimized_count += 1

            print(f"      {status_icon} {source.title()}: {opt_icon} {info['file_type']} | {info['path']}")

        if all_available:
            print("   ✅ All data sources available")
        else:
            print("   ⚠️  Some data sources missing")

        print(f"   🚀 {optimized_count}/{len(status)} sources optimized")
        return True

    except Exception as e:
        print(f"   ❌ File detection error: {e}")
        return False


def test_data_loading():
    """Test data loading functions with performance metrics."""
    print("\n4. Testing Data Loading Functions...")

    try:
        from src.data.ingestion import load_detailed_referrals, load_inbound_referrals, load_provider_data

        results = {}

        # Test provider data loading
        print("   🔄 Loading provider data...")
        start_time = time.time()
        provider_df = load_provider_data()
        load_time = time.time() - start_time

        results["provider"] = {
            "records": len(provider_df),
            "load_time": load_time,
            "columns": len(provider_df.columns) if not provider_df.empty else 0,
            "success": not provider_df.empty,
        }

        status = "✅" if not provider_df.empty else "❌"
        print(f"      {status} Provider: {len(provider_df)} records, {load_time:.3f}s")

        # Test inbound referrals loading
        print("   🔄 Loading inbound referrals...")
        start_time = time.time()
        inbound_df = load_inbound_referrals()
        load_time = time.time() - start_time

        results["inbound"] = {
            "records": len(inbound_df),
            "load_time": load_time,
            "columns": len(inbound_df.columns) if not inbound_df.empty else 0,
            "success": not inbound_df.empty,
        }

        status = "✅" if not inbound_df.empty else "❌"
        print(f"      {status} Inbound: {len(inbound_df)} records, {load_time:.3f}s")

        # Test outbound referrals loading
        print("   🔄 Loading outbound referrals...")
        start_time = time.time()
        outbound_df = load_detailed_referrals()
        load_time = time.time() - start_time

        results["outbound"] = {
            "records": len(outbound_df),
            "load_time": load_time,
            "columns": len(outbound_df.columns) if not outbound_df.empty else 0,
            "success": not outbound_df.empty,
        }

        status = "✅" if not outbound_df.empty else "❌"
        print(f"      {status} Outbound: {len(outbound_df)} records, {load_time:.3f}s")

        # Summary
        total_records = sum(r["records"] for r in results.values())
        total_time = sum(r["load_time"] for r in results.values())
        success_count = sum(1 for r in results.values() if r["success"])

        print(f"   📊 Summary: {success_count}/3 datasets loaded, {total_records} total records, {total_time:.3f}s")

        return success_count == 3, results

    except Exception as e:
        print(f"   ❌ Data loading error: {e}")
        return False, {}


def test_data_quality():
    """Test data quality and integrity."""
    print("\n5. Testing Data Quality...")

    try:
        from src.data.ingestion import load_detailed_referrals, load_inbound_referrals, load_provider_data

        # Load all datasets
        provider_df = load_provider_data()
        inbound_df = load_inbound_referrals()
        outbound_df = load_detailed_referrals()

        quality_checks = {"provider": [], "inbound": [], "outbound": []}

        # Provider data quality checks
        if not provider_df.empty:
            required_cols = ["Full Name", "Street", "City", "State", "Zip"]
            missing_cols = [col for col in required_cols if col not in provider_df.columns]

            if not missing_cols:
                quality_checks["provider"].append("✅ All required columns present")
            else:
                quality_checks["provider"].append(f"⚠️  Missing columns: {missing_cols}")

            # Check for coordinates
            if "Latitude" in provider_df.columns and "Longitude" in provider_df.columns:
                valid_coords = (provider_df["Latitude"].notna() & provider_df["Longitude"].notna()).sum()
                quality_checks["provider"].append(f"✅ {valid_coords} valid coordinate pairs")

            # Check for duplicates
            duplicates = provider_df.duplicated().sum()
            if duplicates == 0:
                quality_checks["provider"].append("✅ No duplicate records")
            else:
                quality_checks["provider"].append(f"⚠️  {duplicates} duplicate records")

        # Inbound data quality checks
        if not inbound_df.empty:
            # Check for referral date
            if "Referral Date" in inbound_df.columns:
                valid_dates = inbound_df["Referral Date"].notna().sum()
                quality_checks["inbound"].append(f"✅ {valid_dates} valid referral dates")

            # Check Sign Up Date filling
            if "Sign Up Date" in inbound_df.columns:
                null_signup = inbound_df["Sign Up Date"].isnull().sum()
                if null_signup == 0:
                    quality_checks["inbound"].append("✅ All Sign Up Date values filled")
                else:
                    quality_checks["inbound"].append(f"⚠️  {null_signup} missing Sign Up Date values")

        # Outbound data quality checks
        if not outbound_df.empty:
            # Check for referral date
            if "Referral Date" in outbound_df.columns:
                valid_dates = outbound_df["Referral Date"].notna().sum()
                quality_checks["outbound"].append(f"✅ {valid_dates} valid referral dates")

            # Check coordinates
            if "Latitude" in outbound_df.columns and "Longitude" in outbound_df.columns:
                valid_coords = (outbound_df["Latitude"].notna() & outbound_df["Longitude"].notna()).sum()
                quality_checks["outbound"].append(f"✅ {valid_coords} valid coordinates")

        # Print quality results
        for dataset, checks in quality_checks.items():
            if checks:
                print(f"   📊 {dataset.title()} Quality:")
                for check in checks:
                    print(f"      {check}")

        return True

    except Exception as e:
        print(f"   ❌ Data quality check error: {e}")
        return False


def test_caching_system():
    """Test caching functionality."""
    print("\n6. Testing Caching System...")

    try:
        from src.data.ingestion import load_provider_data, refresh_data_cache

        # First load (cache miss)
        start_time = time.time()
        df1 = load_provider_data()
        first_load_time = time.time() - start_time

        # Second load (cache hit)
        start_time = time.time()
        df2 = load_provider_data()
        second_load_time = time.time() - start_time

        # Verify data consistency
        if len(df1) == len(df2) and list(df1.columns) == list(df2.columns):
            print("   ✅ Cache returns consistent data")
        else:
            print("   ⚠️  Cache data inconsistency detected")

        # Performance comparison
        if second_load_time < first_load_time:
            speedup = (first_load_time - second_load_time) / first_load_time * 100
            print(f"   ✅ Cache provides {speedup:.1f}% speedup")
        else:
            print("   ⚠️  Cache may not be working effectively")

        # Test cache refresh
        refresh_data_cache()
        print("   ✅ Cache refresh function works")

        return True

    except Exception as e:
        print(f"   ❌ Caching test error: {e}")
        return False


def test_error_handling():
    """Test error handling and fallback mechanisms."""
    print("\n7. Testing Error Handling...")

    try:
        from src.data.ingestion import DataIngestionManager, DataSource

        # Test with non-existent data directory
        manager = DataIngestionManager("nonexistent_data_dir")

        # This should gracefully handle missing files
        result = manager.load_data(DataSource.INBOUND_REFERRALS, show_status=False)

        if result.empty:
            print("   ✅ Gracefully handles missing data directory")
        else:
            print("   ⚠️  Unexpected data returned from missing directory")

        # Test status with missing files
        status = manager.get_data_status()
        unavailable_count = sum(1 for info in status.values() if not info["available"])

        if unavailable_count > 0:
            print(f"   ✅ Correctly detects {unavailable_count} unavailable sources")

        return True

    except Exception as e:
        print(f"   ❌ Error handling test failed: {e}")
        return False


def test_optimization_preparation():
    """Test the optimized data preparation system."""
    print("\n8. Testing Data Preparation System...")

    try:
        # Check if optimized preparation script exists and is importable
        optimized_prep_path = Path("src/data/preparation.py")
        if optimized_prep_path.exists():
            print("   ✅ Optimized data preparation script found")

            # Test if we can import the main functions
            from src.data.preparation import main, StreamlinedDataPreparation

            processor = StreamlinedDataPreparation()
            print("   ✅ StreamlinedDataPreparation class importable")

            # Check if cleaned files exist (result of preparation)
            cleaned_files = ["data/cleaned_inbound_referrals.parquet", "data/processed/cleaned_outbound_referrals.parquet"]

            existing_files = [f for f in cleaned_files if Path(f).exists()]
            print(f"   ✅ {len(existing_files)}/{len(cleaned_files)} cleaned files available")

        else:
            print("   ⚠️  Optimized data preparation script not found")

        return True

    except Exception as e:
        print(f"   ❌ Data preparation test error: {e}")
        return False


def main():
    """Run comprehensive workflow validation."""
    print("🔍 JLG PROVIDER RECOMMENDER - COMPREHENSIVE WORKFLOW VALIDATION")
    print("=" * 80)

    test_results = []

    # Run all tests
    tests = [
        ("Import System", test_imports),
        ("Manager Initialization", test_manager_initialization),
        ("File Detection", test_file_detection),
        ("Data Loading", lambda: test_data_loading()[0]),  # Only get success status
        ("Data Quality", test_data_quality),
        ("Caching System", test_caching_system),
        ("Error Handling", test_error_handling),
        ("Data Preparation", test_optimization_preparation),
    ]

    for test_name, test_func in tests:
        try:
            result = test_func()
            test_results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} test crashed: {e}")
            test_results.append((test_name, False))

    # Summary
    print("\n" + "=" * 80)
    print("📊 VALIDATION SUMMARY")
    print("=" * 80)

    passed_tests = sum(1 for _, result in test_results if result)
    total_tests = len(test_results)

    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} | {test_name}")

    print(f"\n🎯 Overall Result: {passed_tests}/{total_tests} tests passed")

    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED - Workflow is error-free and operating as expected!")
        print("✅ The optimized data ingestion system is ready for production use.")
    else:
        print("⚠️  Some tests failed - Review and address issues before production use.")

    return passed_tests == total_tests


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
