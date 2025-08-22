from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import anthropic
from typing import List, Optional, Tuple
from datetime import datetime
import asyncio
import uuid
import json
from fastapi.responses import StreamingResponse

from backend.config_manager import get_config
from backend.drive_manager import DriveManager
from backend.job_parser import JobParser
from backend.docx_utils import read_docx_content, write_docx_content, copy_docx_with_new_content, smart_content_replacement, smart_template_replacement, multi_tag_template_replacement, tag_based_template_replacement, find_template_and_baseline_files, read_content_file, parse_claude_response_for_tags, parse_interview_prep_response
from backend.excel_tracker import create_resume_tracker
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

class EnabledPrompts(BaseModel):
    prompt_1: bool = True
    prompt_2: bool = False
    prompt_3: bool = True
    prompt_4: bool = False

class ResumeRequest(BaseModel):
    job_url: str = ""  # Now optional - can be empty if job_description is provided
    job_description: str = ""  # Manual job description input - optional
    additional_details: str = ""  # Additional context for the application
    motivation_notes: str = "I am passionate about building scalable systems and leading engineering teams to deliver high-quality software solutions."
    resume_template: str
    company_name: str = ""  # For Level 2 Google Drive integration
    position_title: str = ""  # For Level 2 Google Drive integration
    use_drive_integration: bool = False  # Enable/disable Drive features
    claude_model: str = "claude-sonnet-4-20250514"  # Default to Sonnet 4
    enabled_prompts: EnabledPrompts = EnabledPrompts()  # Prompt control settings
    enable_resume_tracking: bool = False  # Excel tracking toggle
    prevent_duplicate_resumes: bool = False  # Duplicate prevention toggle
    # Removed session_id - no more progress tracking

class ResumeResponse(BaseModel):
    resume_text: str
    cover_letter: str
    interview_prep: str
    # Level 2 Google Drive fields
    drive_results: Optional[dict] = None
    success: bool = True
    message: str = ""

# Removed complex progress tracking - keeping it simple

def scrape_job_description(url: str) -> str:
    """Scrape job description from URL and return cleaned text"""
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

def scrape_job_content(url: str) -> Tuple[str, str]:
    """Scrape job content and return both raw HTML and cleaned text"""
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        raw_html = response.text
        
        # Also create cleaned text version for prompts
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        cleaned_text = ' '.join(chunk for chunk in chunks if chunk)
        
        # Check if this is a SPA page with no content
        print(f"DEBUG: cleaned_text length: {len(cleaned_text.strip())}")
        print(f"DEBUG: is_spa_page: {JobParser._is_spa_page(raw_html)}")
        
        if len(cleaned_text.strip()) < 100 and JobParser._is_spa_page(raw_html):
            print("🔄 SPA page detected, creating synthetic job description from URL...")
            try:
                synthetic_description = create_synthetic_job_description(url, raw_html)
                print(f"DEBUG: synthetic_description created: {len(synthetic_description) if synthetic_description else 0} chars")
                if synthetic_description:
                    print(f"✅ Created synthetic job description ({len(synthetic_description)} chars)")
                    return raw_html, synthetic_description
                else:
                    print("❌ Could not create synthetic job description")
            except Exception as e:
                print(f"❌ Error creating synthetic job description: {e}")
        else:
            print(f"DEBUG: Using regular cleaned text ({len(cleaned_text)} chars)")
        
        return raw_html, cleaned_text[:5000]  # Return both versions
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to scrape job content: {str(e)}")

def create_synthetic_job_description(url: str, raw_html: str) -> str:
    """Create a synthetic job description for SPA pages based on URL and available data"""
    try:
        # Parse job information from the URL and HTML
        job_info = JobParser.parse_job_posting(raw_html, url)
        
        company = job_info.get('company_name', 'the company')
        position = job_info.get('position_title', 'this position')
        salary = job_info.get('salary', 'competitive salary')
        
        # Create a synthetic job description template
        synthetic_description = f"""
Job Title: {position}
Company: {company}
Location: Remote/Hybrid available
Salary: {salary}

We are seeking a {position} to join our team at {company}. This is an exciting opportunity to work with a growing technology company.

Key Responsibilities:
- Lead and manage engineering teams
- Drive technical strategy and architecture decisions  
- Collaborate with cross-functional teams
- Mentor and develop team members
- Ensure delivery of high-quality software solutions

Requirements:
- Proven experience in engineering management
- Strong technical background in software development
- Experience with modern technology stacks
- Leadership and team building skills
- Excellent communication abilities

What We Offer:
- {salary}
- Flexible work arrangements
- Professional development opportunities
- Collaborative work environment
- Growth opportunities

URL: {url}

Note: This is a synthetic job description created from available URL data. Please refer to the original job posting for complete details.
        """
        
        return synthetic_description.strip()
        
    except Exception as e:
        print(f"Error creating synthetic job description: {e}")
        return ""

def create_drive_sync_files(company_name: str, position_title: str, 
            resume_template: str, resume_content: str, cover_letter_content: str, 
            interview_prep_content: str = "", use_template_system: bool = False,
            template_file: Optional[Path] = None, prompt_full_results: Optional[dict] = None) -> dict:
    """Create files in Google Drive sync folder by copying baseline resume and creating cover letter"""
    try:
        file_config = config.get('file_organization', {})
        drive_root = file_config.get('drive_for_mac_root', '')
        
        if not drive_root:
            raise Exception("Google Drive for Mac root path not configured")
        
        # Create full folder path using Drive sync root + folder structure
        folder_structure = file_config.get('folder_structure', 'resume-automation-system/ready-for-review/{company_name} - {position_title}/')
        relative_folder = folder_structure.format(
            company_name=company_name,
            position_title=position_title
        )
        
        full_folder_path = Path(drive_root) / relative_folder
        full_folder_path.mkdir(parents=True, exist_ok=True)
        
        results = {}
        
        # 1. Copy baseline resume and update with optimized content
        resume_filename = file_config.get('resume_filename', 'Jerry Mindek {position_title} - {company_name}')
        resume_name = resume_filename.format(
            company_name=company_name,
            position_title=position_title
        )
        
        # Find the original baseline resume file to copy from
        baseline_resume_mapping = config.get_baseline_resume_mapping()
        baseline_resume_name = baseline_resume_mapping.get(resume_template)
        
        templates_folder = Path(drive_root) / "resume-automation-system" / "templates"
        potential_baseline_files = [
            templates_folder / f"{baseline_resume_name}.docx",
            templates_folder / f"{baseline_resume_name}.txt",
            templates_folder / baseline_resume_name
        ]
        
        baseline_file = None
        for potential_file in potential_baseline_files:
            if potential_file.exists():
                baseline_file = potential_file
                break
        
        if baseline_file or use_template_system:
            resume_docx_file = full_folder_path / f"{resume_name}.docx"
            resume_txt_file = full_folder_path / f"{resume_name}.txt"
            
            # Always create text version
            with open(resume_txt_file, 'w', encoding='utf-8') as f:
                f.write(resume_content)
            
            # Create .docx version based on system type
            if use_template_system and template_file:
                # Use docxtpl-based template replacement for 2-document system
                print(f"DEBUG: Resume content length: {len(resume_content)}")
                print(f"DEBUG: Resume content preview: {resume_content[:300]}...")
                
                # Parse Claude's response to extract tag values
                tag_values = parse_claude_response_for_tags(resume_content, "")  # baseline_content if needed
                print(f"DEBUG: Extracted {len(tag_values)} tag values: {list(tag_values.keys())}")
                
                copy_success = tag_based_template_replacement(template_file, resume_docx_file, tag_values)
                if copy_success:
                    print(f"Created resume using docxtpl template system: {resume_docx_file}")
                else:
                    print(f"Failed to create .docx resume using template system: {resume_docx_file}")
            else:
                # Use original content replacement system
                copy_success = write_docx_content(resume_docx_file, resume_content, preserve_formatting=True)
                if copy_success:
                    print(f"Created optimized resume with structured formatting: {resume_docx_file}")
                else:
                    print(f"Failed to create .docx resume: {resume_docx_file}")
            
            results['resume_path'] = str(resume_docx_file) if copy_success else str(resume_txt_file)
            results['resume_txt_path'] = str(resume_txt_file)
            results['resume_docx_path'] = str(resume_docx_file) if copy_success else None
            results['resume_link'] = f"file://{resume_docx_file.absolute()}" if copy_success else f"file://{resume_txt_file.absolute()}"
            
            if copy_success:
                system_type = "tag-based template system" if use_template_system else "structured formatting"
                print(f"Successfully created resume using {system_type}: {resume_docx_file}")
            else:
                print(f"Failed to create .docx resume, created text file only: {resume_txt_file}")
        else:
            # Fallback: create new files if baseline not found
            resume_txt_file = full_folder_path / f"{resume_name}.txt"
            resume_docx_file = full_folder_path / f"{resume_name}.docx"
            
            with open(resume_txt_file, 'w', encoding='utf-8') as f:
                f.write(resume_content)
            
            write_docx_success = write_docx_content(resume_docx_file, resume_content, preserve_formatting=True)
            
            results['resume_path'] = str(resume_docx_file) if write_docx_success else str(resume_txt_file)
            results['resume_txt_path'] = str(resume_txt_file)
            results['resume_docx_path'] = str(resume_docx_file) if write_docx_success else None
            results['resume_link'] = f"file://{resume_docx_file.absolute()}" if write_docx_success else f"file://{resume_txt_file.absolute()}"
            print(f"Baseline resume not found, created new files: {resume_txt_file}" + (f" and {resume_docx_file}" if write_docx_success else ""))
        
        # 2. Create cover letter file
        cover_letter_filename = file_config.get('cover_letter_filename', 'Cover Letter - {company_name} - {position_title}')
        cover_letter_name = cover_letter_filename.format(
            company_name=company_name,
            position_title=position_title
        )
        
        # Create both .txt and .docx versions
        cover_letter_txt_file = full_folder_path / f"{cover_letter_name}.txt"
        cover_letter_docx_file = full_folder_path / f"{cover_letter_name}.docx"
        
        # Write text version
        with open(cover_letter_txt_file, 'w', encoding='utf-8') as f:
            f.write(cover_letter_content)
        
        # Try to use cover letter template with {{CONTENT}} tag support
        cover_letter_docx_success = False
        cover_letter_template_file = None
        
        # Look for cover letter template
        potential_cover_letter_template_files = [
            templates_folder / "Cover Letter Template.docx",
            templates_folder / "Cover Letter Template.txt", 
            templates_folder / "Cover Letter Template"
        ]
        
        for potential_file in potential_cover_letter_template_files:
            if potential_file.exists():
                cover_letter_template_file = potential_file
                break
        
        if cover_letter_template_file and cover_letter_template_file.suffix.lower() == '.docx':
            # Use docxtpl for cover letter template replacement
            try:
                print(f"DEBUG: Cover letter content length: {len(cover_letter_content)}")
                print(f"DEBUG: Cover letter content preview: {cover_letter_content[:300]}...")
                
                # Parse Claude's full response (with template tags) for cover letter tags
                cover_letter_full_response = cover_letter_content
                if prompt_full_results and 3 in prompt_full_results:
                    cover_letter_full_response = prompt_full_results[3]
                    print(f"DEBUG: Using full Claude response for cover letter template parsing")
                else:
                    print(f"DEBUG: Using extracted content for cover letter template parsing (may not work)")
                
                cover_letter_tags = parse_claude_response_for_tags(cover_letter_full_response, "")
                print(f"DEBUG: Cover letter extracted {len(cover_letter_tags)} tag values: {list(cover_letter_tags.keys())}")
                
                if cover_letter_tags:
                    # Use docxtpl to populate the template
                    cover_letter_docx_success = tag_based_template_replacement(
            cover_letter_template_file, 
            cover_letter_docx_file, 
            cover_letter_tags
                    )
                    if cover_letter_docx_success:
                        print(f"Used docxtpl cover letter template with tags: {list(cover_letter_tags.keys())}")
                    else:
                        print(f"docxtpl template replacement failed, falling back to new document creation")
                else:
                    print("No cover letter tags found in Claude response, falling back to new document creation")
                    cover_letter_docx_success = False
                    
            except Exception as e:
                print(f"Error using docxtpl cover letter template: {str(e)}")
                cover_letter_docx_success = False
        
        # Fallback: create new .docx if template approach failed
        if not cover_letter_docx_success:
            cover_letter_docx_success = write_docx_content(cover_letter_docx_file, cover_letter_content, preserve_formatting=True)
            
        results['cover_letter_path'] = str(cover_letter_docx_file) if cover_letter_docx_success else str(cover_letter_txt_file)
        results['cover_letter_txt_path'] = str(cover_letter_txt_file)
        results['cover_letter_docx_path'] = str(cover_letter_docx_file) if cover_letter_docx_success else None
        results['cover_letter_link'] = f"file://{cover_letter_docx_file.absolute()}" if cover_letter_docx_success else f"file://{cover_letter_txt_file.absolute()}"
        
        # 3. Create interview prep notes file using docx template
        if interview_prep_content:
            interview_prep_filename = f"{company_name} - Interview Prep Notes"
            interview_prep_docx_file = full_folder_path / f"{interview_prep_filename}.docx"
            interview_prep_txt_file = full_folder_path / f"{interview_prep_filename}.txt"
            
            # Always create text version
            with open(interview_prep_txt_file, 'w', encoding='utf-8') as f:
                f.write(f"# Interview Prep Notes - {company_name}\n\n")
                f.write(f"**Position:** {position_title}\n\n")
                f.write("---\n\n")
                f.write(interview_prep_content)
            
            # Try to use interview prep template
            interview_prep_template_file = templates_folder / "Interview Prep Notes Template.docx"
            interview_prep_docx_success = False
            
            if interview_prep_template_file.exists():
                try:
                    print(f"Using interview prep template: {interview_prep_template_file}")
                    
                    # Parse Claude's structured response
                    interview_prep_tags = parse_interview_prep_response(interview_prep_content)
                    
                    # Add basic info tags
                    interview_prep_tags['jobtitle'] = position_title
                    interview_prep_tags['company'] = company_name
                    
                    # Use docxtpl for template replacement
                    interview_prep_docx_success = tag_based_template_replacement(
            interview_prep_template_file, 
            interview_prep_docx_file, 
            interview_prep_tags
                    )
                    
                    if interview_prep_docx_success:
                        print(f"Created interview prep using template: {interview_prep_docx_file}")
                    else:
                        print(f"Template replacement failed, using text file only")
                        
                except Exception as template_error:
                    print(f"Error using interview prep template: {template_error}")
            else:
                print(f"Interview prep template not found: {interview_prep_template_file}")
            
            results['interview_prep_path'] = str(interview_prep_docx_file) if interview_prep_docx_success else str(interview_prep_txt_file)
            results['interview_prep_docx_path'] = str(interview_prep_docx_file) if interview_prep_docx_success else None
            results['interview_prep_txt_path'] = str(interview_prep_txt_file)
            results['interview_prep_link'] = f"file://{interview_prep_docx_file.absolute()}" if interview_prep_docx_success else f"file://{interview_prep_txt_file.absolute()}"
        else:
            results['interview_prep_path'] = None
            results['interview_prep_docx_path'] = None
            results['interview_prep_txt_path'] = None
            results['interview_prep_link'] = None
        
        results['folder_path'] = str(full_folder_path.absolute())
        
        print(f"Created files in Google Drive sync folder: {full_folder_path.absolute()}")
        return results
        
    except Exception as e:
        print(f"Error creating Drive sync files: {str(e)}")
        return {}

async def process_with_anthropic(prompt: str, model: str = "claude-sonnet-4-20250514", prompt_name: str = "unknown", output_folder: Optional[Path] = None) -> str:
    """Process prompt with Anthropic Claude API and optionally save response"""
    try:
        response = client.messages.create(
            model=model,
            max_tokens=4000,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = response.content[0].text
        
        # Save Claude's response if output folder is provided
        if output_folder and prompt_name:
            try:
                response_file = output_folder / f"Claude Response - {prompt_name}.txt"
                with open(response_file, 'w', encoding='utf-8') as f:
                    f.write(f"=== CLAUDE RESPONSE FOR {prompt_name.upper()} ===\n\n")
                    f.write(f"Model: {model}\n")
                    f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Response length: {len(response_text)} characters\n\n")
                    f.write("=== FULL RESPONSE ===\n\n")
                    f.write(response_text)
                    f.write("\n\n=== END RESPONSE ===\n")
                print(f"Saved Claude response to: {response_file}")
            except Exception as save_error:
                print(f"Warning: Failed to save Claude response: {save_error}")
        
        return response_text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Anthropic API error: {str(e)}")

def generate_prompts(
    prompts_config: dict,
    motivation_notes: str,
    job_description: str,
    resume_reference: str,
    additional_details: str = "",
    cover_letter_base: str = "",
    template_content: str = "",
    use_template_system: bool = False,
    resume_type: str = ""
) -> list[str]:
    """
    Generate all prompts with placeholders for the resume generation process.
    
    Args:
        prompts_config: Dictionary containing prompt templates
        motivation_notes: User's motivation notes
        job_description: The job description to target
        resume_reference: The resume baseline content
        additional_details: Additional context or requirements for the application
        cover_letter_base: Optional base content for the cover letter
        template_content: Template with tags (for 2-document system)
        use_template_system: Whether to use 2-document template system
        
    Returns:
        List of formatted prompt strings with placeholders
    """
    print(f"DEBUG: motivation_notes: {motivation_notes[:100]}...")
    print(f"DEBUG: job_description length: {len(job_description)}")
    print(f"DEBUG: use_template_system parameter: {use_template_system}")
    print(f"DEBUG: template_content length: {len(template_content) if template_content else 'None'}")
    print(f"DEBUG: prompts_config has prompt_1_template: {'prompt_1_template' in prompts_config}")
    
    if use_template_system:
        # For 2-document system, use the template-specific prompt
        try:
            formatted_prompt_1 = prompts_config.get('prompt_1_template', '').format(
                resume_base=resume_reference,
                job_description=job_description,
                additional_details=additional_details,
                resume_type=resume_type
            )
            print("✅ Using template-specific prompt_1_template for 2-document system")
        except Exception as e:
            print(f"❌ Error formatting template prompt: {str(e)}")
            print("Falling back to standard prompt")
            formatted_prompt_1 = prompts_config.get('prompt_1', '').format(
                resume_base=resume_reference,
                job_description=job_description,
                additional_details=additional_details
            )
    else:
        # Original system
        formatted_prompt_1 = prompts_config.get('prompt_1', '').format(
            resume_base=resume_reference,
            job_description=job_description,
            additional_details=additional_details
        )
        print("Using standard prompt_1 for original system")
    
    print(f"DEBUG: Formatted prompt_1 length: {len(formatted_prompt_1)} characters")
    print(f"DEBUG: Last 500 chars of prompt_1: ...{formatted_prompt_1[-500:]}")
    
    # Check if resume_reference actually made it into the formatted prompt
    if resume_reference and resume_reference in formatted_prompt_1:
        print("✅ Resume reference found in formatted prompt")
    else:
        print("❌ Resume reference NOT found in formatted prompt")
        print(f"DEBUG: Resume reference starts with: '{resume_reference[:50]}'" if resume_reference else "DEBUG: resume_reference is empty/None")
    
    return [
        formatted_prompt_1,
        prompts_config.get('prompt_2', '').format(
            resume_from_prompt_1='[RESUME_FROM_PROMPT_1]',
            job_description=job_description,
            additional_details=additional_details
        ),
        prompts_config.get('prompt_3', '').format(
            job_description=job_description,
            motivation_notes=motivation_notes,
            resume_from_prompt_2='[RESUME_FROM_PROMPT_2]',
            cover_letter_base=cover_letter_base if cover_letter_base else "No cover letter template provided.",
            additional_details=additional_details
        ),
        prompts_config.get('prompt_4', '').format(
            job_description=job_description,
            resume_from_prompt_2='[RESUME_FROM_PROMPT_2]',
            motivation_notes=motivation_notes,
            additional_details=additional_details
        )
    ]

# Removed all progress tracking endpoints - keeping it simple

@app.post("/api/generate-resume", response_model=ResumeResponse)
async def generate_resume(request: ResumeRequest):
    """Generate resume, cover letter, and interview prep"""
    global drive_manager
    
    # Removed progress tracking
    
    # Use manual job description if provided, otherwise scrape from URL
    if request.job_description and request.job_description.strip():
        print(f"Using manual job description ({len(request.job_description)} chars)")
        job_description = request.job_description.strip()
        raw_html = ""  # No HTML content from manual input
    else:
        if not request.job_url:
            raise HTTPException(status_code=400, detail="Either job_url or job_description must be provided")
        # Scrape job content (both raw HTML and cleaned text)
        raw_html, job_description = scrape_job_content(request.job_url)
    
    # Fallback: If job description is still empty, create a basic one using available info
    if not job_description or len(job_description.strip()) < 50:
        print(f"⚠️  Job description too short ({len(job_description)} chars), creating fallback")
        company_name = request.company_name or "the company"
        position_title = request.position_title or "this engineering role"
        
        job_description = f"""
Job Title: {position_title}
Company: {company_name}

We are seeking a qualified {position_title} to join our team at {company_name}. 

Key Responsibilities:
- Lead engineering teams and drive technical excellence
- Collaborate with cross-functional teams on product development
- Mentor team members and contribute to technical strategy
- Ensure delivery of high-quality software solutions

Requirements:
- Proven experience in engineering leadership
- Strong technical background and communication skills
- Experience with modern software development practices

This is an excellent opportunity to make a significant impact at {company_name}.
"""
        print(f"✅ Created fallback job description ({len(job_description)} chars)")
    
    # Removed progress tracking
    # Parse job information from raw HTML for better company/position detection (only if we have HTML)
    if raw_html:
        job_info = JobParser.parse_job_posting(raw_html, request.job_url)
        
        # Use parsed job info to enhance request data if not provided
        if not request.company_name and job_info.get('company_name'):
            request.company_name = job_info['company_name']
        if not request.position_title and job_info.get('position_title'):
            request.position_title = job_info['position_title']
    else:
        # For manual job descriptions, try to parse from the text itself
        job_info = JobParser.parse_job_posting(job_description, "")
        
        # Use parsed job info to enhance request data if not provided
        if not request.company_name and job_info.get('company_name'):
            request.company_name = job_info['company_name']
        if not request.position_title and job_info.get('position_title'):
            request.position_title = job_info['position_title']
    
    print(f"Job parsing results: Company='{request.company_name}', Position='{request.position_title}'")
    
    # Check for duplicate resume if prevention is enabled
    if request.prevent_duplicate_resumes and request.company_name and request.position_title:
        try:
            resume_tracker = create_resume_tracker(config.config)
            if resume_tracker:
                is_duplicate = resume_tracker.check_duplicate_resume(
                    company=request.company_name,
                    role=request.position_title,
                    application_page=request.job_url
                )
                
                if is_duplicate:
                    print(f"Duplicate resume detected: {request.company_name} - {request.position_title}")
                    
                    return ResumeResponse(
                        resume_text="",
                        cover_letter="",
                        interview_prep="",
                        success=False,
                        message=f"Resume already exists for {request.company_name} - {request.position_title}. Not rebuilt to avoid duplicates.",
                        drive_results={"duplicate_detected": True}
                    )
        except Exception as e:
            print(f"Error checking for duplicates: {str(e)}")
            # Continue with generation if duplicate check fails
    
    # Get resume template from Google Drive sync folder (local files)
    resume_reference = ""
    cover_letter_base = ""
    
    file_config = config.get('file_organization', {})
    drive_root = file_config.get('drive_for_mac_root', '')
    
    if not drive_root:
        raise HTTPException(status_code=500, detail="Google Drive for Mac root path not configured")
    
    # Cross-reference resume_template to get baseline_resume_name
    baseline_resume_mapping = config.get_baseline_resume_mapping()
    baseline_resume_name = baseline_resume_mapping.get(request.resume_template)
    
    if not baseline_resume_name:
        raise HTTPException(status_code=400, detail=f"Unknown resume template: {request.resume_template}")
    
    # Load both template and baseline files using new 2-document system
    templates_folder = Path(drive_root) / "resume-automation-system" / "templates"
    template_file, baseline_file = find_template_and_baseline_files(templates_folder, baseline_resume_name)
    
    resume_reference = ""
    template_content = ""
    use_template_system = False
    
    if template_file and baseline_file:
        # New 2-document system: we have both template and baseline
        try:
            # Load baseline content (now prefers .docx over .gdoc)
            resume_reference = read_content_file(baseline_file)
            print(f"Successfully loaded baseline content '{baseline_resume_name}' from {baseline_file.suffix} file: {len(resume_reference)} characters")
            
            # Load template content
            template_content = read_content_file(template_file)
            print(f"Successfully loaded template '{baseline_resume_name} Template' from {template_file.suffix} file: {len(template_content)} characters")
            
            use_template_system = True
            print(f"Using 2-document template system for '{baseline_resume_name}'")
            print(f"Baseline preview: {resume_reference[:200]}...")
            print(f"Template preview: {template_content[:200]}...")
            
        except Exception as e:
            print(f"❌ ERROR: Failed to read template system files: {str(e)}")
            print(f"Falling back to old system")
            use_template_system = False
            # Still try to load baseline for fallback
            if baseline_file:
                try:
                    resume_reference = read_content_file(baseline_file)
                    print(f"Successfully loaded baseline in fallback mode: {len(resume_reference)} characters")
                except Exception as fallback_error:
                    print(f"❌ Even fallback failed: {str(fallback_error)}")
                    raise HTTPException(status_code=500, detail=f"Failed to read baseline resume: {str(fallback_error)}")
    
    elif baseline_file:
        # Fallback to old system: only baseline file exists
        try:
            resume_reference = read_content_file(baseline_file)
            print(f"Successfully loaded baseline resume '{baseline_resume_name}' from {baseline_file.suffix} file (fallback mode): {len(resume_reference)} characters")
            print(f"Baseline resume preview: {resume_reference[:200]}...")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to read baseline resume '{baseline_resume_name}' from {baseline_file}: {str(e)}")
    
    elif not template_file and not baseline_file:
        # Neither found - error
        available_files = list(templates_folder.glob("*")) if templates_folder.exists() else []
        raise HTTPException(status_code=500, detail=f"No template or baseline files found for '{baseline_resume_name}' in {templates_folder}. Available files: {[f.name for f in available_files]}")
    
    # Ensure we have content
    if not resume_reference:
        raise HTTPException(status_code=500, detail=f"No resume content loaded for '{baseline_resume_name}'")
    
    # Load cover letter template from sync folder
    potential_cover_letter_files = [
        templates_folder / "Cover Letter Template.docx",
        templates_folder / "Cover Letter Template.txt",
        templates_folder / "Cover Letter Template"
    ]
    
    cover_letter_file = None
    for potential_file in potential_cover_letter_files:
        if potential_file.exists():
            cover_letter_file = potential_file
            break
    
    if cover_letter_file:
        try:
            # Check file extension to determine how to read it
            if cover_letter_file.suffix.lower() == '.docx':
                cover_letter_base = read_docx_content(cover_letter_file)
                print(f"Successfully loaded cover letter template from .docx file: {len(cover_letter_base)} characters")
            else:
                # Read as plain text
                with open(cover_letter_file, 'r', encoding='utf-8') as f:
                    cover_letter_base = f.read()
                print(f"Successfully loaded cover letter template from text file: {len(cover_letter_base)} characters")
            
            print(f"Cover letter template preview: {cover_letter_base[:200]}...")
        except Exception as e:
            print(f"Warning: Failed to read cover letter template from {cover_letter_file}: {str(e)}")
    else:
        print(f"Warning: Cover letter template not found in {templates_folder}")
    
    # Get prompts from configuration
    prompts_config = config.get_prompts()
    
    # Format prompts with variables
    print(f"DEBUG: resume_reference length: {len(resume_reference)} characters")
    print(f"DEBUG: resume_reference preview: {resume_reference[:100]}...")
    print(f"DEBUG: resume_reference type: {type(resume_reference)}")
    # Generate all prompts with placeholders
    prompts = generate_prompts(
        prompts_config=prompts_config,
        motivation_notes=request.motivation_notes,
        job_description=job_description,
        resume_reference=resume_reference,
        additional_details=request.additional_details,
        cover_letter_base=cover_letter_base,
        template_content=template_content,
        use_template_system=use_template_system,
        resume_type=baseline_resume_name
    )
    
    # Process prompts in sequence - simplified approach
    prompt_results = {}  # Store results by prompt number
    prompt_full_results = {}  # Store full Claude responses for template processing
    claude_responses_folder = None  # Track where Claude responses were saved
    enabled_prompts_dict = {
        1: request.enabled_prompts.prompt_1,
        2: request.enabled_prompts.prompt_2,
        3: request.enabled_prompts.prompt_3,
        4: request.enabled_prompts.prompt_4
    }
    
    try:
        for i, prompt in enumerate(prompts, 1):
            # Skip disabled prompts
            if not enabled_prompts_dict.get(i, True):
                print(f"Skipping prompt {i} - disabled by user settings")
                if i == 1:
                    prompt_results[1] = "Resume generation disabled"
                elif i == 2:
                    prompt_results[2] = prompt_results.get(1, "Resume refinement disabled")
                elif i == 3:
                    prompt_results[3] = "Cover letter generation disabled"
                elif i == 4:
                    prompt_results[4] = "Interview prep disabled"
                continue
            
            # Skip steps 2 and 4 for template system ONLY if user didn't explicitly enable them
            if use_template_system and (i == 2 or i == 4) and not enabled_prompts_dict.get(i, False):
                print(f"Skipping prompt {i} for template system (user didn't enable)")
                if i == 2:
                    prompt_results[2] = prompt_results.get(1, "Resume refinement skipped")
                else:  # i == 4
                    prompt_results[4] = "Interview prep skipped for template system"
                continue
            
            # If user enabled prompts 2 or 4 with template system, run them
            if use_template_system and (i == 2 or i == 4) and enabled_prompts_dict.get(i, False):
                print(f"Running prompt {i} for template system (user explicitly enabled)")
            
            # Replace placeholders with previous results
            if i > 1 and 1 in prompt_results:
                prompt = prompt.replace("[RESUME_FROM_PROMPT_1]", prompt_results[1])
            if i > 2 and 2 in prompt_results:
                prompt = prompt.replace("[RESUME_FROM_PROMPT_2]", prompt_results[2])
        
            # Log when we're sending the prompt to Anthropic
            from datetime import datetime
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"{timestamp} - Sending prompt {i} to Anthropic (length: {len(prompt)} characters)")
        
            # Create output folder for this specific job application to store Claude responses
            # Prioritize request parameters to ensure consistency with drive sync files
            company_name = request.company_name or job_info.get('company_name', 'Unknown Company')
            position_title = request.position_title or job_info.get('position_title', 'Unknown Position')
            output_folder = None
        
            # Always try to create an output folder for Claude responses
            try:
                file_config = config.get_file_organization_config()
                drive_root = file_config.get('drive_for_mac_root', '')
                
                if drive_root and Path(drive_root).exists():
                    # Use configured Google Drive sync path if available
                    folder_structure = file_config.get('folder_structure', 'resume-automation-system/ready-for-review/{company_name} - {position_title}/')
                    relative_folder = folder_structure.format(
                        company_name=company_name.replace('/', '-').replace('\\', '-'),  # Clean folder name
                        position_title=position_title.replace('/', '-').replace('\\', '-')
                    )
                    output_folder = Path(drive_root) / relative_folder
                else:
                    # Fallback to temporary folder in project directory for Claude responses
                    import tempfile
                    temp_dir = Path(tempfile.gettempdir()) / "resume-automation-claude-responses"
                    safe_company = company_name.replace('/', '-').replace('\\', '-') if company_name else "Unknown"
                    safe_position = position_title.replace('/', '-').replace('\\', '-') if position_title else "Unknown"
                    output_folder = temp_dir / f"{safe_company} - {safe_position}"
                    print(f"Using temporary folder for Claude responses: {output_folder}")
                
                output_folder.mkdir(parents=True, exist_ok=True)
                claude_responses_folder = output_folder  # Track the folder for response data
                print(f"Created Claude response folder: {output_folder}")
                
            except Exception as folder_error:
                print(f"Warning: Could not create output folder for Claude responses: {folder_error}")
                # Continue without saving Claude responses if folder creation fails
        
            # Define prompt names for clarity
            prompt_names = ["Prompt 1 - Resume Optimization", "Prompt 2 - Resume Refinement", "Prompt 3 - Cover Letter", "Prompt 4 - Interview Prep"]
            prompt_name = prompt_names[i-1] if i <= len(prompt_names) else f"Prompt {i}"
        
            result = await process_with_anthropic(prompt, request.claude_model, prompt_name, output_folder)
        
            print(f"DEBUG: Prompt {i} result length: {len(result)}")
            print(f"DEBUG: Prompt {i} result preview: {repr(result[:200])}")
        
            # Store full result for template processing
            prompt_full_results[i] = result
        
            # Extract just the content part for processing while keeping full response in Claude Response files
            if i in [1, 2]:  # Resume prompts - extract content after reasoning
                content_start = result.find("Jerry Mindek\n614-560-5114")
                if content_start != -1:
                    extracted_result = result[content_start:]
                    print(f"DEBUG: Found 'Jerry Mindek' in Prompt {i} at position {content_start}")
                else:
                    # Fallback: look for any content that starts with Jerry Mindek
                    fallback_start = result.find("Jerry Mindek")
                    if fallback_start != -1:
                        extracted_result = result[fallback_start:]
                        print(f"DEBUG: Found 'Jerry Mindek' fallback in Prompt {i} at position {fallback_start}")
                    else:
                        extracted_result = result
                        print(f"DEBUG: No 'Jerry Mindek' found in Prompt {i}, using full result")
                prompt_results[i] = extracted_result
                print(f"DEBUG: Stored Prompt {i} result: {repr(extracted_result[:100])}")
            elif i == 3:  # Cover letter prompt - extract cover letter content from template tags
                # Look for both single and double brace formats
                template_start = result.find("{company}")
                if template_start == -1:
                    template_start = result.find("{{company}}")
                
                if template_start != -1:
                    extracted_result = result[template_start:]
                    print(f"DEBUG: Found template tags in Prompt 3 at position {template_start}")
                    
                    # Look for content section in both formats
                    content_marker = "{content}\n"
                    if content_marker not in extracted_result:
                        content_marker = "{{content}}\n"
                    
                    content_start = extracted_result.find(content_marker)
                    if content_start != -1:
                        content_start += len(content_marker)
                        content_end = extracted_result.find("\n\nJerry Mindek")
                        if content_end == -1:
                            content_end = extracted_result.find("\nJerry Mindek")
                        if content_end == -1:
                            # Look for signature at end
                            content_end = len(extracted_result)
                        else:
                            content_end += len("\n\nJerry Mindek")
                            
                        # Extract just the cover letter content for display
                        cover_letter_content = extracted_result[content_start:content_end].strip()
                        print(f"DEBUG: Extracted cover letter content: {repr(cover_letter_content[:100])}")
                        prompt_results[i] = cover_letter_content
                    else:
                        # Fallback to the full template tags
                        prompt_results[i] = extracted_result
                        print(f"DEBUG: Using full template result as fallback")
                else:
                    extracted_result = result  # Use full result if template tags not found
                    print(f"DEBUG: No template tags found in Prompt 3, using full result")
                    prompt_results[i] = extracted_result
                print(f"DEBUG: Stored Prompt 3 result: {repr(prompt_results[i][:100])}")
            else:  # Interview prep - extract structured content after strategy analysis
                company_start = result.find("COMPANY:")
                if company_start != -1:
                    # Extract structured content starting from COMPANY:
                    structured_content = result[company_start:]
                    print(f"DEBUG: Found structured interview prep content at position {company_start}")
                    prompt_results[i] = structured_content
                else:
                    # Fallback to full result if structured format not found
                    prompt_results[i] = result
                    print(f"DEBUG: No structured format found in Interview prep, using full result")
                print(f"DEBUG: Stored Prompt {i} result: {repr(prompt_results[i][:100])}")
    
    except Exception as e:
        print(f"Error during prompt processing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Resume generation failed: {str(e)}")
    
    # Prepare response data - simple approach using prompt results dictionary
    print(f"DEBUG: Prompt results keys: {list(prompt_results.keys())}")
    for key, value in prompt_results.items():
        print(f"DEBUG: prompt_results[{key}] = {repr(value[:50])}..." if len(value) > 50 else f"DEBUG: prompt_results[{key}] = {repr(value)}")
    
    # Use prompt 2 if available, otherwise prompt 1 for resume
    resume_text = prompt_results.get(2, prompt_results.get(1, "Resume generation failed"))
    cover_letter = prompt_results.get(3, "Cover letter generation failed")
    interview_prep = prompt_results.get(4, "Interview prep skipped")
    
    response_data = {
        "resume_text": resume_text,
        "cover_letter": cover_letter,
        "interview_prep": interview_prep,
        "success": True,
        "message": "Resume package generated successfully"
    }
    
    # Add Claude responses folder info if available
    if claude_responses_folder:
        response_data["claude_responses_folder"] = str(claude_responses_folder)
        response_data["message"] += f" | Claude responses saved to: {claude_responses_folder.name}"
    
    # Level 2: Google Drive Integration - Create files in Drive sync folder
    if request.use_drive_integration and request.company_name and request.position_title:
        try:
            # Create files in Google Drive sync folder
            sync_results = create_drive_sync_files(
                company_name=request.company_name,
                position_title=request.position_title,
                resume_template=request.resume_template,
                resume_content=resume_text,
                cover_letter_content=cover_letter,
                interview_prep_content=interview_prep,
                use_template_system=use_template_system,
                template_file=template_file if use_template_system else None,
                prompt_full_results=prompt_full_results
            )
            
            if sync_results:
                response_data["drive_results"] = sync_results
                response_data["message"] += " | Files created in Google Drive sync folder"
            else:
                response_data["message"] += " | Warning: Drive sync file creation failed"
                
        except Exception as e:
            response_data["message"] += f" | Drive sync error: {str(e)}"
    
    # Excel Resume Tracking - Add application record to tracking spreadsheet
    if request.enable_resume_tracking and request.company_name and request.position_title:
        try:
            # Create resume tracker from config
            resume_tracker = create_resume_tracker(config.config)
            
            if resume_tracker:
                # Extract department from job description if possible
                department = ""  # Could extract from job description in future
                
                # Extract salary from job info if available
                salary_info = job_info.get('salary', '') or ''
                
                # Add record to tracking spreadsheet
                tracking_success = resume_tracker.add_application_record(
                    company=request.company_name,
                    department=department,
                    role=request.position_title,
                    salary=salary_info,
                    application_date=None,  # Uses current date
                    application_page=request.job_url  # Job description URL
                )
                
                if tracking_success:
                    response_data["message"] += " | Application logged to tracking spreadsheet"
                else:
                    response_data["message"] += " | Warning: Excel tracking failed"
            else:
                response_data["message"] += " | Warning: Excel tracking disabled in config"
                
        except Exception as e:
            print(f"Excel tracking error: {str(e)}")
            response_data["message"] += f" | Excel tracking error: {str(e)}"
    
    # Removed progress tracking
    return ResumeResponse(**response_data)


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
        
        # Create user-friendly display names for UI
        template_display_names = {
            'senior_engineering_manager': 'Senior Engineering Manager',
            'engineering_manager': 'Engineering Manager', 
            'director': 'Director of Engineering',
            'data_engineering_manager': 'Data Engineering Manager',
            'senior_software_engineer': 'Senior Software Engineer',
            'software_engineer': 'Software Engineer',
            'lead_data_engineer': 'Lead Data Engineer',
            'data_engineer': 'Data Engineer'
        }
        
        # Remove sensitive information
        safe_config = {
            "templates_folder_configured": bool(drive_config.get('templates_folder_id')),
            "output_folder_configured": bool(drive_config.get('output_folder_id')),
            "service_account_configured": bool(drive_config.get('service_account_file')),
            "baseline_resumes": drive_config.get('baseline_resumes', {}),
            "templates": template_display_names,  # Use display names for UI
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
            # Get raw HTML content for better parsing (don't strip HTML tags)
            try:
                response = requests.get(job_url, headers={'User-Agent': 'Mozilla/5.0'})
                job_description = response.text  # Keep raw HTML for title tag parsing
            except Exception as e:
                return {
                    "success": False,
                    "company_name": "",
                    "position_title": "",
                    "confidence": "low",
                    "message": f"Failed to fetch job page: {str(e)}"
                }
        
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
            parsed_info = JobParser.parse_job_posting(job_description, job_url)
            # Apply default template if no template was detected
            if not parsed_info.get('suggested_template') and default_template:
                parsed_info['suggested_template'] = default_template
                parsed_info['template_source'] = 'default'
        
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