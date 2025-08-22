# Resume Automation System

An AI-powered resume generation system that creates tailored resumes, cover letters, and interview prep notes based on job descriptions.

## Features

- 🤖 AI-powered resume optimization using Claude AI
- 📄 Automated cover letter generation
- 🎯 Automated Interview preparation notes
- 📁 Google Drive integration for file organization via API or Drive for Mac/Windows
- 🔄 Template-based document generation
- 📊 Application tracking with Excel integration
- 🌐 Web interface for easy use

## Prerequisites

- Python 3.9+
- Either 
  - Google Drive for Mac/Windows
  - Google Drive API enabled
- Anthropic Claude API access
- Existing Resume content

## Setup Instructions

### 1. Clone and Install

```bash
git clone <your-repo-url>
cd resume-automation
pip install -r requirements.txt
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

1. Create a Google Cloud Project and enable the Drive API
2. Create a Service Account and download the JSON credentials
3. Save the credentials as `service_account.json` in the project root
4. Share your Google Drive folders with the service account email

### 4. Configuration

1. Copy the configuration template:
   ```bash
   cp config_template.yaml config.yaml
   ```

2. Edit `config.yaml` and update:
   - `google_drive.templates_folder_id`: Your Google Drive templates folder ID
   - `google_drive.output_folder_id`: Your Google Drive output folder ID
   - `file_organization.drive_for_mac_root`: Your Google Drive sync path
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
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

### Web Interface

Open http://localhost:8000/static/index.html in your browser to access the web interface.

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

### Prompt Configuration

The system uses 4 prompts:
1. **Prompt 1**: Resume optimization
2. **Prompt 2**: Resume refinement (optional)
3. **Prompt 3**: Cover letter generation
4. **Prompt 4**: Interview prep notes

## Security Notes

- Never commit `.env` or `service_account.json` files
- Never commit `config.yaml` or `prompts.yaml` files
- Use environment variables for sensitive configuration
- Regularly rotate API keys and service account credentials

## Troubleshooting

### Common Issues

1. **"No resume content loaded"**: Check that baseline resume files exist in `templates/resumes/`
2. **Google Drive authentication errors**: Verify service account permissions
3. **API rate limits**: Adjust `system.rate_limit_delay` in config.yaml
4. **Template parsing errors**: Ensure template files have correct format

### Debugging

Enable debug mode by setting environment variable:
```bash
export DEBUG=true
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