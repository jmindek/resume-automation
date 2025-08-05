from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import anthropic
from typing import List

load_dotenv()

app = FastAPI(title="Resume Automation API")

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

# Configure Anthropic
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

class ResumeRequest(BaseModel):
    job_url: str
    motivation_notes: str
    resume_template: str
    base_resume: str = ""  # Optional field for user's existing resume

class ResumeResponse(BaseModel):
    resume_text: str
    cover_letter: str
    interview_prep: str

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
    
    # Scrape job description
    job_description = scrape_job_description(request.job_url)
    
    # Get base template
    base_template = get_base_resume_template(request.resume_template)
    
    # Use base resume if provided, otherwise use template
    resume_base = request.base_resume if request.base_resume.strip() else base_template
    
    # Your 4 specific prompts
    prompts = [
        f"""You are an elite professional resume writer. 
Please align my resume with this specific job description using Problem-Solution-Impact bullet format. 

### Focus on
1. JD analysis: Extract key requirements and align my experience 
2. Content prioritization: Reorder/reframe achievements for maximum relevance
3. Skills/tech stack alignment: Match their likely technology needs
4. Quantified impact: Emphasize metrics that matter to this role
5. Remove/add content as needed for direct relevance

### Additional details:
 - Sure is P&C insurance not health related, not fintech.
 - Root is auto insurance not health related, not fintech.
 - Enlace is insuretech, healthcare related.
 - Manta.com is an enhanced online SMB directory who's mission was enhance SMBs online presence for customer acquistion and improved sales
 - I do not have Databricks, dbt, Snowflake experience. I am working on certifications for each.

### Constraints: 
1. Don't add facts.
2. Ask clarifying questions about experience details as needed.

### Format:
1. Do not boldface text in skills or role descriptions.
2. Do not explicitly include the text Problem, Solution, Impact in the bullets.

### Sections to include:
Leadership Philosophy (servant)
Key Achievements
Skills
Professional Experience
Education only if required by the job description

### Specific details for this resume
 - {request.motivation_notes}

Resume: {resume_base}
JD: {job_description}""",
        
        f"""Take this tailored resume to a 10/10 recruiter pick likelihood by:

1. Length optimization: Remove low-impact content.
2. Mission alignment: Add language showing I understand their mission/values.
3. Leadership differentiation: Highlight unique leadership approach.
4. Format optimization with smart brevity descriptions.
5. Industry-specific language: Use terminology that resonates with their domain.

Focus on what makes me uniquely qualified vs just qualified.

Resume to optimize: [RESUME_FROM_PROMPT_1]
Job Description: {job_description}
Motivation Notes: {request.motivation_notes}""",
        
        f"""Write a compelling 200-250 word, 3-5 paragraph cover letter that:
1. Opens with mission alignment and genuine interest
2. Highlights 2-3 most relevant achievements with specific metrics
3. Shows cultural/leadership fit with concrete examples
4. Closes with enthusiasm and availability
5. Maintains authentic tone without overstating expertise
6. I am available immediately

Job Description: {job_description}
Motivation Notes: {request.motivation_notes}
Optimized Resume: [RESUME_FROM_PROMPT_2]""",
        
        f"""Based on this tailored resume and JD analysis, provide my strategic interview positioning:

1. **Core narrative**: What's my 2-3 sentence positioning statement that differentiates me?

2. **Key proof points**: Which 3-4 achievements/stories should I lead with that directly address their biggest pain points?

3. **Potential concerns**: What gaps or weaknesses might they probe, and how should I address them?

4. **Cultural alignment**: How do I demonstrate mission fit and values alignment beyond just technical skills?

5. **Strategic questions**: What 3-5 thoughtful questions should I ask that show deep understanding of their challenges?

6. **Closing positioning**: How do I summarize why I'm uniquely qualified vs other candidates?

Focus on making me the obvious choice by connecting my specific experience to their specific needs.

Job Description: {job_description}
Final Resume: [RESUME_FROM_PROMPT_2]
Motivation Notes: {request.motivation_notes}"""
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
    
    return ResumeResponse(
        resume_text=results[1],  # Resume from prompt 2
        cover_letter=results[2],  # Cover letter from prompt 3
        interview_prep=results[3]  # Interview prep from prompt 4
    )

@app.get("/")
async def root():
    """Serve the frontend"""
    return {"message": "Resume Automation API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)