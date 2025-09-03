"""
Base64 Logo Converter for Cloud Deployment
Converts the JLG logo to base64 encoding for cloud-ready Streamlit app
"""

import base64
import os

def image_to_base64(image_path: str) -> str | None:
    """Convert image file to base64 string."""
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
            return encoded_string
    except FileNotFoundError:
        print(f"Error: Image file '{image_path}' not found.")
        return None
    except Exception as e:
        print(f"Error encoding image: {e}")
        return None

def create_base64_config(image_path: str, output_file: str = "logo_config.py"):
    """Create a Python file with base64 encoded logo."""
    base64_string = image_to_base64(image_path)
    
    if base64_string:
        # Determine image format from file extension
        file_ext = os.path.splitext(image_path)[1].lower()
        mime_type = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg', 
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.svg': 'image/svg+xml'
        }.get(file_ext, 'image/jpeg')
        
        config_content = f'''"""
Base64 encoded logo for cloud deployment
Generated automatically - do not edit manually
Original file: {image_path}
"""

# Base64 encoded logo data
LOGO_BASE64 = "{base64_string}"

# Data URI for direct use in HTML/CSS
LOGO_DATA_URI = "data:{mime_type};base64,{base64_string}"

# Image format information
LOGO_MIME_TYPE = "{mime_type}"
LOGO_FORMAT = "{file_ext[1:].upper()}"
ORIGINAL_FILE = "{image_path}"
'''
        
        with open(output_file, 'w') as f:
            f.write(config_content)
        
        print(f"✅ Base64 logo configuration saved to '{output_file}'")
        print(f"📊 Original file size: {os.path.getsize(image_path)} bytes")
        print(f"📊 Base64 string length: {len(base64_string)} characters")
        print(f"📊 Size increase: {len(base64_string) / os.path.getsize(image_path) * 100:.1f}%")
        
        return True
    return False

def main():
    """Main function to convert logo to base64."""
    logo_path = "JaklitschLaw_NewLogo_withDogsRed.jpg"
    
    print("🏥 JLG Provider Recommender - Logo Base64 Converter")
    print("=" * 55)
    print(f"Converting: {logo_path}")
    print()
    
    if os.path.exists(logo_path):
        success = create_base64_config(logo_path)
        if success:
            print()
            print("🚀 Conversion complete! Your app is now cloud-ready.")
            print("   The logo will load from embedded base64 data.")
        else:
            print("❌ Conversion failed.")
            return 1
    else:
        print(f"❌ Logo file '{logo_path}' not found.")
        print("   Available image files:")
        for file in os.listdir('.'):
            if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.svg')):
                print(f"   - {file}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
