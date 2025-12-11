# MakeZip - Azure Function for Creating Zip Archives

[![Python Version](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11-blue)](https://www.python.org/downloads/)
[![Azure Functions](https://img.shields.io/badge/Azure%20Functions-v4-0062AD)](https://azure.microsoft.com/en-us/services/functions/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

A lightweight, serverless Azure Function that creates zip archives from multiple files sent via API. Perfect for integrating with Azure Logic Apps, Power Automate, or any application that needs on-demand zip file creation.

## Features

- **Multi-file Support** - Bundle multiple files into a single zip archive
- **Smart Type Detection** - Automatically handles both text and binary files
- **Base64 Support** - Seamlessly processes binary files (PDF, Word, Excel, images)
- **Compression** - Built-in ZIP_DEFLATED compression (level 6)
- **Security** - Filename sanitization and input validation
- **Error Handling** - Comprehensive error messages and logging
- **Logic Apps Ready** - Designed for Azure Logic Apps integration
- **Cost Effective** - Runs on Azure Functions Consumption Plan

## Quick Start

### Prerequisites

- Python 3.9, 3.10, or 3.11
- [Azure Functions Core Tools](https://docs.microsoft.com/en-us/azure/azure-functions/functions-run-local) v4.x
- [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli) (for deployment)

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/Gopikrish25/MakeZip.git
   cd MakeZip
   ```

2. **Install dependencies** (optional - automatically installed by Azure Functions)
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the function locally**
   ```bash
   func start
   ```

4. **Test the endpoint**
   ```bash
   curl -X POST http://localhost:7071/api/makezip \
     -H "Content-Type: application/json" \
     -d '[{"name":"test.txt","content":"Hello World!"}]' \
     --output test.zip
   ```

## API Documentation

### Endpoint

```
POST /api/makezip
```

### Request Format

Send a JSON array of file objects:

```json
[
  {
    "name": "filename.txt",
    "content": "file content as string"
  },
  {
    "name": "document.pdf",
    "content": "base64_encoded_content",
    "encoding": "base64"
  }
]
```

### Request Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Filename including extension |
| `content` | string | Yes | File content (plain text or base64) |
| `encoding` | string | No | Set to `"base64"` for binary files (auto-detected if omitted) |

### Response

- **Success (200)**: Returns a zip file as binary data
  - Content-Type: `application/zip`
  - Content-Disposition: `attachment; filename="archive.zip"`

- **Error (400)**: Invalid request
  ```json
  {
    "error": "Description of the error"
  }
  ```

- **Error (500)**: Internal server error
  ```json
  {
    "error": "Internal server error: details"
  }
  ```

## Usage Examples

### Example 1: Text Files Only

```bash
curl -X POST http://localhost:7071/api/makezip \
  -H "Content-Type: application/json" \
  -d '[
    {"name":"readme.txt","content":"This is a text file"},
    {"name":"config.json","content":"{\"setting\":\"value\"}"}
  ]' \
  --output files.zip
```

### Example 2: Mixed Text and Binary Files

```json
[
  {
    "name": "readme.txt",
    "content": "This is a plain text file"
  },
  {
    "name": "report.docx",
    "content": "UEsDBBQABgAIAAAAIQ...[base64 content]...",
    "encoding": "base64"
  },
  {
    "name": "invoice.pdf",
    "content": "JVBERi0xLjQKJeLjz9...[base64 content]...",
    "encoding": "base64"
  }
]
```

## 🔗 Azure Logic Apps Integration

### Step-by-Step Integration

1. **Get File Content** - Use appropriate connector (SharePoint, OneDrive, Blob Storage, SFTP)
   ```
   Action: Get file content
   ```

2. **Convert to Base64** - Use Expression
   ```
   base64(body('Get_file_content'))
   ```

3. **Compose JSON Array** - Build the request payload
   ```json
   [
     {
       "name": "@{triggerBody()?['Name']}",
       "content": "@{outputs('Convert_to_Base64')}",
       "encoding": "base64"
     }
   ]
   ```

4. **HTTP Action** - Call the Azure Function
   - Method: `POST`
   - URI: `https://<your-function-app>.azurewebsites.net/api/makezip`
   - Headers: `Content-Type: application/json`
   - Body: Output from Compose action

5. **Save Result** - Store or email the zip file


## Deployment to Azure

### Method 1: Azure CLI

```bash

# Login to Azure
az login


# Deploy the function
func azure functionapp publish myZipFunctionApp
```

### Method 2: VS Code Azure Functions Extension

1. Install the [Azure Functions extension](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-azurefunctions)
2. Click on Azure icon in sidebar
3. Click "Deploy to Function App..."
4. Follow the prompts
   

## Performance & Limits

| Metric | Value | Notes |
|--------|-------|-------|
| Max Request Size | 100 MB | Azure Functions limit |
| Max Execution Time | 5 minutes | Consumption plan (can be extended with Premium) |
| Max Memory | 1.5 GB | Consumption plan |
| Compression Level | 6 | Balance between speed and size |
| Supported Files | All types | Text and binary |

### Recommendations

- **Small files (<10 MB)**: Works perfectly with default settings
- **Medium files (10-50 MB)**: Monitor execution time
- **Large files (>50 MB)**: Consider Premium plan or Blob Storage integration

## Security Features

- **Filename Sanitization** - Prevents path traversal attacks
- **Input Validation** - Comprehensive checks on all inputs
- **Error Handling** - No sensitive data in error messages
- **Authentication** - Supports Azure Function Keys (set `authLevel` in function.json)


## Troubleshooting

### Issue: Files are Corrupted

**Symptoms**: Zip file extracts but files won't open

**Solution**: Ensure binary files are base64 encoded
```json
{
  "name": "document.pdf",
  "content": "base64_string_here",
  "encoding": "base64"  // ← Required for binary files
}
```

### Issue: "Invalid JSON" Error

**Symptoms**: 400 Bad Request error

**Solution**: 
- Validate JSON syntax (no trailing commas)
- Check quote escaping in content
- Use a JSON validator before sending

### Issue: Timeout Errors

**Symptoms**: Function times out with many/large files

**Solution**:
- Split into multiple smaller requests
- Increase `functionTimeout` in `host.json`
- Consider Azure Functions Premium plan

### Issue: Base64 Detection Fails

**Symptoms**: Files are being treated as text instead of binary

**Solution**: Explicitly set `"encoding": "base64"` in the request

## Cost Estimation

Running on Azure Functions Consumption Plan:

| Usage | Monthly Cost (USD) |
|-------|-------------------|
| 1,000 executions | Free (within free tier) |
| 10,000 executions | ~$0.04 |
| 100,000 executions | ~$0.42 |
| 1,000,000 executions | ~$4.20 |

**Calculation based on:**
- Execution time: 500ms average
- Memory: 512 MB
- Free tier: 1M executions + 400,000 GB-s per month

## Planned Features Roadmap

- [ ] Add password protection for zip files
- [ ] Support for nested folder structures
- [ ] Async processing for large files
- [ ] Webhook notifications on completion
- [ ] Multiple compression formats (tar.gz, 7z)
- [ ] Batch processing API

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/NewFeature`)
3. Commit your changes (`git commit -m 'Add some NewFeature'`)
4. Push to the branch (`git push origin feature/NewFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [Azure Functions](https://azure.microsoft.com/en-us/services/functions/)
- Inspired by the need for better file handling in Azure Logic Apps
- Thanks to the Azure Functions team for the excellent Python support

## Contact & Support

- **Issues**: [GitHub Issues] (https://github.com/Gopikrish25/MakeZip/issues)
- **Discussions**: [GitHub Discussions] (https://github.com/Gopikrish25/MakeZip/discussions)
- **Email**: [gopi.sankagkrm@outlook.com]

## ⭐ Show Your Support

If this project helped you, please consider giving it a star! ⭐

---

**Made with ❤️ for the Azure community**
