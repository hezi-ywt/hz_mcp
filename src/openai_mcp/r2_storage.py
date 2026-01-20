"""
Cloudflare R2 Storage Module

Handles image uploads to Cloudflare R2 storage and generates public URLs.
"""

import os
import uuid
import logging
from io import BytesIO
from typing import Optional
from PIL import Image
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

logger = logging.getLogger(__name__)


def is_r2_configured() -> bool:
    """
    Check if R2 credentials are properly configured.
    
    Returns:
        bool: True if all required R2 environment variables are set
    """
    required_vars = [
        "R2_ACCOUNT_ID",
        "R2_ACCESS_KEY_ID",
        "R2_SECRET_ACCESS_KEY",
        "R2_BUCKET_NAME"
    ]
    return all(os.getenv(var) for var in required_vars)


def get_r2_client():
    """
    Create and return a configured R2 client using boto3.
    
    Returns:
        boto3.client: Configured S3-compatible client for R2
        
    Raises:
        ValueError: If R2 credentials are not configured
    """
    if not is_r2_configured():
        raise ValueError("R2 credentials not configured. Please set R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, and R2_BUCKET_NAME in environment variables.")
    
    account_id = os.getenv("R2_ACCOUNT_ID")
    access_key_id = os.getenv("R2_ACCESS_KEY_ID")
    secret_access_key = os.getenv("R2_SECRET_ACCESS_KEY")
    
    # Cloudflare R2 endpoint format
    endpoint_url = f"https://{account_id}.r2.cloudflarestorage.com"
    
    client = boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        region_name="auto"  # R2 uses 'auto' as region
    )
    
    return client


def upload_image_to_r2(
    image: Image.Image,
    filename: Optional[str] = None,
    content_type: str = "image/png"
) -> str:
    """
    Upload a PIL Image to Cloudflare R2 and return the public URL.
    
    Args:
        image: PIL Image object to upload
        filename: Optional custom filename (without extension)
        content_type: MIME type of the image (default: image/png)
        
    Returns:
        str: Public URL of the uploaded image
        
    Raises:
        ValueError: If R2 is not configured
        ClientError: If upload fails
    """
    if not is_r2_configured():
        raise ValueError("R2 is not configured")
    
    try:
        # Generate unique filename if not provided
        if not filename:
            filename = f"image_{uuid.uuid4().hex[:12]}"
        
        # Add extension based on content type
        extension = content_type.split("/")[-1]
        if extension == "jpeg":
            extension = "jpg"
        full_filename = f"{filename}.{extension}"
        
        # Convert image to bytes
        buffer = BytesIO()
        image_format = "PNG" if extension == "png" else "JPEG"
        image.save(buffer, format=image_format, quality=95)
        buffer.seek(0)
        
        # Get R2 client and bucket name
        client = get_r2_client()
        bucket_name = os.getenv("R2_BUCKET_NAME")
        
        # Upload to R2
        client.put_object(
            Bucket=bucket_name,
            Key=full_filename,
            Body=buffer.getvalue(),
            ContentType=content_type,
            CacheControl="public, max-age=31536000"  # Cache for 1 year
        )
        
        # Generate public URL
        public_domain = os.getenv("R2_PUBLIC_DOMAIN")
        if public_domain:
            # Use custom domain if configured
            public_url = f"{public_domain.rstrip('/')}/{full_filename}"
        else:
            # Use default R2.dev domain
            account_id = os.getenv("R2_ACCOUNT_ID")
            public_url = f"https://{bucket_name}.{account_id}.r2.dev/{full_filename}"
        
        logger.info(f"Successfully uploaded image to R2: {public_url}")
        return public_url
        
    except NoCredentialsError:
        logger.error("R2 credentials are invalid")
        raise ValueError("Invalid R2 credentials")
    except ClientError as e:
        logger.error(f"Failed to upload to R2: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during R2 upload: {str(e)}")
        raise


def upload_bytes_to_r2(
    data: bytes,
    filename: str,
    content_type: str = "image/png"
) -> str:
    """
    Upload raw bytes to Cloudflare R2.
    
    Args:
        data: Raw bytes to upload
        filename: Filename for the object
        content_type: MIME type of the content
        
    Returns:
        str: Public URL of the uploaded object
    """
    if not is_r2_configured():
        raise ValueError("R2 is not configured")
    
    try:
        client = get_r2_client()
        bucket_name = os.getenv("R2_BUCKET_NAME")
        
        client.put_object(
            Bucket=bucket_name,
            Key=filename,
            Body=data,
            ContentType=content_type,
            CacheControl="public, max-age=31536000"
        )
        
        # Generate public URL
        public_domain = os.getenv("R2_PUBLIC_DOMAIN")
        if public_domain:
            public_url = f"{public_domain.rstrip('/')}/{filename}"
        else:
            account_id = os.getenv("R2_ACCOUNT_ID")
            public_url = f"https://{bucket_name}.{account_id}.r2.dev/{filename}"
        
        logger.info(f"Successfully uploaded bytes to R2: {public_url}")
        return public_url
        
    except Exception as e:
        logger.error(f"Failed to upload bytes to R2: {str(e)}")
        raise
