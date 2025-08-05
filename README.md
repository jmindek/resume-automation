# Resume Automation System

A Level 1 resume automation system that generates customized resumes, cover letters, and interview prep notes based on job descriptions.

## Features

- **Job Description Analysis**: Scrapes and analyzes job postings from URLs
- **Template Selection**: Choose from 4 professional resume templates:
  - Senior Engineering Manager
  - Engineering Manager  
  - Data Engineering Manager
  - Senior Software Engineer
- **AI-Powered Generation**: Uses Anthropic Claude 3.5 Sonnet to generate tailored content
- **Complete Package**: Outputs resume, cover letter, and interview prep notes
- **Simple Interface**: Clean HTML/TypeScript frontend

## Setup

1. **Install Python dependencies**:
   ```bash
   uv pip install -r requirements.txt
   ```

2. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env and add your Anthropic API key
   ```

3. **Run the application**:
   ```bash
   npm run start
   # or
   uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Access the application**:
   Open http://localhost:8000/static/index.html in your browser

## Usage

1. Enter the job description URL
2. Add your motivation notes explaining why you're interested
3. (Optional) Paste your existing resume, or select a template to use as base
4. Click "Generate Resume Package"
5. Review the generated resume, cover letter, and interview prep notes

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