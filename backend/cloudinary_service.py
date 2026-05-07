"""
Cloudinary Service for PDF Storage - WITH DETAILED DEBUG LOGGING
"""

import cloudinary
import cloudinary.uploader
import cloudinary.utils
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Configure Cloudinary
cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
api_key = os.getenv("CLOUDINARY_API_KEY")
api_secret = os.getenv("CLOUDINARY_API_SECRET")

print(f"🔍 Cloudinary Config Debug:")
print(f"  Cloud Name: {cloud_name}")
print(f"  API Key: {api_key[:5]}...{api_key[-3:] if api_key else 'MISSING'}")
print(f"  API Secret: {'SET' if api_secret else 'MISSING'} (length: {len(api_secret) if api_secret else 0})")

cloudinary.config(
    cloud_name=cloud_name,
    api_key=api_key,
    api_secret=api_secret,
    secure=True
)

print(f"✓ Cloudinary configured with cloud: {cloud_name}")


def upload_pdf(file_path: str, public_id: str = None) -> dict:
    """
    Upload a PDF file to Cloudinary.
    """
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not public_id:
            public_id = Path(file_path).stem
        
        print(f"⏳ Uploading to Cloudinary: {file_path}")
        print(f"  Public ID: {public_id}")
        print(f"  File size: {os.path.getsize(file_path)} bytes")
        
        # Upload with detailed logging
        result = cloudinary.uploader.upload(
            file_path,
            folder="dprs",
            resource_type="raw",
            public_id=public_id,
            overwrite=False,
            use_filename=True,
            unique_filename=True,
            access_mode="public"  # Allow public access to files
        )
        
        print(f"✓ Cloudinary upload successful!")
        print(f"  URL: {result['secure_url']}")
        print(f"  Public ID: {result['public_id']}")
        print(f"  Bytes: {result['bytes']}")
        print(f"  Format: {result.get('format', 'N/A')}")
        
        return {
            'url': result['url'],
            'secure_url': result['secure_url'],
            'public_id': result['public_id'],
            'bytes': result['bytes'],
            'resource_type': result['resource_type']
        }
        
    except Exception as e:
        print(f"❌ Cloudinary upload FAILED!")
        print(f"  Error Type: {type(e).__name__}")
        print(f"  Error Message: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


def delete_pdf(public_id: str) -> bool:
    """Delete a PDF from Cloudinary."""
    try:
        if not public_id:
            return False
            
        print(f"⏳ Deleting from Cloudinary: {public_id}")
        
        result = cloudinary.uploader.destroy(
            public_id,
            resource_type="raw"
        )
        
        success = result.get('result') == 'ok'
        
        if success:
            print(f"✓ Cloudinary delete successful: {public_id}")
        else:
            print(f"⚠ Cloudinary delete returned: {result.get('result')}")
            
        return success
        
    except Exception as e:
        print(f"✗ Cloudinary delete error: {str(e)}")
        return False


def get_pdf_url(public_id: str) -> str:
    """Get the direct HTTPS URL for a PDF."""
    url, options = cloudinary.utils.cloudinary_url(
        public_id,
        resource_type="raw",
        secure=True
    )
    return url
