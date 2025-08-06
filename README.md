# Resume Automation System - Level 2

An advanced resume automation system that generates customized resumes, cover letters, and interview prep notes, with integrated Google Drive document management.

## Level 1 Features (Core)

- **Job Description Analysis**: Scrapes and analyzes job postings from URLs
- **4-Prompt Chain Workflow**: Elite resume writing process using configurable prompts
- **Template Selection**: Choose from 4 professional resume templates
- **AI-Powered Generation**: Uses Anthropic Claude 3.5 Sonnet to generate tailored content
- **Complete Package**: Outputs resume, cover letter, and interview prep notes

## Level 2 Features (Google Drive Integration) 🚀

- **Google Drive Authentication**: Secure service account integration
- **Template Management**: Access resume templates directly from Google Drive
- **Automated Document Creation**: Creates organized Google Docs and PDFs
- **File Organization**: Structured folders: `Job Applications/[Company] - [Position]/`
- **PDF Generation**: Automatic PDF exports for easy sharing
- **Real-time Status**: Connection testing and configuration validation
- **Configurable Prompts**: Easy customization through `config.yaml`

## Quick Start (Level 1)

1. **Install dependencies**: `uv pip install -r requirements.txt`
2. **Set up environment**: `cp .env.example .env` and add your Anthropic API key
3. **Run**: `npm run start`
4. **Access**: http://localhost:8000/static/index.html

## Level 2 Setup (Google Drive Integration)

For full Google Drive integration, follow the detailed setup guide: **[SETUP_LEVEL_2.md](SETUP_LEVEL_2.md)**

**Quick checklist:**
- [ ] Google Cloud project with Drive & Docs APIs enabled
- [ ] Service account created and `service_account.json` downloaded
- [ ] Google Drive folders created and shared with service account
- [ ] `config.yaml` updated with folder IDs
- [ ] Templates uploaded to Google Drive

## Usage

### Level 1 (Basic)
1. Enter job description URL and motivation notes
2. Paste existing resume OR select a template
3. Click "Generate Resume Package" 
4. Review text outputs

### Level 2 (Google Drive)
1. Enable "Google Drive Integration" checkbox
2. Enter company name and position title
3. System automatically:
   - Creates organized folder structure
   - Copies and customizes resume template
   - Generates cover letter document
   - Creates PDF versions
   - Provides direct links to Google Docs

## Features

### Elite Resume Writing Process

The system implements a 4-step process using your custom prompts:

1. **Resume Alignment**: Analyzes job description and aligns your experience using Problem-Solution-Impact format
2. **Optimization**: Takes the resume to 10/10 recruiter pick likelihood through strategic improvements
3. **Cover Letter**: Generates a compelling 200-250 word cover letter with mission alignment
4. **Interview Prep**: Provides strategic interview positioning with core narratives and proof points

### Resume Templates

Modify the resume templates in the `get_base_resume_template()` function in `backend/main.py` to match your experience and formatting preferences.

## API Endpoints

- `POST /api/generate-resume`: Generate resume package
- `GET /`: Health check

## Tech Stack

- **Backend**: FastAPI, Python
- **AI**: Anthropic Claude 3.5 Sonnet
- **Frontend**: HTML, TypeScript, Vanilla JS
- **Web Scraping**: BeautifulSoup, Requests