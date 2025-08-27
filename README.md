# Resume Automation System

An AI-powered resume generation system that creates tailored resumes, cover letters, and interview prep notes based on job descriptions.

## Features

- 🤖 AI-powered resume optimization using Claude AI
- 📄 Automated cover letter generation
- 🎯 Automated Interview preparation notes
- 📁 Google Drive integration via Google Drive sync folder (requires Google Drive for Mac/Windows)
- 🔄 Template-based document generation
- 📊 Application tracking with Excel integration
- 🌐 Web interface for easy use

## Prerequisites

- Python 3.9+
- Google Drive for Mac/Windows installed and syncing
- Anthropic Claude API access
- Existing Resume content

## Setup Instructions

### 1. Clone and Install

```bash
git clone <your-repo-url>
cd resume-automation
uv pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and add your Anthropic API key:
```
ANTHROPIC_API_KEY=your_api_key_here
```

### 3. Google Drive Setup

The system uses your local Google Drive sync folder (requires Google Drive for Mac/Windows to be installed and syncing).

### 4. Configuration

1. Copy the configuration template:
   ```bash
   cp config_template.yaml config.yaml
   ```

2. Edit `config.yaml` and update:
   - `file_organization.drive_for_mac_root`: Your Google Drive sync path (e.g., `/Users/yourname/Library/CloudStorage/GoogleDrive-your.email@gmail.com/My Drive`)
   - `user` section: Your personal information

### 5. Prompts Configuration

1. Copy the prompts template:
   ```bash
   cp prompts_template.yaml prompts.yaml
   ```

2. Edit `prompts.yaml` and replace placeholders:
   - `{name}`: Your full name
   - `{phone}`: Your phone number
   - `{email}`: Your email address
   - `{city_state}`: Your city and state
   - `{company_name1},{company_1_date_range}`: Company name 1 and date range
   - `{company_name2},{company_2_date_range}`: Company name 2 and date range
   - `{company_name3},{company_3_date_range}`: Company name 3 and date range
   - `{company_name4},{company_4_date_range}`: Company name 4 and date range

### 6. Google Drive Folder Structure

Create this folder structure in your Google Drive:

```
resume-automation-system/
├── templates/
│   ├── resumes/
│   │   ├── Engineering Manager.docx
│   │   ├── Senior Software Engineer.docx
│   │   └── Data Engineering Manager.docx
│   ├── Engineering Manager Template.docx
│   ├── Cover Letter Template.docx
│   └── Interview Prep Notes Template.docx
└── ready-for-review/
    └── (generated resumes will appear here)
```

## Usage

### Start the Server

```bash
npm run dev
# or alternatively:
uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

This will start the FastAPI server with hot-reload enabled on http://localhost:8000

### Web Interface

Open http://localhost:8000/static/index.html in your browser to access the web interface.

### Alternative Start Commands

```bash
# Using npm (recommended)
npm run dev

# Using uv directly
uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# For production
uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

## Configuration Options

### Resume Templates

Available templates in `config.yaml`:
- `engineering_manager`: Engineering Manager
- `senior_engineering_manager`: Senior Engineering Manager  
- `data_engineering_manager`: Data Engineering Manager
- `senior_software_engineer`: Senior Software Engineer
- `software_engineer`: Software Engineer
- `lead_data_engineer`: Lead Data Engineer
- `data_engineer`: Data Engineer

### Template Format

Your .docx templates should use Jinja2 template tags that can be replaced:

```
{{name}}
{{email}}
{{phone}}
{{linkedin}}
{{jobtitle}}
{{company}}
{{content}}
{{key_achievements_list}}
{{skill_categories}}
```

The system uses DocxTpl to replace these template tags with actual values during processing.

### Prompt Configuration

The system uses 3 prompts:
1. **Prompt 1**: Resume optimization
2. **Prompt 2**: Cover letter generation
3. **Prompt 3**: Interview prep notes

## Security Notes

- Never commit `.env` or `service_account.json` files
- Never commit `config.yaml` or `prompts.yaml` files
- Use environment variables for sensitive configuration
- Regularly rotate API keys and service account credentials
- Keep `service_account.json` secure and never commit to version control
- Service account has full access to shared folders only
- Consider using folder-level permissions rather than drive-wide access
- Regularly rotate service account keys if needed

## Troubleshooting

### Common Issues

1. **"No resume content loaded"**: Check that baseline resume files exist in `templates/resumes/`
2. **Google Drive authentication errors**: Verify service account permissions
3. **API rate limits**: Adjust `system.rate_limit_delay` in config.yaml
4. **Template parsing errors**: Ensure template files have correct format
5. **"Service account file not found"**: Ensure `service_account.json` is in the project root and check file permissions
6. **"Failed to connect to Google Drive"**: Verify APIs are enabled in Google Cloud Console, check service account has access to folders, and ensure folder IDs are correct
7. **"Template not found"**: Verify template names in config.yaml match actual template files, check templates folder ID is correct
8. **"Permission denied"**: Share folders with service account email and give Editor permissions (not just Viewer)

### Debugging

Enable debug mode by setting environment variable:
```bash
export DEBUG=true
```

#### Debug Commands

```bash
# Test the resume generation endpoint
curl -X POST "http://localhost:8000/api/generate-resume" \
  -H "Content-Type: application/json" \
  -d '{"job_description": "test job", "motivation_notes": "test motivation", "resume_template": "engineering_manager", "company_name": "TestCorp", "position_title": "Test Role"}'
```

#### File Organization

Files are created in your Google Drive sync folder and organized as:
```
[Your Google Drive]/resume-automation-system/ready-for-review/
└── [Company Name] - [Position Title]/
    ├── Resume - [Company] - [Position].docx
    ├── Cover Letter - [Company] - [Position].docx
    └── Interview Prep Notes - [Company].docx
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

TBD

## Support

For issues and questions, please open a GitHub issue.