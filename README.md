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

### 6. Google Drive Folder Structure and Templates

#### A. Create Folder Structure
Create this folder structure in your Google Drive:

```
resume-automation-system/
├── templates/
│   ├── resumes/              # Your baseline resume content files
│   │   ├── Engineering Manager.docx
│   │   ├── Senior Software Engineer.docx
│   │   ├── Data Engineering Manager.docx
│   │   └── Senior Engineering Manager.docx
│   ├── Engineering Manager Template.docx     # Output formatting templates
│   ├── Cover Letter Template.docx
│   └── Interview Prep Notes Template.docx
└── ready-for-review/
    └── (generated resumes will appear here)
```

#### B. Copy Templates from Repository
**Important:** Copy all template files from this repository's `templates/` folder to your Google Drive `resume-automation-system/templates/` folder. These include:
- All `.docx` template files for output formatting
- Sample baseline resume files

#### C. Create Your Baseline Resume Files
In the `templates/resumes/` folder, create your baseline resume files. **The filenames must exactly match the template names in your `config.yaml`:**

- If `config.yaml` lists `engineering_manager: "Engineering Manager"`, create `Engineering Manager.docx`
- If `config.yaml` lists `senior_software_engineer: "Senior Software Engineer"`, create `Senior Software Engineer.docx`
- And so on...

These files contain your complete resume content that will be optimized for each specific job application.

## Usage

### Daily Workflow - How to Apply for Jobs

Here's the typical workflow for applying to jobs using this system:

#### 1. Generate Resume Package
1. **Find a job** you want to apply for
2. **Copy the job posting URL** and paste it into the "Job Description URL" field
3. **Review auto-detected information**:
   - Company name (auto-scraped from URL)
   - Role/position title (auto-detected from job description)
   - Salary range (if available)
   - Best-fit resume template (auto-selected based on job requirements)
4. **Verify and correct** any auto-detected fields if needed
5. **Add your motivation notes** explaining why you're interested in this role
6. **Click "Generate Resume Package"**

The system will create:
- Tailored resume optimized for this specific job
- Custom cover letter
- Interview preparation notes

#### 2. Review and Download from Google Drive
1. **Navigate to your Google Drive** → `resume-automation-system/ready-for-review/[Company] - [Position]/`
2. **Review the generated resume**:
   - Ideally, make no changes or only trivial adjustments
   - The content should be pre-optimized for the job
3. **Review the generated cover letter**:
   - Again, ideally minimal to no changes needed
   - Should be tailored to the company and role
4. **Download both files**:
   - Save as DOCX for editing capability
   - Save as PDF for final submission

#### 3. Apply for the Job
1. **Submit your application** through the company's normal process
2. **Upload the generated resume** (PDF recommended)
3. **Upload the generated cover letter** (PDF recommended)
4. **Use the interview prep notes** to prepare for potential interviews

#### 4. Track Your Application
1. **Open the resume tracker** (Excel file in your Google Drive)
2. **Find your job entry** - it should be pre-populated with:
   - Company name
   - Role/position title
   - Job posting URL
   - Salary range (if detected)
3. **Update the "Applied" column** with today's date
4. **Track follow-ups** and interview progress as they occur

This workflow is designed to take a job application from discovery to submission in under 10 minutes, with most of that time spent on review rather than content creation.

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

## Important Limitations and Considerations

⚠️ **Version 1 Limitations - Please Read:**

### Template Limitations
- **Single output format**: There is only one type of output resume template. If you don't like the format, you'll need to create your own Jinja2 template or you may find this application unusable.
- **Jinja2 knowledge helpful**: Users familiar with Jinja templating will find customization straightforward. Others may find template modification to be an insurmountable barrier.

### Baseline Resume Recommendations
- **Use baseline files**: While you technically don't need baseline resume files (you could paste content each time), this would dramatically slow you down and counteract one of the main goals of this application.
- **Recommended**: Create and maintain your baseline resume files as described in the setup.

### Configuration Customization
- **4-job limit**: The output resume is configured to contain only 4 jobs by default. Modify `config.yaml` to increase or decrease this number.
- **Customize everything**: Modify `config.yaml` to adjust:
  - Number of achievements per job
  - Prompt optimization for your specific situation
  - Personal information and company details
  - Template mappings and file names

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

**Important:** Your baseline resume files in `templates/resumes/` must be named exactly as shown in the right column above. For example:
- `Engineering Manager.docx` (matches the `engineering_manager` template)
- `Senior Software Engineer.docx` (matches the `senior_software_engineer` template)

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