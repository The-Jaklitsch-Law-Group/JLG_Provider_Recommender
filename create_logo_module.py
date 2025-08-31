"""
Base64 Logo Encoder for JLG Provider Recommender
Method 2: Create embedded logo file for cloud deployment

This script creates a Python module with the base64-encoded logo
that can be imported directly into the Streamlit app for cloud hosting.
"""

import base64
import os
from pathlib import Path

def create_logo_module():
    """Create a Python module with embedded base64 logo"""
    
    # Path to the logo file
    logo_path = Path("jlg_logo.svg")
    
    if not logo_path.exists():
        print(f"Error: Logo file {logo_path} not found!")
        return False
    
    try:
        # Read and encode the logo
        with open(logo_path, "rb") as logo_file:
            logo_data = logo_file.read()
            logo_base64 = base64.b64encode(logo_data).decode('utf-8')
        
        # Create the Python module content
        module_content = f'''"""
JLG Logo Module
Contains base64-encoded logo for cloud deployment compatibility
Generated automatically - do not edit manually
"""

# Base64-encoded JLG logo (SVG format)
JLG_LOGO_BASE64 = "{logo_base64}"

def get_logo_data_url():
    """Return data URL for use in Streamlit components"""
    return f"data:image/svg+xml;base64,{{JLG_LOGO_BASE64}}"

def get_logo_bytes():
    """Return decoded logo bytes"""
    import base64
    return base64.b64decode(JLG_LOGO_BASE64)

# Usage examples:
# import logo_data
# st.image(logo_data.get_logo_data_url())
# st.markdown(f'<img src="{{logo_data.get_logo_data_url()}}" width="200">', unsafe_allow_html=True)
'''
        
        # Write the module file
        with open("logo_data.py", "w", encoding="utf-8") as module_file:
            module_file.write(module_content)
        
        print("✅ Successfully created logo_data.py module")
        print("📁 File size:", len(module_content), "bytes")
        print("🎨 Logo encoded length:", len(logo_base64), "characters")
        print("\n📋 Usage in app.py:")
        print("   import logo_data")
        print('   st.image(logo_data.get_logo_data_url(), width=200)')
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating logo module: {e}")
        return False

if __name__ == "__main__":
    print("🎨 Creating embedded logo module for cloud deployment...")
    success = create_logo_module()
    
    if success:
        print("\n✨ Logo module created successfully!")
        print("🚀 Ready for Streamlit Cloud deployment")
    else:
        print("\n❌ Failed to create logo module")
