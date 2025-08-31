#!/usr/bin/env python3
"""Script to regenerate cleaned provider data with enhanced time-based features."""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.absolute()
sys.path.append(str(project_root))

def regenerate_data():
    """Regenerate cleaned data with new features."""
    
    print("🔄 Regenerating provider data with enhanced features...")
    
    # Check if source data exists
    source_file = project_root / "data" / "Referrals_App_Outbound.parquet"
    
    if not source_file.exists():
        print(f"❌ Source data file not found: {source_file}")
        print("Please ensure the raw data file exists before running data cleaning.")
        return False
    
    try:
        # Import and run the cleaning script
        from prepare_contacts.clean_outbound_referrals import main as clean_main
        
        print("📊 Running data cleaning and aggregation...")
        clean_main()
        
        print("✅ Data regeneration complete!")
        print("\nGenerated files:")
        print(f"- {project_root / 'data' / 'cleaned_outbound_referrals.parquet'}")
        print(f"- {project_root / 'data' / 'detailed_referrals.parquet'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during data regeneration: {e}")
        return False

def validate_generated_data():
    """Validate the generated data files."""
    
    print("\n🔍 Validating generated data...")
    
    try:
        import pandas as pd
        from provider_utils import validate_provider_data, load_detailed_referrals
        
        # Check cleaned provider data
        provider_file = project_root / "data" / "cleaned_outbound_referrals.parquet"
        if provider_file.exists():
            provider_df = pd.read_parquet(provider_file)
            is_valid, message = validate_provider_data(provider_df)
            
            if is_valid:
                print("✅ Provider data validation passed")
            else:
                print("⚠️ Provider data validation issues:")
                print(message)
        else:
            print("❌ Cleaned provider data file not found")
            return False
        
        # Check detailed referrals data
        detailed_file = project_root / "data" / "detailed_referrals.parquet"
        if detailed_file.exists():
            detailed_df = load_detailed_referrals(str(detailed_file))
            
            if not detailed_df.empty:
                print(f"✅ Detailed referrals data loaded: {len(detailed_df)} records")
                
                # Check date range
                if 'Referral Date' in detailed_df.columns:
                    date_range = detailed_df['Referral Date'].agg(['min', 'max'])
                    print(f"   Date range: {date_range['min'].date()} to {date_range['max'].date()}")
                else:
                    print("⚠️ No Referral Date column found in detailed data")
            else:
                print("⚠️ Detailed referrals data is empty")
        else:
            print("❌ Detailed referrals data file not found")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during validation: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Provider Recommender Data Regeneration")
    print("=" * 50)
    
    # Regenerate data
    success = regenerate_data()
    
    if success:
        # Validate the results
        validate_generated_data()
        
        print("\n🎉 Data regeneration and validation complete!")
        print("\nNext steps:")
        print("1. Test the application: streamlit run app.py")
        print("2. Check data quality: streamlit run data_dashboard.py")
        print("3. Run tests: python run_tests.py")
    else:
        print("\n💥 Data regeneration failed. Please check the errors above.")
        sys.exit(1)
