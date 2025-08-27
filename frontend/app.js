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
        this.resumeTemplateDocxSelect = document.getElementById('resumeTemplateDocx');
        this.overrideResumeInput = document.getElementById('overrideResume');
        this.overrideResumeFile = document.getElementById('overrideResumeFile');
        this.overrideResumeDropArea = document.getElementById('overrideResumeDropArea');
        this.overrideResumeBrowse = document.getElementById('overrideResumeBrowse');
        this.overrideResumeFileName = document.getElementById('overrideResumeFileName');
        this.selectedFile = null;
        
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
    
    // Helper function to keep both template selectors in sync
    setResumeTemplate(templateValue) {
        console.log(`DEBUG: Setting resume template to: "${templateValue}"`);
        this.resumeTemplateSelect.value = templateValue;
        this.resumeTemplateDocxSelect.value = templateValue; // Keep docx selector in sync
        console.log(`DEBUG: Baseline template now: "${this.resumeTemplateSelect.value}"`);
        console.log(`DEBUG: Resume template now: "${this.resumeTemplateDocxSelect.value}"`);
    }
    
    // Handle override resume file upload
    async handleOverrideResumeFile(file) {
        console.log('handleOverrideResumeFile called with:', file);
        if (!file) {
            console.log('No file provided, returning');
            return;
        }
        
        // Show file name
        console.log('Displaying file name:', file.name);
        this.overrideResumeFileName.textContent = `Selected: ${file.name}`;
        this.overrideResumeFileName.style.display = 'block';
        
        try {
            // Store the file for later upload
            this.selectedFile = file;
            
            // Read file content based on type
            let content = '';
            if (file.type === 'text/plain' || file.name.endsWith('.txt')) {
                // Handle text files immediately
                content = await this.readTextFile(file);
                this.overrideResumeInput.value = content;
                this.selectedFile = null; // Clear since we have text content
            } else if (file.name.endsWith('.docx')) {
                // DOCX files will be processed by backend
                this.showToast('DOCX file selected. Content will be extracted automatically during generation.', 'info', 4000);
                this.overrideResumeInput.value = `[DOCX FILE SELECTED: ${file.name}]`;
                this.overrideResumeInput.disabled = true;
            } else if (file.type === 'application/pdf' || file.name.endsWith('.pdf')) {
                // PDF files will be processed by backend
                this.showToast('PDF file selected. Content will be extracted automatically during generation.', 'info', 4000);
                this.overrideResumeInput.value = `[PDF FILE SELECTED: ${file.name}]`;
                this.overrideResumeInput.disabled = true;
            } else {
                this.showToast('Unsupported file format. Please use .txt, .docx, or .pdf files.', 'error', 5000);
                return;
            }
            
        } catch (error) {
            console.error('Error reading file:', error);
            this.showToast('Error reading file. Please try again.', 'error', 5000);
        }
    }
    
    // Helper to read text files
    readTextFile(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = (e) => reject(e);
            reader.readAsText(file);
        });
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
        
        // Resume tracking event listeners
        this.enableResumeTracking.addEventListener('change', this.saveSettings.bind(this));
        this.preventDuplicateResumes.addEventListener('change', this.saveSettings.bind(this));
        
        // Auto-detect job info when URL changes
        this.jobUrlInput.addEventListener('blur', () => {
            console.log('Job URL blur event triggered:', this.jobUrlInput.value);
            this.autoDetectJobInfo();
        });
        this.jobUrlInput.addEventListener('change', () => {
            console.log('Job URL change event triggered:', this.jobUrlInput.value);
            this.autoDetectJobInfo();
        });
        
        // Auto-select baseline resume when position title changes manually
        this.positionTitleInput.addEventListener('blur', this.handlePositionTitleChange.bind(this));
        this.positionTitleInput.addEventListener('change', this.handlePositionTitleChange.bind(this));
        
        // Clear file selection when user types in override resume textarea
        this.overrideResumeInput.addEventListener('input', () => {
            if (this.selectedFile && this.overrideResumeInput.value.trim() && 
                !this.overrideResumeInput.value.includes('[DOCX FILE SELECTED:') && 
                !this.overrideResumeInput.value.includes('[PDF FILE SELECTED:')) {
                this.selectedFile = null;
                this.overrideResumeInput.disabled = false;
                this.overrideResumeFileName.style.display = 'none';
                console.log('Cleared file selection due to manual text input');
            }
        });
        
        // Override resume file upload event listeners
        if (this.overrideResumeBrowse) {
            console.log('Adding click listener to browse button');
            this.overrideResumeBrowse.addEventListener('click', (e) => {
                console.log('Browse button clicked');
                e.preventDefault();
                e.stopPropagation();
                if (this.overrideResumeFile) {
                    console.log('Triggering file input click');
                    this.overrideResumeFile.click();
                } else {
                    console.error('File input element not available when trying to click');
                }
            });
        } else {
            console.error('overrideResumeBrowse element not found!');
        }
        
        if (this.overrideResumeFile) {
            console.log('Adding change listener to file input');
            this.overrideResumeFile.addEventListener('change', (e) => {
                console.log('File input changed:', e.target.files[0]);
                this.handleOverrideResumeFile(e.target.files[0]);
            });
        } else {
            console.error('overrideResumeFile element not found!');
        }
        
        // Drag and drop event listeners
        if (this.overrideResumeDropArea) {
            console.log('Adding drag and drop listeners');
            
            // Add click handler to entire drop area as fallback
            this.overrideResumeDropArea.addEventListener('click', (e) => {
                // Only trigger if clicking on the drop area itself, not child elements
                if (e.target === this.overrideResumeDropArea || e.target.id === 'overrideResumeUploadText') {
                    console.log('Drop area clicked, opening file dialog');
                    if (this.overrideResumeFile) {
                        this.overrideResumeFile.click();
                    }
                }
            });
            
            this.overrideResumeDropArea.addEventListener('dragover', (e) => {
                console.log('Drag over detected');
                e.preventDefault();
                this.overrideResumeDropArea.classList.add('dragover');
            });
            
            this.overrideResumeDropArea.addEventListener('dragleave', (e) => {
                e.preventDefault();
                this.overrideResumeDropArea.classList.remove('dragover');
            });
            
            this.overrideResumeDropArea.addEventListener('drop', (e) => {
                console.log('File drop detected');
                e.preventDefault();
                this.overrideResumeDropArea.classList.remove('dragover');
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    console.log('Dropped file:', files[0].name);
                    this.handleOverrideResumeFile(files[0]);
                }
            });
        } else {
            console.error('overrideResumeDropArea element not found!');
        }
        
        // Load initial templates and settings
        this.loadTemplateOptions();
        this.loadSettings();
        
        // Show drive options by default since it's checked
        this.toggleDriveOptions();
        
        // Debug: Check if elements are found
        console.log('DOM elements check:');
        console.log('jobUrlInput:', this.jobUrlInput);
        console.log('companyNameInput:', this.companyNameInput);
        console.log('positionTitleInput:', this.positionTitleInput);
        console.log('autoDetectionStatus:', this.autoDetectionStatus);
        console.log('overrideResumeFile:', this.overrideResumeFile);
        console.log('overrideResumeDropArea:', this.overrideResumeDropArea);
        console.log('overrideResumeBrowse:', this.overrideResumeBrowse);
        console.log('overrideResumeFileName:', this.overrideResumeFileName);
    }
    
    async handleSubmit(event) {
        event.preventDefault();
        
        // Check if we have a file to upload
        if (this.selectedFile) {
            await this.handleFileUploadSubmit();
        } else {
            await this.handleRegularSubmit();
        }
    }
    
    async handleRegularSubmit() {
        const requestData = {
            job_url: document.getElementById('jobUrl').value,
            job_description: document.getElementById('jobDescription').value || "",
            additional_details: document.getElementById('additionalDetails').value || "",
            motivation_notes: document.getElementById('motivationNotes').value || "I am passionate about building scalable systems and leading engineering teams to deliver high-quality software solutions.",
            resume_template: document.getElementById('resumeTemplate').value,
            resume_template_docx: document.getElementById('resumeTemplateDocx').value,
            override_resume: document.getElementById('overrideResume').value || "",
            use_drive_integration: document.getElementById('useDriveIntegration').checked,
            company_name: document.getElementById('companyName').value,
            position_title: document.getElementById('positionTitle').value,
            claude_model: document.getElementById('claudeModel').value,
            // Prompt control settings
            enabled_prompts: {
                prompt_1: this.enablePrompt1.checked,
                prompt_2: this.enablePrompt2.checked,
                prompt_3: this.enablePrompt3.checked
            },
            // Resume tracking settings
            enable_resume_tracking: this.enableResumeTracking.checked,
            prevent_duplicate_resumes: this.preventDuplicateResumes.checked
        };
        
        // Validate inputs
        if (!this.validateInputs(requestData)) {
            return;
        }
        
        console.log('Resume generation request data:', requestData);
        console.log('=== STARTING RESUME GENERATION REQUEST ===');
        
        this.showLoading(true);
        this.hideError();
        this.hideResults();
        
        try {
            console.log('About to make fetch request to /api/generate-resume');
            const response = await fetch('/api/generate-resume', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });
            
            await this.handleResponse(response);
        } catch (error) {
            this.handleError(error);
        } finally {
            this.showLoading(false);
        }
    }
    
    async handleFileUploadSubmit() {
        const formData = new FormData();
        
        // Add all form fields
        formData.append('job_url', document.getElementById('jobUrl').value);
        formData.append('job_description', document.getElementById('jobDescription').value || "");
        formData.append('additional_details', document.getElementById('additionalDetails').value || "");
        formData.append('motivation_notes', document.getElementById('motivationNotes').value || "I am passionate about building scalable systems and leading engineering teams to deliver high-quality software solutions.");
        formData.append('resume_template', document.getElementById('resumeTemplate').value);
        formData.append('resume_template_docx', document.getElementById('resumeTemplateDocx').value);
        formData.append('use_drive_integration', document.getElementById('useDriveIntegration').checked);
        formData.append('company_name', document.getElementById('companyName').value);
        formData.append('position_title', document.getElementById('positionTitle').value);
        formData.append('claude_model', document.getElementById('claudeModel').value);
        formData.append('enable_resume_tracking', this.enableResumeTracking.checked);
        formData.append('prevent_duplicate_resumes', this.preventDuplicateResumes.checked);
        
        // Add enabled prompts as JSON string
        formData.append('enabled_prompts', JSON.stringify({
            prompt_1: this.enablePrompt1.checked,
            prompt_2: this.enablePrompt2.checked,
            prompt_3: this.enablePrompt3.checked
        }));
        
        // Add the file
        formData.append('override_resume_file', this.selectedFile);
        
        console.log('=== STARTING FILE UPLOAD RESUME GENERATION ===');
        console.log('File:', this.selectedFile.name, this.selectedFile.type);
        
        this.showLoading(true);
        this.hideError();
        this.hideResults();
        
        try {
            console.log('About to make file upload request to /api/generate-resume-upload');
            const response = await fetch('/api/generate-resume-upload', {
                method: 'POST',
                body: formData
            });
            
            await this.handleResponse(response);
        } catch (error) {
            this.handleError(error);
        } finally {
            this.showLoading(false);
        }
    }
    
    async handleResponse(response) {
        if (!response.ok) {
            let errorData;
            const responseText = await response.text();
            console.error('Raw server response:', responseText);
            console.error('Response status:', response.status);
            
            try {
                errorData = JSON.parse(responseText);
                console.error('Parsed error data:', errorData);
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            } catch (jsonError) {
                console.error('Response is not JSON, likely HTML error page');
                throw new Error(`Server error (${response.status}): ${responseText.substring(0, 200)}...`);
            }
        }
        
        const successText = await response.text();
        console.log('Raw success response (first 500 chars):', successText.substring(0, 500));
        console.log('Response content type:', response.headers.get('content-type'));
        
        let result;
        try {
            result = JSON.parse(successText);
            console.log('Successfully parsed JSON response');
        } catch (jsonError) {
            console.error('Success response is not JSON, full response:', successText);
            console.error('JSON parse error:', jsonError.message);
            throw new Error('Server returned invalid response format - check console for full response');
        }
        
        // Check if this was a duplicate detection
        if (!result.success && result.drive_results?.duplicate_detected) {
            this.showToast(result.message, 'warning', 7000);
            return; // Don't display empty results
        }
        
        // Display results
        this.displayResults(result);
    }
    
    handleError(error) {
        console.error('Full error object:', error);
        console.error('Error message:', error.message);
        
        // Check if this is a job scraping failure
        if (error.message.includes('Failed to scrape') || 
            error.message.includes('job scraping failed') || 
            error.message.includes('Job scraping failed') ||
            error.message.includes('Only extracted') ||
            error.message.includes('appears to be too minimal')) {
            
            // Extract the specific reason from the error message
            let reason = 'the website may have anti-scraping protection';
            if (error.message.includes('Single Page Application')) {
                reason = 'this appears to be a Single Page Application that loads content with JavaScript';
            } else if (error.message.includes('appears to be too minimal')) {
                reason = 'the job description appears to be too minimal for proper optimization';
            } else if (error.message.includes('Only extracted')) {
                reason = 'only a small amount of content could be extracted from the page';
            }
            
            // Show user-friendly toast message
            this.showToast(
                `Please paste in the job description. I could not scrape it because ${reason}.`, 
                'warning', 
                8000
            );
            
            // Focus on the job description textarea
            this.jobDescriptionInput.focus();
            
        } else {
            // For other errors, show the generic error message
            this.showError(`Failed to generate resume: ${error.message}`);
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
            this.setResumeTemplate('engineering_manager');
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
        
        // Show loading status
        this.showAutoDetectionStatus('🔍 Auto-detecting company and position...', 'loading');
        
        try {
            console.log('Making auto-detection request for URL:', jobUrl);
            const response = await fetch('/api/parse-job', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ job_url: jobUrl })
            });
            
            console.log('Auto-detection response status:', response.status);
            
            const result = await response.json();
            console.log('Auto-detection result:', result);
            
            if (result.success) {
                // Auto-populate fields with detected values (overwrite if we have good data)
                if (result.company_name && result.company_name !== "Not found") {
                    this.companyNameInput.value = result.company_name;
                }
                if (result.position_title && result.position_title !== "404 error" && result.position_title !== null) {
                    this.positionTitleInput.value = result.position_title;
                }
                
                // Auto-select resume template based on position if suggested (always override)
                if (result.suggested_template) {
                    this.setResumeTemplate(result.suggested_template);
                    console.log(`Auto-selected template: ${result.suggested_template} based on position: ${result.position_title}`);
                } else if (!this.resumeTemplateSelect.value || this.resumeTemplateSelect.value === "") {
                    // Fallback to default template if no suggestion and nothing selected
                    this.setResumeTemplate('engineering_manager');
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
                this.setResumeTemplate('engineering_manager');
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
            this.setResumeTemplate("");
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
                this.setResumeTemplate(result.suggested_template);
                this.showAutoDetectionStatus(
                    `✅ Auto-selected both templates: ${result.suggested_template.replace('_', ' ')} based on position "${positionTitle}"`, 
                    'success'
                );
                
                // Auto-hide status after 3 seconds
                setTimeout(() => this.hideAutoDetectionStatus(), 3000);
                
                console.log(`Auto-selected both resume templates: ${result.suggested_template} for position: ${positionTitle}`);
            } else {
                // Fallback to default
                this.setResumeTemplate('engineering_manager');
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
                this.setResumeTemplate('engineering_manager');
            }
        }
    }
    
    // Remove unused methods
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ResumeAutomation();
});