// Resume Automation Frontend
class ResumeAutomation {
    constructor() {
        this.form = document.getElementById('resumeForm');
        this.generateBtn = document.getElementById('generateBtn');
        this.loading = document.getElementById('loading');
        this.error = document.getElementById('error');
        this.results = document.getElementById('results');
        
        this.init();
    }
    
    init() {
        this.form.addEventListener('submit', this.handleSubmit.bind(this));
    }
    
    async handleSubmit(event) {
        event.preventDefault();
        
        const formData = new FormData(this.form);
        const requestData = {
            job_url: document.getElementById('jobUrl').value,
            motivation_notes: document.getElementById('motivationNotes').value,
            resume_template: document.getElementById('resumeTemplate').value,
            base_resume: document.getElementById('baseResume').value
        };
        
        // Validate inputs
        if (!this.validateInputs(requestData)) {
            return;
        }
        
        this.showLoading(true);
        this.hideError();
        this.hideResults();
        
        try {
            const response = await fetch('/api/generate-resume', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            this.displayResults(result);
            
        } catch (error) {
            console.error('Error:', error);
            this.showError(`Failed to generate resume: ${error.message}`);
        } finally {
            this.showLoading(false);
        }
    }
    
    validateInputs(data) {
        if (!data.job_url || !data.motivation_notes) {
            this.showError('Please fill in job URL and motivation notes.');
            return false;
        }
        
        // If no base resume provided, template is required
        if (!data.base_resume?.trim() && !data.resume_template) {
            this.showError('Please either provide your resume or select a template.');
            return false;
        }
        
        // Basic URL validation
        try {
            new URL(data.job_url);
        } catch {
            this.showError('Please enter a valid URL for the job description.');
            return false;
        }
        
        return true;
    }
    
    showLoading(show) {
        this.loading.style.display = show ? 'block' : 'none';
        this.generateBtn.disabled = show;
        this.generateBtn.textContent = show ? 'Generating...' : 'Generate Resume Package';
    }
    
    showError(message) {
        this.error.textContent = message;
        this.error.style.display = 'block';
    }
    
    hideError() {
        this.error.style.display = 'none';
    }
    
    hideResults() {
        this.results.style.display = 'none';
    }
    
    displayResults(data) {
        document.getElementById('resumeContent').textContent = data.resume_text;
        document.getElementById('coverLetterContent').textContent = data.cover_letter;
        document.getElementById('interviewPrepContent').textContent = data.interview_prep;
        
        this.results.style.display = 'block';
        
        // Scroll to results
        this.results.scrollIntoView({ behavior: 'smooth' });
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ResumeAutomation();
});