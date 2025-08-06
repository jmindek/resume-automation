from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import anthropic
from typing import List, Optional

from .config_manager import get_config
from .drive_manager import DriveManager
from .job_parser import JobParser
import os
from pathlib import Path

load_dotenv()

app = FastAPI(title="Resume Automation API - Level 2")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Initialize services
config = get_config()
client = anthropic.Anthropic(api_key=config.get('anthropic.api_key'))
drive_manager = None  # Initialize on first use to handle missing credentials gracefully

class ResumeRequest(BaseModel):
    job_url: str
    motivation_notes: str = "I am passionate about building scalable systems and leading engineering teams to deliver high-quality software solutions."
    resume_template: str
    company_name: str = ""  # For Level 2 Google Drive integration
    position_title: str = ""  # For Level 2 Google Drive integration
    use_drive_integration: bool = False  # Enable/disable Drive features

class ResumeResponse(BaseModel):
    resume_text: str
    cover_letter: str
    interview_prep: str
    # Level 2 Google Drive fields
    drive_results: Optional[dict] = None
    success: bool = True
    message: str = ""

def scrape_job_description(url: str) -> str:
    """Scrape job description from URL"""
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text[:5000]  # Limit to first 5000 characters
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to scrape job description: {str(e)}")

def get_base_resume_template(template_type: str) -> str:
    """Get base resume template based on role"""
    templates = {
        "senior_engineering_manager": """
SENIOR ENGINEERING MANAGER TEMPLATE
Name: [Your Name]
Email: [Your Email] | Phone: [Your Phone] | LinkedIn: [Your LinkedIn]

SUMMARY
Experienced engineering leader with [X] years managing high-performing teams and delivering complex technical solutions. Proven track record in scaling engineering organizations, driving technical strategy, and fostering innovation.

EXPERIENCE
[Previous Senior Engineering Manager roles with team size, budget, technical achievements]

TECHNICAL SKILLS
Leadership: Team building, mentoring, performance management
Technical: [Relevant technologies and architectures]
Business: Strategy, roadmap planning, stakeholder management

EDUCATION
[Degree] in [Field] from [University]
""",
        "engineering_manager": """
ENGINEERING MANAGER TEMPLATE
Name: [Your Name]
Email: [Your Email] | Phone: [Your Phone] | LinkedIn: [Your LinkedIn]

SUMMARY
Results-driven engineering manager with expertise in leading development teams and delivering scalable software solutions. Strong background in both technical execution and people management.

EXPERIENCE
[Previous Engineering Manager roles with team accomplishments and technical projects]

TECHNICAL SKILLS
Management: Team leadership, agile methodologies, project management
Technical: [Programming languages, frameworks, tools]
Soft Skills: Communication, problem-solving, cross-functional collaboration

EDUCATION
[Degree] in [Field] from [University]
""",
        "data_engineering_manager": """
DATA ENGINEERING MANAGER TEMPLATE
Name: [Your Name]
Email: [Your Email] | Phone: [Your Phone] | LinkedIn: [Your LinkedIn]

SUMMARY
Data engineering leader specializing in building scalable data infrastructure and managing teams that deliver mission-critical analytics solutions. Expert in modern data stack and ML operations.

EXPERIENCE
[Previous Data Engineering Manager roles with data pipeline achievements and team growth]

TECHNICAL SKILLS
Data Technologies: [Data warehouses, streaming platforms, ETL tools]
Management: Data team leadership, technical roadmap planning
Analytics: Business intelligence, machine learning, data governance

EDUCATION
[Degree] in [Field] from [University]
""",
        "senior_software_engineer": """
SENIOR SOFTWARE ENGINEER TEMPLATE
Name: [Your Name]
Email: [Your Email] | Phone: [Your Phone] | LinkedIn: [Your LinkedIn]

SUMMARY
Senior software engineer with deep expertise in designing and implementing scalable systems. Passionate about clean code, system architecture, and mentoring junior developers.

EXPERIENCE
[Previous Senior SWE roles with technical achievements and system designs]

TECHNICAL SKILLS
Programming: [Languages and frameworks]
Systems: Architecture design, scalability, performance optimization
Collaboration: Code review, technical mentoring, cross-team projects

EDUCATION
[Degree] in [Field] from [University]
"""
    }
    return templates.get(template_type, templates["senior_software_engineer"])

def create_local_drive_files(company_name: str, position_title: str, 
                            resume_content: str, cover_letter_content: str) -> dict:
    """Create local files that will sync to Google Drive"""
    try:
        file_config = config.get('file_organization', {})
        
        # Create folder structure
        folder_structure = file_config.get('folder_structure', 'output/{company_name} - {position_title}/')
        folder_path = folder_structure.format(
            company_name=company_name,
            position_title=position_title
        )
        
        # Create local directory
        local_folder = Path(folder_path)
        local_folder.mkdir(parents=True, exist_ok=True)
        
        results = {}
        
        # Create resume file
        resume_filename = file_config.get('resume_filename', 'Resume - {company_name} - {position_title}')
        resume_name = resume_filename.format(
            company_name=company_name,
            position_title=position_title
        )
        
        resume_file = local_folder / f"{resume_name}.txt"
        with open(resume_file, 'w', encoding='utf-8') as f:
            f.write(resume_content)
        
        results['resume_path'] = str(resume_file)
        results['resume_link'] = f"file://{resume_file.absolute()}"
        
        # Create cover letter file
        cover_letter_filename = file_config.get('cover_letter_filename', 'Cover Letter - {company_name} - {position_title}')
        cover_letter_name = cover_letter_filename.format(
            company_name=company_name,
            position_title=position_title
        )
        
        cover_letter_file = local_folder / f"{cover_letter_name}.txt"
        with open(cover_letter_file, 'w', encoding='utf-8') as f:
            f.write(cover_letter_content)
            
        results['cover_letter_path'] = str(cover_letter_file)
        results['cover_letter_link'] = f"file://{cover_letter_file.absolute()}"
        results['folder_path'] = str(local_folder.absolute())
        
        print(f"Created local files in: {local_folder.absolute()}")
        return results
        
    except Exception as e:
        print(f"Error creating local files: {str(e)}")
        return {}

async def process_with_anthropic(prompt: str) -> str:
    """Process prompt with Anthropic Claude API"""
    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4000,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Anthropic API error: {str(e)}")

@app.post("/api/generate-resume", response_model=ResumeResponse)
async def generate_resume(request: ResumeRequest):
    """Generate resume, cover letter, and interview prep"""
    global drive_manager
    
    # Scrape job description
    job_description = scrape_job_description(request.job_url)
    
    # Get base resume content from Google Drive template or fallback template
    resume_base = ""
    cover_letter_base = ""
    
    # Try to get template content from Google Drive
    try:
        if drive_manager is None:
            drive_manager = DriveManager()
        
        baseline_resume_mapping = config.get_baseline_resume_mapping()
        baseline_resume_name = baseline_resume_mapping.get(request.resume_template)
        
        if baseline_resume_name:
            baseline_resume_id = drive_manager.find_template_by_name(baseline_resume_name)
            if baseline_resume_id:
                drive_content = drive_manager.get_document_content(baseline_resume_id)
                if drive_content:
                    resume_base = drive_content
                    print(f"Successfully loaded baseline resume '{baseline_resume_name}' from Google Drive: {len(drive_content)} characters")
                    print(f"Baseline resume content preview: {drive_content[:200]}...")
                else:
                    print(f"Failed to get content from baseline resume '{baseline_resume_name}' (ID: {baseline_resume_id})")
        
        # Load cover letter template from Google Drive
        cover_letter_template_id = config.get('google_drive.cover_letter_template_id')
        if cover_letter_template_id:
            cover_letter_content = drive_manager.get_document_content(cover_letter_template_id)
            if cover_letter_content:
                cover_letter_base = cover_letter_content
                print(f"Successfully loaded cover letter template from Google Drive: {len(cover_letter_content)} characters")
                print(f"Cover letter template preview: {cover_letter_content[:200]}...")
            else:
                print(f"Failed to get content from cover letter template (ID: {cover_letter_template_id})")
        
    except Exception as e:
        print(f"Failed to load baseline resume from Google Drive: {str(e)}")
    
    # Fallback to built-in template structure if Google Drive failed
    if not resume_base:
        resume_base = get_base_resume_template(request.resume_template)
        print(f"Using fallback template structure for {request.resume_template}")
    
    # Get prompts from configuration
    prompts_config = config.get_prompts()
    
    # Format prompts with variables
    print(f"DEBUG: resume_base length: {len(resume_base)} characters")
    print(f"DEBUG: resume_base preview: {resume_base[:100]}...")
    print(f"DEBUG: resume_base type: {type(resume_base)}")
    print(f"DEBUG: motivation_notes: {request.motivation_notes[:100]}...")
    print(f"DEBUG: job_description length: {len(job_description)}")
    
    formatted_prompt_1 = prompts_config.get('prompt_1', '').format(
        motivation_notes=request.motivation_notes,
        resume_base=resume_base,
        job_description=job_description
    )
    
    print(f"DEBUG: Formatted prompt_1 length: {len(formatted_prompt_1)} characters")
    print(f"DEBUG: Last 500 chars of prompt_1: ...{formatted_prompt_1[-500:]}")
    
    # Check if resume_base actually made it into the formatted prompt
    if resume_base and resume_base in formatted_prompt_1:
        print("✅ Resume content found in formatted prompt")
    else:
        print("❌ Resume content NOT found in formatted prompt")
        print(f"DEBUG: Resume base starts with: '{resume_base[:50]}'" if resume_base else "DEBUG: resume_base is empty/None")
    
    prompts = [
        formatted_prompt_1,
        prompts_config.get('prompt_2', '').format(
            resume_from_prompt_1='[RESUME_FROM_PROMPT_1]',
            job_description=job_description,
            motivation_notes=request.motivation_notes
        ),
        prompts_config.get('prompt_3', '').format(
            job_description=job_description,
            motivation_notes=request.motivation_notes,
            resume_from_prompt_2='[RESUME_FROM_PROMPT_2]',
            cover_letter_base=cover_letter_base if cover_letter_base else "No cover letter template provided."
        ),
        prompts_config.get('prompt_4', '').format(
            job_description=job_description,
            resume_from_prompt_2='[RESUME_FROM_PROMPT_2]',
            motivation_notes=request.motivation_notes
        )
    ]
    
    # Process prompts in sequence
    results = []
    for i, prompt in enumerate(prompts):
        # Replace placeholders with previous results
        if i >= 1:
            prompt = prompt.replace("[RESUME_FROM_PROMPT_1]", results[0])
        if i >= 2:
            prompt = prompt.replace("[RESUME_FROM_PROMPT_2]", results[1])
        
        result = await process_with_anthropic(prompt)
        results.append(result)
    
    # Prepare response data
    response_data = {
        "resume_text": results[1],  # Resume from prompt 2
        "cover_letter": results[2],  # Cover letter from prompt 3
        "interview_prep": results[3],  # Interview prep from prompt 4
        "success": True,
        "message": "Resume package generated successfully"
    }
    
    # Level 2: Google Drive Integration - Generate local files for Drive sync
    if request.use_drive_integration and request.company_name and request.position_title:
        try:
            # Create local files that sync to Google Drive
            local_results = create_local_drive_files(
                company_name=request.company_name,
                position_title=request.position_title,
                resume_content=results[1],
                cover_letter_content=results[2]
            )
            
            if local_results:
                response_data["drive_results"] = local_results
                response_data["message"] += " | Local files created for Google Drive sync"
            else:
                response_data["message"] += " | Warning: Local file creation failed"
                
        except Exception as e:
            response_data["message"] += f" | Local file creation error: {str(e)}"
    
    return ResumeResponse(**response_data)

@app.get("/api/drive/test")
async def test_drive_connection():
    """Test Google Drive API connection"""
    try:
        global drive_manager
        if drive_manager is None:
            drive_manager = DriveManager()
        
        is_connected = drive_manager.test_connection()
        return {
            "connected": is_connected,
            "message": "Google Drive connection successful" if is_connected else "Failed to connect to Google Drive"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Drive connection error: {str(e)}")

@app.get("/api/drive/templates")
async def list_drive_templates():
    """List available resume templates from Google Drive"""
    try:
        global drive_manager
        if drive_manager is None:
            drive_manager = DriveManager()
        
        baseline_resumes = drive_manager.list_template_files()
        return {
            "baseline_resumes": baseline_resumes,
            "baseline_resume_mapping": config.get_baseline_resume_mapping(),
            "templates": baseline_resumes,  # Legacy key for compatibility
            "template_mapping": config.get_baseline_resume_mapping()  # Legacy key for compatibility
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list templates: {str(e)}")

@app.get("/api/config/prompts")
async def get_prompts():
    """Get current prompt configuration"""
    try:
        prompts = config.get_prompts()
        return {"prompts": prompts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get prompts: {str(e)}")

@app.get("/api/config/drive")
async def get_drive_config():
    """Get Google Drive configuration (without sensitive data)"""
    try:
        drive_config = config.get_drive_config()
        file_org_config = config.get('file_organization', {})
        
        # Remove sensitive information
        safe_config = {
            "templates_folder_configured": bool(drive_config.get('templates_folder_id')),
            "output_folder_configured": bool(drive_config.get('output_folder_id')),
            "service_account_configured": bool(drive_config.get('service_account_file')),
            "baseline_resumes": drive_config.get('baseline_resumes', {}),
            "templates": drive_config.get('baseline_resumes', {}),  # Legacy key for frontend compatibility 
            "folder_structure": file_org_config.get('folder_structure', '')
        }
        return safe_config
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get drive config: {str(e)}")

@app.get("/api/debug/template/{template_key}")
async def debug_template_lookup(template_key: str):
    """Debug endpoint to test template lookup"""
    try:
        global drive_manager
        if drive_manager is None:
            drive_manager = DriveManager()
        
        # Get baseline resume mapping
        baseline_resume_mapping = config.get_baseline_resume_mapping()
        baseline_resume_name = baseline_resume_mapping.get(template_key)
        
        if not baseline_resume_name:
            return {"error": f"Template key '{template_key}' not found in config", "available_keys": list(baseline_resume_mapping.keys())}
        
        # Find baseline resume
        baseline_resume_id = drive_manager.find_template_by_name(baseline_resume_name)
        
        return {
            "template_key": template_key,
            "baseline_resume_name": baseline_resume_name,
            "baseline_resume_id": baseline_resume_id,
            "found": bool(baseline_resume_id),
            "available_baseline_resumes": [t['name'] for t in drive_manager.list_template_files()]
        }
        
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/parse-job")
async def parse_job_info(request: dict):
    """Parse job description to extract company name and position title"""
    try:
        job_url = request.get('job_url', '')
        position_title = request.get('position_title', '')  # Allow direct position title input
        job_description = ""
        
        # Scrape job description if URL provided
        if job_url:
            job_description = scrape_job_description(job_url)
        
        # Get default baseline resume from config
        default_template = config.get('google_drive.default_baseline_resume')
        
        # Parse job information or use provided position title
        if position_title and not job_url:
            # Direct position title provided, just auto-select template
            suggested_template = JobParser.select_resume_template(position_title)
            if not suggested_template and default_template:
                suggested_template = default_template
                
            parsed_info = {
                'company_name': '',
                'position_title': position_title,
                'suggested_template': suggested_template,
                'confidence': 'high',  # High confidence for direct input
                'template_source': 'auto-detected' if JobParser.select_resume_template(position_title) else 'default'
            }
        else:
            # Normal parsing from job description
            parsed_info = JobParser.parse_job_posting(job_description, job_url, default_template)
        
        return {
            "success": True,
            "company_name": parsed_info.get('company_name', ''),
            "position_title": parsed_info.get('position_title', ''),
            "suggested_template": parsed_info.get('suggested_template', ''),
            "template_source": parsed_info.get('template_source', 'none'),
            "confidence": parsed_info.get('confidence', 'low'),
            "message": f"Extracted with {parsed_info.get('confidence', 'low')} confidence"
        }
        
    except Exception as e:
        return {
            "success": False,
            "company_name": "",
            "position_title": "",
            "confidence": "low",
            "message": f"Error parsing job: {str(e)}"
        }

@app.get("/")
async def root():
    """Serve the frontend"""
    return {
        "message": "Resume Automation API - Level 2 is running",
        "version": "2.0",
        "features": [
            "Fast-agent resume generation",
            "Google Drive integration",
            "Configurable prompts",
            "PDF generation",
            "Organized file structure"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)