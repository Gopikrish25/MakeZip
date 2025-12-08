# function_app.py (create this file in the root directory)
import azure.functions as func
import logging
import json
import zipfile
import io
import base64
from typing import List, Dict, Any

# Initialize the Function App with the new v2 programming model
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

def is_base64_encoded(content: str) -> bool:
    """
    Automatically detect if content is base64 encoded.
    This is useful when the encoding field is not provided.
    """
    try:
        if not content or not isinstance(content, str):
            return False
        # Try to decode and re-encode to verify it's valid base64
        decoded = base64.b64decode(content, validate=True)
        re_encoded = base64.b64encode(decoded).decode('utf-8')
        # Remove any whitespace for comparison
        return re_encoded.strip() == content.strip()
    except Exception:
        return False

def process_file_content(filename: str, content: str, encoding: str = None) -> bytes:
    """
    Process file content based on encoding type.
    
    Args:
        filename: Name of the file
        content: File content (either plain text or base64)
        encoding: Encoding type ('base64' or None)
    
    Returns:
        bytes: Processed file data
    """
    # Determine file extension
    file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
    
    # List of extensions that are typically binary
    binary_extensions = {
        'docx', 'doc', 'xlsx', 'xls', 'xlsm', 'pptx', 'ppt',
        'pdf', 'zip', 'rar', '7z', 'tar', 'gz',
        'jpg', 'jpeg', 'png', 'gif', 'bmp', 'ico', 'webp',
        'mp3', 'mp4', 'avi', 'mov', 'wmv', 'flv',
        'exe', 'dll', 'so', 'bin'
    }
    
    # Auto-detect encoding if not specified
    if encoding is None:
        if file_ext in binary_extensions or is_base64_encoded(content):
            encoding = 'base64'
        else:
            encoding = 'text'
    
    # Process based on encoding
    if encoding == 'base64':
        try:
            return base64.b64decode(content)
        except Exception as e:
            logging.error(f"Error decoding base64 for {filename}: {str(e)}")
            raise ValueError(f"Invalid base64 content for {filename}")
    else:
        # Text content - encode as UTF-8
        return content.encode('utf-8')
    
@app.route(route="home", methods=["GET"])
def home(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse("Welcome to the MakeZip API!", status_code=200)

@app.route(route="makezip", methods=["POST"])
def makezip(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Function to create a zip file from multiple files passed in the request body.
    
    Request body format:
    [
        {
            "name": "file1.txt",
            "content": "text content"
        },
        {
            "name": "file2.docx",
            "content": "base64_encoded_content",
            "encoding": "base64"  # Optional - will auto-detect if not provided
        }
    ]
    
    Returns:
        A zip file containing all the provided files
    """
    logging.info('Processing zip file creation request')

    try:
        # Parse the request body
        try:
            req_body = req.get_json()
        except ValueError:
            return func.HttpResponse(
                json.dumps({"error": "Invalid JSON in request body"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Validate request body structure
        if not isinstance(req_body, list):
            return func.HttpResponse(
                json.dumps({"error": "Request body must be a JSON array of file objects"}),
                status_code=400,
                mimetype="application/json"
            )
        
        if len(req_body) == 0:
            return func.HttpResponse(
                json.dumps({"error": "Request body cannot be empty"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Create a BytesIO object to hold the zip file in memory
        zip_buffer = io.BytesIO()
        
        # Create a zip file with compression
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zip_file:
            processed_files = []
            
            for idx, file_obj in enumerate(req_body):
                # Validate file object structure
                if not isinstance(file_obj, dict):
                    return func.HttpResponse(
                        json.dumps({"error": f"File at index {idx} must be a JSON object"}),
                        status_code=400,
                        mimetype="application/json"
                    )
                
                if 'name' not in file_obj:
                    return func.HttpResponse(
                        json.dumps({"error": f"File at index {idx} is missing 'name' field"}),
                        status_code=400,
                        mimetype="application/json"
                    )
                
                if 'content' not in file_obj:
                    return func.HttpResponse(
                        json.dumps({"error": f"File at index {idx} is missing 'content' field"}),
                        status_code=400,
                        mimetype="application/json"
                    )
                
                filename = file_obj['name']
                content = file_obj['content']
                encoding = file_obj.get('encoding')  # Optional field
                
                # Validate filename
                if not filename or not isinstance(filename, str):
                    return func.HttpResponse(
                        json.dumps({"error": f"Invalid filename at index {idx}"}),
                        status_code=400,
                        mimetype="application/json"
                    )
                
                # Sanitize filename to prevent path traversal
                filename = filename.replace('..', '').replace('/', '').replace('\\', '')
                
                try:
                    # Process the file content
                    file_data = process_file_content(filename, content, encoding)
                    
                    # Write the file to the zip
                    zip_file.writestr(filename, file_data)
                    processed_files.append(filename)
                    
                    logging.info(f"Added file to zip: {filename} ({len(file_data)} bytes)")
                    
                except ValueError as e:
                    return func.HttpResponse(
                        json.dumps({"error": str(e)}),
                        status_code=400,
                        mimetype="application/json"
                    )
        
        # Get the zip file content
        zip_buffer.seek(0)
        zip_content = zip_buffer.read()
        
        logging.info(f"Successfully created zip file with {len(processed_files)} files ({len(zip_content)} bytes)")
        
        # Return the zip file as a response
        return func.HttpResponse(
            zip_content,
            status_code=200,
            mimetype='application/zip',
            headers={
                'Content-Disposition': 'attachment; filename="archive.zip"',
                'Content-Length': str(len(zip_content))
            }
        )
        
    except Exception as e:
        logging.error(f"Unexpected error processing request: {str(e)}", exc_info=True)
        return func.HttpResponse(
            json.dumps({"error": f"Internal server error: {str(e)}"}),
            status_code=500,
            mimetype="application/json"
        )