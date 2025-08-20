// Resume Automation Frontend - Level 2
class ResumeAutomation {
    constructor() {
        this.form = document.getElementById('resumeForm');
        this.generateBtn = document.getElementById('generateBtn');
        this.loading = document.getElementById('loading');
        this.error = document.getElementById('error');
        this.results = document.getElementById('results');
        this.useDriveIntegration = document.getElementById('useDriveIntegration');
        this.driveOptions = document.getElementById('driveOptions');
        this.driveResults = document.getElementById('driveResults');
        this.jobUrlInput = document.getElementById('jobUrl');
        this.jobDescriptionInput = document.getElementById('jobDescription');
        this.companyNameInput = document.getElementById('companyName');
        this.positionTitleInput = document.getElementById('positionTitle');
        this.autoDetectionStatus = document.getElementById('autoDetectionStatus');
        this.resumeTemplateSelect = document.getElementById('resumeTemplate');
        
        // Settings panel elements
        this.settingsBtn = document.getElementById('settingsBtn');
        this.settingsPanel = document.getElementById('settingsPanel');
        this.settingsOverlay = document.getElementById('settingsOverlay');
        this.settingsClose = document.getElementById('settingsClose');
        this.claudeModelSelect = document.getElementById('claudeModel');
        
        // Prompt control elements
        this.enablePrompt1 = document.getElementById('enablePrompt1');
        this.enablePrompt2 = document.getElementById('enablePrompt2');
        this.enablePrompt3 = document.getElementById('enablePrompt3');
        this.enablePrompt4 = document.getElementById('enablePrompt4');
        
        // Resume tracking elements
        this.enableResumeTracking = document.getElementById('enableResumeTracking');
        this.preventDuplicateResumes = document.getElementById('preventDuplicateResumes');
        
        // Removed all status tracker elements
        
        this.init();
    }
    
    showToast(message, type = 'info', duration = 5000) {
        // Create toast element
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        
        // Add to page
        document.body.appendChild(toast);
        
        // Show toast with animation
        setTimeout(() => toast.classList.add('show'), 100);
        
        // Remove toast after duration
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => document.body.removeChild(toast), 300);
        }, duration);
    }
    
    // Removed status tracker initialization
    
    // Removed status tracker updates
    
    // Removed status tracker hiding
    
    // Removed progress simulation
    
    // Removed task completion marking
    
    // Removed error task marking
    
    // Removed complex progress session creation
    
    // Removed complex progress listener
    
    // Removed complex progress listener
    
    init() {
        this.form.addEventListener('submit', this.handleSubmit.bind(this));
        this.useDriveIntegration.addEventListener('change', this.toggleDriveOptions.bind(this));
        
        // Settings panel event listeners
        this.settingsBtn.addEventListener('click', this.openSettings.bind(this));
        this.settingsClose.addEventListener('click', this.closeSettings.bind(this));
        this.settingsOverlay.addEventListener('click', this.closeSettings.bind(this));
        this.claudeModelSelect.addEventListener('change', this.saveSettings.bind(this));
        
        // Prompt control event listeners
        this.enablePrompt1.addEventListener('change', this.saveSettings.bind(this));
        this.enablePrompt2.addEventListener('change', this.saveSettings.bind(this));
        this.enablePrompt3.addEventListener('change', this.saveSettings.bind(this));
        this.enablePrompt4.addEventListener('change', this.saveSettings.bind(this));
        
        // Resume tracking event listeners
        this.enableResumeTracking.addEventListener('change', this.saveSettings.bind(this));
        this.preventDuplicateResumes.addEventListener('change', this.saveSettings.bind(this));
        
        // Auto-detect job info when URL changes
        this.jobUrlInput.addEventListener('blur', this.autoDetectJobInfo.bind(this));
        this.jobUrlInput.addEventListener('change', this.autoDetectJobInfo.bind(this));
        
        // Auto-select baseline resume when position title changes manually
        this.positionTitleInput.addEventListener('blur', this.handlePositionTitleChange.bind(this));
        this.positionTitleInput.addEventListener('change', this.handlePositionTitleChange.bind(this));
        
        // Load initial templates and settings
        this.loadTemplateOptions();
        this.loadSettings();
        
        // Show drive options by default since it's checked
        this.toggleDriveOptions();
    }
    
    async handleSubmit(event) {
        event.preventDefault();
        
        const formData = new FormData(this.form);
        const requestData = {
            job_url: document.getElementById('jobUrl').value,
            job_description: document.getElementById('jobDescription').value || "",
            additional_details: document.getElementById('additionalDetails').value || "",
            motivation_notes: document.getElementById('motivationNotes').value || "I am passionate about building scalable systems and leading engineering teams to deliver high-quality software solutions.",
            resume_template: document.getElementById('resumeTemplate').value,
            use_drive_integration: document.getElementById('useDriveIntegration').checked,
            company_name: document.getElementById('companyName').value,
            position_title: document.getElementById('positionTitle').value,
            claude_model: document.getElementById('claudeModel').value,
            // Prompt control settings
            enabled_prompts: {
                prompt_1: this.enablePrompt1.checked,
                prompt_2: this.enablePrompt2.checked,
                prompt_3: this.enablePrompt3.checked,
                prompt_4: this.enablePrompt4.checked
            },
            // Resume tracking settings
            enable_resume_tracking: this.enableResumeTracking.checked,
            prevent_duplicate_resumes: this.preventDuplicateResumes.checked
        };
        
        // Validate inputs
        if (!this.validateInputs(requestData)) {
            return;
        }
        
        this.showLoading(true);
        this.hideError();
        this.hideResults();
        
        // Removed all status tracking
        
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
            
            // Check if this was a duplicate detection
            if (!result.success && result.drive_results?.duplicate_detected) {
                this.showToast(result.message, 'warning', 7000);
                return; // Don't display empty results
            }
            
            // Display results
            this.displayResults(result);
            
        } catch (error) {
            console.error('Error:', error);
            this.showError(`Failed to generate resume: ${error.message}`);
        } finally {
            this.showLoading(false);
        }
    }
    
    validateInputs(data) {
        // Either job URL or job description is required
        if ((!data.job_url && !data.job_description) || !data.motivation_notes) {
            this.showError('Please provide either a job URL or paste the job description, plus motivation notes.');
            return false;
        }
        
        // Resume template should be auto-selected, but use default if not
        if (!data.resume_template) {
            // Auto-select the default template if none is selected
            this.resumeTemplateSelect.value = 'engineering_manager';
            data.resume_template = 'engineering_manager';
        }
        
        // If Drive integration is enabled, company and position are required
        if (data.use_drive_integration && (!data.company_name?.trim() || !data.position_title?.trim())) {
            this.showError('Company name and position title are required for Google Drive integration. Please edit the auto-detected values or enter them manually.');
            return false;
        }
        
        // Basic URL validation (only if job URL is provided)
        if (data.job_url && !data.job_description) {
            try {
                new URL(data.job_url);
            } catch {
                this.showError('Please enter a valid URL for the job description.');
                return false;
            }
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
        
        // Display Google Drive results if available
        if (data.drive_results) {
            this.displayDriveResults(data.drive_results);
            this.driveResults.style.display = 'block';
        } else {
            this.driveResults.style.display = 'none';
        }
        
        this.results.style.display = 'block';
        
        // Scroll to results
        this.results.scrollIntoView({ behavior: 'smooth' });
    }
    
    displayDriveResults(driveResults) {
        const driveLinksContent = document.getElementById('driveLinksContent');
        let html = '<h4>📁 Files Created:</h4><ul style="margin: 10px 0; padding-left: 20px;">';
        
        // Resume files
        if (driveResults.resume_docx_path && driveResults.resume_txt_path) {
            html += `<li><strong>Resume:</strong> ${driveResults.resume_docx_path} (.docx) + ${driveResults.resume_txt_path} (.txt)</li>`;
        } else if (driveResults.resume_path) {
            html += `<li><strong>Resume:</strong> ${driveResults.resume_path}</li>`;
        }
        
        // Cover letter files
        if (driveResults.cover_letter_docx_path && driveResults.cover_letter_txt_path) {
            html += `<li><strong>Cover Letter:</strong> ${driveResults.cover_letter_docx_path} (.docx) + ${driveResults.cover_letter_txt_path} (.txt)</li>`;
        } else if (driveResults.cover_letter_path) {
            html += `<li><strong>Cover Letter:</strong> ${driveResults.cover_letter_path}</li>`;
        }
        
        // Interview prep notes file
        if (driveResults.interview_prep_path) {
            html += `<li><strong>Interview Prep Notes:</strong> ${driveResults.interview_prep_path} (.md)</li>`;
        }
        
        if (driveResults.folder_path) {
            html += `<li><strong>📂 Folder:</strong> ${driveResults.folder_path}</li>`;
        }
        
        html += '</ul>';
        html += '<p style="font-size: 12px; color: #666; margin-top: 10px;">💡 Files sync to Google Drive automatically. Open .docx files in Microsoft Word or Google Docs.</p>';
        
        driveLinksContent.innerHTML = html;
    }
    
    // Settings Panel Methods
    openSettings() {
        this.settingsPanel.classList.add('open');
        this.settingsOverlay.classList.add('show');
        document.body.style.overflow = 'hidden';
    }
    
    closeSettings() {
        this.settingsPanel.classList.remove('open');
        this.settingsOverlay.classList.remove('show');
        document.body.style.overflow = '';
    }
    
    saveSettings() {
        // Save settings to localStorage
        const settings = {
            claudeModel: this.claudeModelSelect.value,
            useDriveIntegration: this.useDriveIntegration.checked,
            enableResumeTracking: this.enableResumeTracking.checked,
            preventDuplicateResumes: this.preventDuplicateResumes.checked,
            enabledPrompts: {
                prompt_1: this.enablePrompt1.checked,
                prompt_2: this.enablePrompt2.checked,
                prompt_3: this.enablePrompt3.checked,
                prompt_4: this.enablePrompt4.checked
            }
        };
        localStorage.setItem('resumeAutomationSettings', JSON.stringify(settings));
        console.log('Settings saved:', settings);
    }
    
    loadSettings() {
        // Load settings from localStorage
        const savedSettings = localStorage.getItem('resumeAutomationSettings');
        if (savedSettings) {
            try {
                const settings = JSON.parse(savedSettings);
                if (settings.claudeModel) {
                    this.claudeModelSelect.value = settings.claudeModel;
                }
                if (typeof settings.useDriveIntegration === 'boolean') {
                    this.useDriveIntegration.checked = settings.useDriveIntegration;
                    this.toggleDriveOptions();
                }
                if (typeof settings.enableResumeTracking === 'boolean') {
                    this.enableResumeTracking.checked = settings.enableResumeTracking;
                }
                if (typeof settings.preventDuplicateResumes === 'boolean') {
                    this.preventDuplicateResumes.checked = settings.preventDuplicateResumes;
                }
                // Load prompt settings
                if (settings.enabledPrompts) {
                    this.enablePrompt1.checked = settings.enabledPrompts.prompt_1 !== false; // Default to true
                    this.enablePrompt2.checked = settings.enabledPrompts.prompt_2 === true;  // Default to false
                    this.enablePrompt3.checked = settings.enabledPrompts.prompt_3 !== false; // Default to true
                    this.enablePrompt4.checked = settings.enabledPrompts.prompt_4 === true;  // Default to false
                }
                console.log('Settings loaded:', settings);
            } catch (e) {
                console.error('Error loading settings:', e);
            }
        }
        
        // Save settings when useDriveIntegration changes
        this.useDriveIntegration.addEventListener('change', this.saveSettings.bind(this));
    }
    
    
    toggleDriveOptions() {
        if (this.useDriveIntegration.checked) {
            this.driveOptions.style.display = 'block';
            // Auto-detect job info when Drive integration is enabled
            if (this.jobUrlInput.value) {
                // Always run auto-detection to ensure template is selected
                this.autoDetectJobInfo();
            }
        } else {
            this.driveOptions.style.display = 'none';
        }
    }
    
    async loadTemplateOptions() {
        try {
            const response = await fetch('/api/config/drive');
            const config = await response.json();
            
            if (config.templates) {
                // Clear existing options except the first one
                this.resumeTemplateSelect.innerHTML = '<option value="">Select a template...</option>';
                
                // Add template options from config
                Object.entries(config.templates).forEach(([key, displayName]) => {
                    const option = document.createElement('option');
                    option.value = key;
                    option.textContent = displayName;
                    this.resumeTemplateSelect.appendChild(option);
                });
            }
            
            // Update folder organization display if available
            if (config.folder_structure) {
                const folderInfo = document.querySelector('#driveOptions small:last-child');
                if (folderInfo) {
                    const displayStructure = config.folder_structure
                        .replace('{company_name}', '[Company]')
                        .replace('{position_title}', '[Position]');
                    folderInfo.innerHTML = `📁 Files will be organized in: ${displayStructure}`;
                }
            }
        } catch (error) {
            console.error('Failed to load template options:', error);
            // Keep default hardcoded options if config loading fails
        }
    }
    
    async autoDetectJobInfo() {
        const jobUrl = this.jobUrlInput.value.trim();
        
        if (!jobUrl) {
            this.clearJobInfo();
            return;
        }
        
        // Only auto-detect if fields are empty (don't override user edits)
        const hasExistingData = this.companyNameInput.value.trim() || this.positionTitleInput.value.trim();
        
        // Show loading status
        this.showAutoDetectionStatus('🔍 Auto-detecting company and position...', 'loading');
        
        try {
            const response = await fetch('/api/parse-job', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ job_url: jobUrl })
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Only fill empty fields or if user hasn't made edits
                if (!this.companyNameInput.value.trim() && result.company_name) {
                    this.companyNameInput.value = result.company_name;
                }
                if (!this.positionTitleInput.value.trim() && result.position_title) {
                    this.positionTitleInput.value = result.position_title;
                }
                
                // Auto-select resume template based on position if suggested
                if (result.suggested_template && (!this.resumeTemplateSelect.value || this.resumeTemplateSelect.value === "")) {
                    this.resumeTemplateSelect.value = result.suggested_template;
                    console.log(`Auto-selected template: ${result.suggested_template} based on position: ${result.position_title}`);
                } else if (!this.resumeTemplateSelect.value || this.resumeTemplateSelect.value === "") {
                    // Fallback to default template if no suggestion and nothing selected
                    this.resumeTemplateSelect.value = 'engineering_manager';
                    console.log('Using default template: engineering_manager');
                }
                
                let statusMsg;
                if (result.company_name || result.position_title) {
                    const detected = [];
                    if (result.company_name) detected.push(`Company: ${result.company_name}`);
                    if (result.position_title) detected.push(`Position: ${result.position_title}`);
                    
                    // Show template selection info
                    if (result.suggested_template) {
                        if (result.template_source === 'auto-detected') {
                            detected.push(`Template: Auto-selected`);
                        } else if (result.template_source === 'default') {
                            detected.push(`Template: Using default (Engineering Manager)`);
                        }
                    }
                    
                    statusMsg = `✅ Auto-detected: ${detected.join(', ')} (${result.confidence} confidence) - Edit as needed`;
                } else {
                    statusMsg = '⚠️ Could not auto-detect company/position from job posting. Using default template. Please edit manually.';
                }
                
                this.showAutoDetectionStatus(statusMsg, result.company_name || result.position_title ? 'success' : 'warning');
                
                // Auto-hide status after 5 seconds if successful
                if (result.company_name || result.position_title) {
                    setTimeout(() => this.hideAutoDetectionStatus(), 5000);
                }
            } else {
                this.showAutoDetectionStatus(`⚠️ Auto-detection incomplete: ${result.message}. Please review and edit.`, 'warning');
            }
        } catch (error) {
            console.error('Auto-detection error:', error);
            // Ensure we have a template selected even if auto-detection fails
            if (!this.resumeTemplateSelect.value || this.resumeTemplateSelect.value === "") {
                this.resumeTemplateSelect.value = 'engineering_manager';
                console.log('Auto-detection failed, using default template: engineering_manager');
            }
            this.showAutoDetectionStatus('❌ Auto-detection failed. Using default template. Please enter company/position manually.', 'error');
        }
    }
    
    clearJobInfo() {
        this.companyNameInput.value = '';
        this.positionTitleInput.value = '';
        this.hideAutoDetectionStatus();
    }
    
    
    showAutoDetectionStatus(message, type) {
        const colors = {
            success: '#d4edda',
            warning: '#fff3cd',
            error: '#f8d7da',
            loading: '#e2e3e5'
        };
        
        this.autoDetectionStatus.textContent = message;
        this.autoDetectionStatus.style.backgroundColor = colors[type] || colors.loading;
        this.autoDetectionStatus.style.display = 'block';
    }
    
    hideAutoDetectionStatus() {
        this.autoDetectionStatus.style.display = 'none';
    }
    
    async handlePositionTitleChange() {
        const positionTitle = this.positionTitleInput.value.trim();
        
        if (!positionTitle) {
            // Clear selection if position title is empty
            this.resumeTemplateSelect.value = "";
            return;
        }
        
        try {
            // Call backend to get template suggestion based on position title
            const response = await fetch('/api/parse-job', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    job_url: '', 
                    position_title: positionTitle 
                })
            });
            
            const result = await response.json();
            
            if (result.success && result.suggested_template) {
                this.resumeTemplateSelect.value = result.suggested_template;
                this.showAutoDetectionStatus(
                    `✅ Auto-selected baseline resume: ${result.suggested_template.replace('_', ' ')} based on position "${positionTitle}"`, 
                    'success'
                );
                
                // Auto-hide status after 3 seconds
                setTimeout(() => this.hideAutoDetectionStatus(), 3000);
                
                console.log(`Auto-selected baseline resume: ${result.suggested_template} for position: ${positionTitle}`);
            } else {
                // Fallback to default
                this.resumeTemplateSelect.value = 'engineering_manager';
                this.showAutoDetectionStatus(
                    `⚠️ Using default baseline resume (Engineering Manager) for position "${positionTitle}"`, 
                    'warning'
                );
                
                setTimeout(() => this.hideAutoDetectionStatus(), 3000);
            }
        } catch (error) {
            console.error('Error auto-selecting baseline resume:', error);
            // Fallback to default on error
            if (!this.resumeTemplateSelect.value || this.resumeTemplateSelect.value === "") {
                this.resumeTemplateSelect.value = 'engineering_manager';
            }
        }
    }
    
    // Remove unused methods
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ResumeAutomation();
});