"""Integration tests for resume automation backend"""

import pytest
import pytest_asyncio
import asyncio
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import yaml
from pathlib import Path

# Import using absolute imports from the backend package
from backend.main import generate_resume, ResumeRequest, generate_prompts
from backend.config_manager import get_config

def load_prompts_from_config():
    """Load prompts from the config.yaml file"""
    config_path = Path(__file__).parent.parent.parent / 'config.yaml'
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config['prompts']


class TestPromptIntegration:
    """Integration tests for prompt formatting"""
    
    @pytest.fixture
    def mock_drive_manager(self):
        """Mock DriveManager for testing"""
        mock_manager = Mock()
        mock_manager.find_template_by_name.return_value = "mock_template_id"
        mock_manager.get_document_link.return_value = "https://docs.google.com/document/d/1wHsGEaD58amJ2KpfKg3GeDFYa3aw2JbZRxjB5sVgrBk/edit?usp=sharing"
        mock_manager.get_document_content.return_value = None  # Force using link
        return mock_manager
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration"""
        mock_config = Mock()
        mock_config.get_baseline_resume_mapping.return_value = {
            "engineering_manager": "Engineering_Manager_Template"
        }
        # Load actual prompts from config.yaml
        mock_config.get_prompts.return_value = load_prompts_from_config()
        mock_config.get.return_value = None  # No cover letter template
        return mock_config
    
    @pytest.fixture
    def sample_request(self):
        """Sample request for Engineering Manager role"""
        return ResumeRequest(
            job_url="https://example.com/job",
            motivation_notes="I am passionate about leading engineering teams",
            additional_details="Looking for a role with strong technical leadership opportunities",
            resume_template="engineering_manager",
            company_name="TestCorp",
            position_title="Engineering Manager",
            use_drive_integration=False
        )
    
    def test_generate_prompts_with_drive_link(self, mock_config, sample_request):
        """Test that generate_prompts formats prompts correctly with a Google Drive link"""
        # Setup test data
        job_description = "Sample job description for Engineering Manager role"
        resume_reference = "Google Drive Resume Template: https://docs.google.com/document/d/1wHsGEaD58amJ2KpfKg3GeDFYa3aw2JbZRxjB5sVgrBk/edit?usp=sharing"
        
        # Call the function
        prompts = generate_prompts(
            prompts_config=mock_config.get_prompts(),
            motivation_notes=sample_request.motivation_notes,
            job_description=job_description,
            resume_reference=resume_reference,
            additional_details=sample_request.additional_details,
            cover_letter_base=None
        )
        
        # Verify we got the expected number of prompts
        assert len(prompts) == 4
        
        # Print the generated prompts for verification
        for i, prompt in enumerate(prompts, 1):
            print(f"\n=== PROMPT {i} ===\n{prompt}\n")
            
        # Check that placeholders were properly replaced in prompt 1
        assert "{resume_base}" not in prompts[0], "Placeholder {resume_base} was not replaced in prompt 1"
        assert "{job_description}" not in prompts[0], "Placeholder {job_description} was not replaced in prompt 1"
        assert "{additional_details}" not in prompts[0], "Placeholder {additional_details} was not replaced in prompt 1"
        
        # Check that the resume reference and additional details were included in the first prompt
        assert resume_reference in prompts[0], "Resume reference not found in prompt 1"
        assert sample_request.additional_details in prompts[0], "Additional details not found in prompt 1"
        
        # Check that motivation_notes is NOT in prompt 1
        assert sample_request.motivation_notes not in prompts[0], "Motivation notes should not be in prompt 1"
        
        # Check that placeholders for subsequent prompts are still present
        assert "[RESUME_FROM_PROMPT_1]" in prompts[1], "Placeholder [RESUME_FROM_PROMPT_1] not found in prompt 2"
        assert "[RESUME_FROM_PROMPT_2]" in prompts[2], "Placeholder [RESUME_FROM_PROMPT_2] not found in prompt 3"
        assert "[RESUME_FROM_PROMPT_2]" in prompts[3], "Placeholder [RESUME_FROM_PROMPT_2] not found in prompt 4"
        
        # Check that additional_details is in prompt 2
        assert sample_request.additional_details in prompts[1], "Additional details not found in prompt 2"
        
        # Check that motivation_notes is only in prompt 3
        assert sample_request.motivation_notes in prompts[2], "Motivation notes not found in prompt 3"
        assert sample_request.motivation_notes not in prompts[1], "Motivation notes should not be in prompt 2"
        assert sample_request.motivation_notes not in prompts[3], "Motivation notes should not be in prompt 4"
    
    def test_third_prompt_formatting(self, mock_config, sample_request):
        """Test that the third prompt is formatted correctly"""
        # Setup test data
        job_description = "Sample job description for Engineering Manager role"
        resume_reference = "Google Drive Resume Template: https://docs.google.com/document/d/1wHsGEaD58amJ2KpfKg3GeDFYa3aw2JbZRxjB5sVgrBk/edit?usp=sharing"
        
        # Call the function to get all prompts
        prompts = generate_prompts(
            prompts_config=mock_config.get_prompts(),
            motivation_notes=sample_request.motivation_notes,
            job_description=job_description,
            resume_reference=resume_reference,
            additional_details=sample_request.additional_details,
            cover_letter_base=None
        )
        
        # Get the third prompt (index 2)
        prompt_3 = prompts[2]
        
        # Print the generated prompt for debugging
        print(f"\n=== THIRD PROMPT ===\n{prompt_3}\n")
        
        # Check that the third prompt contains the expected sections
        assert "Using my baseline cover letter template" in prompt_3
        assert "create a compelling cover letter" in prompt_3
        assert "1. Update the template with company-specific mission alignment" in prompt_3
        assert "6. I am available immediately" in prompt_3
        
        # Check that placeholders were properly set
        assert "[RESUME_FROM_PROMPT_2]" in prompt_3, "Placeholder [RESUME_FROM_PROMPT_2] not found in prompt 3"
        assert sample_request.motivation_notes in prompt_3, "Motivation notes not found in prompt 3"
        assert sample_request.additional_details in prompt_3, "Additional details not found in prompt 3"
        assert job_description in prompt_3, "Job description not found in prompt 3"
        assert "No cover letter template provided" in prompt_3, "Cover letter template placeholder not found in prompt 3"
        
        # Verify motivation_notes is not in other prompts
        for i, prompt in enumerate(prompts):
            if i != 2:  # Skip prompt 3
                assert sample_request.motivation_notes not in prompt, f"Motivation notes should not be in prompt {i+1}"
        
        # Print the formatted third prompt for verification
        print(f"\n=== THIRD PROMPT ===\n{prompt_3}\n")
    
    def test_drive_link_fallback_to_content(self, mock_config, sample_request):
        """Test that when link fails, it falls back to content"""
        # Setup test data
        job_description = "Sample job description for Engineering Manager role"
        
        # Simulate the case where we fall back to content (no link)
        resume_content = "Mock resume content from Google Drive"
        
        # Call the function with the content directly (simulating the fallback)
        prompts = generate_prompts(
            prompts_config=mock_config.get_prompts(),
            motivation_notes=sample_request.motivation_notes,
            job_description=job_description,
            resume_reference=resume_content,  # Using content directly, not a link
            additional_details=sample_request.additional_details,
            cover_letter_base=None
        )
        
        # Get the first prompt
        first_prompt = prompts[0]
        
        # Print the first prompt for debugging
        print(f"\n=== FIRST PROMPT (Content Fallback) ===\n{first_prompt}\n")
        
        # Verify the first prompt contains the content (not a link format)
        assert resume_content in first_prompt, "Resume content not found in the first prompt"
        assert "Google Drive Resume Template:" not in first_prompt, "Unexpected Google Drive link format in the first prompt"
        
        # Verify the prompt contains the expected sections
        assert "You are an elite professional resume writer" in first_prompt
        assert "Please align my resume with this specific job description" in first_prompt
        assert "Focus on" in first_prompt
        assert "JD analysis:" in first_prompt
        assert "Content prioritization:" in first_prompt
        assert "Skills/tech stack alignment:" in first_prompt
        
        # Verify the job description and resume content are included
        assert job_description in first_prompt, "Job description not found in the first prompt"
        assert "MY CURRENT RESUME TO OPTIMIZE:" in first_prompt, "Resume section header not found"
        assert resume_content in first_prompt, "Resume content not found in the first prompt"


if __name__ == "__main__":
    # Run the tests directly
    pytest.main([__file__, "-v", "-s"])
