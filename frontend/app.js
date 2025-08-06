// Resume Automation Frontend - Level 2
class ResumeAutomation {
    constructor() {
        this.form = document.getElementById('resumeForm');
        this.generateBtn = document.getElementById('generateBtn');
        this.loading = document.getElementById('loading');
        this.error = document.getElementById('error');
        this.results = document.getElementById('results');
        this.driveStatus = document.getElementById('driveStatus');
        this.testDriveBtn = document.getElementById('testDriveBtn');
        this.useDriveIntegration = document.getElementById('useDriveIntegration');
        this.driveOptions = document.getElementById('driveOptions');
        this.driveResults = document.getElementById('driveResults');
        this.jobUrlInput = document.getElementById('jobUrl');
        this.companyNameInput = document.getElementById('companyName');
        this.positionTitleInput = document.getElementById('positionTitle');
        this.autoDetectionStatus = document.getElementById('autoDetectionStatus');
        this.resumeTemplateSelect = document.getElementById('resumeTemplate');
        
        this.init();
    }
    
    init() {
        this.form.addEventListener('submit', this.handleSubmit.bind(this));
        this.testDriveBtn.addEventListener('click', this.testDriveConnection.bind(this));
        this.useDriveIntegration.addEventListener('change', this.toggleDriveOptions.bind(this));
        
        // Auto-detect job info when URL changes
        this.jobUrlInput.addEventListener('blur', this.autoDetectJobInfo.bind(this));
        this.jobUrlInput.addEventListener('change', this.autoDetectJobInfo.bind(this));
        
        // Auto-select baseline resume when position title changes manually
        this.positionTitleInput.addEventListener('blur', this.handlePositionTitleChange.bind(this));
        this.positionTitleInput.addEventListener('change', this.handlePositionTitleChange.bind(this));
        
        // Load initial status and templates
        this.loadDriveStatus();
        this.loadTemplateOptions();
        
        // Show drive options by default since it's checked
        this.toggleDriveOptions();
    }
    
    async handleSubmit(event) {
        event.preventDefault();
        
        const formData = new FormData(this.form);
        const requestData = {
            job_url: document.getElementById('jobUrl').value,
            motivation_notes: document.getElementById('motivationNotes').value || "I am passionate about building scalable systems and leading engineering teams to deliver high-quality software solutions.",
            resume_template: document.getElementById('resumeTemplate').value,
            use_drive_integration: document.getElementById('useDriveIntegration').checked,
            company_name: document.getElementById('companyName').value,
            position_title: document.getElementById('positionTitle').value
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
        
        if (driveResults.resume_path) {
            html += `<li><strong>Resume:</strong> ${driveResults.resume_path}</li>`;
        }
        
        if (driveResults.cover_letter_path) {
            html += `<li><strong>Cover Letter:</strong> ${driveResults.cover_letter_path}</li>`;
        }
        
        if (driveResults.folder_path) {
            html += `<li><strong>📂 Folder:</strong> ${driveResults.folder_path}</li>`;
        }
        
        html += '</ul>';
        html += '<p style="font-size: 12px; color: #666; margin-top: 10px;">💡 Files will sync to Google Drive if you have Google Drive desktop app installed.</p>';
        
        driveLinksContent.innerHTML = html;
    }
    
    async loadDriveStatus() {
        try {
            const response = await fetch('/api/config/drive');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const config = await response.json();
            
            if (config.service_account_configured && config.templates_folder_configured && config.output_folder_configured) {
                this.showDriveStatus('✅ Google Drive configured and ready', 'success');
            } else {
                let issues = [];
                if (!config.service_account_configured) issues.push('service account');
                if (!config.templates_folder_configured) issues.push('templates folder');
                if (!config.output_folder_configured) issues.push('output folder');
                
                this.showDriveStatus(`⚠️ Missing: ${issues.join(', ')}. See SETUP_LEVEL_2.md`, 'warning');
            }
            
        } catch (error) {
            console.error('Drive status error:', error);
            this.showDriveStatus(`❌ Cannot connect to server. Is the backend running? (${error.message})`, 'error');
        }
    }
    
    async testDriveConnection() {
        this.testDriveBtn.disabled = true;
        this.testDriveBtn.textContent = 'Testing...';
        this.showDriveStatus('🔄 Testing Google Drive connection...', 'warning');
        
        try {
            const response = await fetch('/api/drive/test');
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            
            if (result.connected) {
                this.showDriveStatus('✅ Google Drive connection successful! Ready to use Level 2 features.', 'success');
            } else {
                this.showDriveStatus(`❌ Google Drive connection failed: ${result.message || 'Unknown error'}`, 'error');
            }
        } catch (error) {
            console.error('Drive test error:', error);
            this.showDriveStatus(`❌ Error testing connection: ${error.message}`, 'error');
        } finally {
            this.testDriveBtn.disabled = false;
            this.testDriveBtn.textContent = 'Test Connection';
        }
    }
    
    showDriveStatus(message, type) {
        const statusContent = document.getElementById('driveStatusContent');
        const colors = {
            success: '#d4edda',
            warning: '#fff3cd',
            error: '#f8d7da'
        };
        
        statusContent.textContent = message;
        this.driveStatus.style.backgroundColor = colors[type] || colors.warning;
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
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ResumeAutomation();
});