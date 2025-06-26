import os
import requests
import logging
from PIL import Image
from typing import Optional, Dict
import tempfile
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class LogoProcessor:
    def __init__(self):
        self.supported_formats = ['png', 'jpg', 'jpeg', 'svg']
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.temp_dir = tempfile.gettempdir()
    
    def download_logo_from_url(self, url: str) -> Dict:
        """Download logo from URL and validate"""
        if not url or not self._is_valid_url(url):
            return {"success": False, "error": "Invalid URL provided"}
        
        try:
            # Download with timeout and size limit, including proper User-Agent
            headers = {
                'User-Agent': 'MiM Youth Sports Bot/1.0 (https://github.com/nathan-eagle/mim-youth-sports-slack-bot)'
            }
            response = requests.get(url, headers=headers, timeout=10, stream=True)
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('content-type', '').lower()
            if not any(fmt in content_type for fmt in ['image/png', 'image/jpeg', 'image/jpg', 'image/svg']):
                return {"success": False, "error": "URL does not point to a supported image format"}
            
            # Check file size
            content_length = response.headers.get('content-length')
            if content_length and int(content_length) > self.max_file_size:
                return {"success": False, "error": "Image file is too large (max 10MB)"}
            
            # Save to temporary file
            temp_filename = self._generate_temp_filename(url)
            temp_path = os.path.join(self.temp_dir, temp_filename)
            
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Validate downloaded image
            validation_result = self._validate_image_file(temp_path)
            if not validation_result["success"]:
                self._cleanup_temp_file(temp_path)
                return validation_result
            
            logger.info(f"Successfully downloaded logo from URL: {url}")
            return {
                "success": True,
                "file_path": temp_path,
                "original_url": url,
                "format": validation_result["format"],
                "size": validation_result["size"]
            }
            
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Download timeout - please check the URL"}
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"Failed to download image: {str(e)}"}
        except Exception as e:
            logger.error(f"Unexpected error downloading logo: {e}")
            return {"success": False, "error": "Failed to process logo from URL"}
    
    def process_slack_file(self, file_info: Dict, slack_client) -> Dict:
        """Process logo file uploaded to Slack"""
        try:
            file_url = file_info.get('url_private')
            file_name = file_info.get('name', 'logo')
            file_size = file_info.get('size', 0)
            
            if file_size > self.max_file_size:
                return {"success": False, "error": "File is too large (max 10MB)"}
            
            # Download file using Slack client
            response = slack_client.files_info(file=file_info['id'])
            if not response['ok']:
                return {"success": False, "error": "Failed to access uploaded file"}
            
            # Download file content
            file_response = requests.get(
                file_url,
                headers={'Authorization': f'Bearer {slack_client.token}'},
                timeout=10
            )
            file_response.raise_for_status()
            
            # Save to temporary file
            temp_filename = self._generate_temp_filename(file_name)
            temp_path = os.path.join(self.temp_dir, temp_filename)
            
            with open(temp_path, 'wb') as f:
                f.write(file_response.content)
            
            # Validate image
            validation_result = self._validate_image_file(temp_path)
            if not validation_result["success"]:
                self._cleanup_temp_file(temp_path)
                return validation_result
            
            logger.info(f"Successfully processed Slack file: {file_name}")
            return {
                "success": True,
                "file_path": temp_path,
                "original_name": file_name,
                "format": validation_result["format"],
                "size": validation_result["size"]
            }
            
        except Exception as e:
            logger.error(f"Error processing Slack file: {e}")
            return {"success": False, "error": "Failed to process uploaded file"}
    
    def _validate_image_file(self, file_path: str) -> Dict:
        """Validate image file format and properties"""
        try:
            with Image.open(file_path) as img:
                format_lower = img.format.lower() if img.format else 'unknown'
                
                if format_lower not in ['png', 'jpeg', 'jpg']:
                    return {"success": False, "error": f"Unsupported image format: {format_lower}"}
                
                # Check image dimensions (reasonable limits)
                width, height = img.size
                if width < 50 or height < 50:
                    return {"success": False, "error": "Image is too small (minimum 50x50 pixels)"}
                
                if width > 5000 or height > 5000:
                    return {"success": False, "error": "Image is too large (maximum 5000x5000 pixels)"}
                
                return {
                    "success": True,
                    "format": format_lower,
                    "size": (width, height)
                }
                
        except Exception as e:
            logger.error(f"Error validating image: {e}")
            return {"success": False, "error": "Invalid or corrupted image file"}
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid"""
        try:
            result = urlparse(url)
            return bool(result.scheme and result.netloc)
        except:
            return False
    
    def _generate_temp_filename(self, original: str) -> str:
        """Generate temporary filename"""
        import uuid
        import time
        
        # Extract extension if available
        if '.' in original:
            ext = original.split('.')[-1].lower()
            if ext in self.supported_formats:
                return f"logo_{int(time.time())}_{uuid.uuid4().hex[:8]}.{ext}"
        
        return f"logo_{int(time.time())}_{uuid.uuid4().hex[:8]}.png"
    
    def _cleanup_temp_file(self, file_path: str):
        """Clean up temporary file"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Cleaned up temp file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temp file {file_path}: {e}")
    
    def cleanup_logo(self, file_path: str):
        """Public method to cleanup logo file"""
        self._cleanup_temp_file(file_path)

# Global instance
logo_processor = LogoProcessor() 