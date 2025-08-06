# Resume Automation System - Level 2 Setup Guide

## Overview
Level 2 adds Google Drive integration to automatically create organized documents and PDFs from your resume automation process.

## Prerequisites
1. Google Cloud Project with Drive and Docs APIs enabled
2. Service Account credentials
3. Google Drive folders set up for templates and output

## Step-by-Step Setup

### 1. Google Cloud Setup

#### A. Create/Configure Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable required APIs:
   - Google Drive API
   - Google Docs API

#### B. Create Service Account
1. Go to **IAM & Admin > Service Accounts**
2. Click **Create Service Account**
3. Fill in details:
   - Name: `resume-automation`
   - Description: `Service account for resume automation system`
4. Click **Create and Continue**
5. Skip role assignment (click **Continue**)
6. Click **Done**

#### C. Generate Service Account Key
1. Click on your service account
2. Go to **Keys** tab
3. Click **Add Key > Create new key**
4. Select **JSON** format
5. Download the file
6. Rename it to `service_account.json`
7. Move it to your project root directory

### 2. Google Drive Setup

#### A. Create Folder Structure
1. Create a main folder for templates (e.g., "Resume Templates")
2. Upload your 4 resume templates as Google Docs:
   - `Senior_Engineering_Manager_Template`
   - `Engineering_Manager_Template`
   - `Data_Engineering_Manager_Template`
   - `Senior_Software_Engineer_Template`
3. Create an output folder (e.g., "Job Applications")

#### B. Share Folders with Service Account
1. Right-click each folder > **Share**
2. Add your service account email (found in `service_account.json`)
3. Give **Editor** permissions

#### C. Get Folder IDs
1. Open each folder in Google Drive
2. Copy the folder ID from the URL:
   - URL: `https://drive.google.com/drive/folders/1ABC123XYZ`
   - Folder ID: `1ABC123XYZ`

### 3. Configuration

#### A. Update config.yaml
```yaml
google_drive:
  service_account_file: "service_account.json"
  templates_folder_id: "YOUR_TEMPLATES_FOLDER_ID"  # Replace with actual ID
  output_folder_id: "YOUR_OUTPUT_FOLDER_ID"        # Replace with actual ID
  
  templates:
    senior_engineering_manager: "Senior_Engineering_Manager_Template"
    engineering_manager: "Engineering_Manager_Template"
    data_engineering_manager: "Data_Engineering_Manager_Template"
    senior_software_engineer: "Senior_Software_Engineer_Template"
```

#### B. Environment Variables
```bash
cp .env.example .env
# Edit .env and add your Anthropic API key
```

### 4. Installation

```bash
# Install dependencies
uv pip install -r requirements.txt

# Start the application
npm run start
```

### 5. Testing

1. Access the application at: http://localhost:8000/static/index.html
2. Check Google Drive status in the web interface
3. Click "Test Connection" to verify setup
4. Try a complete workflow with Drive integration enabled

### 6. Template Format

Your Google Docs templates should use placeholder text that can be easily replaced:

```
{{NAME}}
{{EMAIL}}
{{PHONE}}
{{LINKEDIN}}
{{POSITION}}
{{COMPANY}}
```

The system will replace these with actual values during processing.

## Troubleshooting

### Common Issues

1. **"Service account file not found"**
   - Ensure `service_account.json` is in the project root
   - Check file permissions

2. **"Failed to connect to Google Drive"**
   - Verify APIs are enabled in Google Cloud Console
   - Check service account has access to folders
   - Ensure folder IDs are correct

3. **"Template not found"**
   - Verify template names in config.yaml match Google Docs names
   - Check templates folder ID is correct
   - Ensure service account has access to templates folder

4. **"Permission denied"**
   - Share folders with service account email
   - Give Editor permissions (not just Viewer)

### Debug Commands

```bash
# Test Drive connection
curl http://localhost:8000/api/drive/test

# List templates
curl http://localhost:8000/api/drive/templates

# Check configuration
curl http://localhost:8000/api/config/drive
```

## File Organization

When Drive integration is enabled, files are organized as:
```
Job Applications/
└── [Company Name] - [Position Title]/
    ├── Resume - [Company] - [Position].docx
    ├── Resume - [Company] - [Position].pdf
    ├── Cover Letter - [Company] - [Position].docx
    └── Cover Letter - [Company] - [Position].pdf
```

## Security Notes

- Keep `service_account.json` secure and never commit to version control
- Service account has full access to shared folders only
- Consider using folder-level permissions rather than drive-wide access
- Regularly rotate service account keys if needed

## Support

If you encounter issues:
1. Check the application logs
2. Verify Google Cloud Console settings
3. Test API endpoints manually
4. Review folder permissions in Google Drive