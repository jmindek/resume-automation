"""Job description parsing utilities for Resume Automation System"""

import re
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse


class JobParser:
    """Parses job descriptions to extract company name and position title"""
    
    # Common company domain mappings
    COMPANY_DOMAINS = {
        'google.com': 'Google',
        'microsoft.com': 'Microsoft',
        'amazon.com': 'Amazon',
        'meta.com': 'Meta',
        'facebook.com': 'Meta',
        'apple.com': 'Apple',
        'netflix.com': 'Netflix',
        'tesla.com': 'Tesla',
        'uber.com': 'Uber',
        'airbnb.com': 'Airbnb',
        'linkedin.com': 'LinkedIn',
        'salesforce.com': 'Salesforce',
        'oracle.com': 'Oracle',
        'ibm.com': 'IBM',
        'intel.com': 'Intel',
        'nvidia.com': 'NVIDIA',
        'adobe.com': 'Adobe',
        'stripe.com': 'Stripe',
        'github.com': 'GitHub',
        'gitlab.com': 'GitLab',
        'atlassian.com': 'Atlassian',
        'shopify.com': 'Shopify',
        'zoom.us': 'Zoom',
        'slack.com': 'Slack',
        'twilio.com': 'Twilio',
        'palantir.com': 'Palantir',
        'databricks.com': 'Databricks',
        'snowflake.com': 'Snowflake',
        'confluent.io': 'Confluent',
    }
    
    # Job board patterns
    JOB_BOARD_PATTERNS = {
        'greenhouse.io': {
            'company_pattern': r'/jobs/(\d+)\?gh_jid=\d+',  # Extract from URL structure
            'position_pattern': r'<h1[^>]*>([^<]+)</h1>',
        },
        'lever.co': {
            'company_pattern': r'https://jobs\.lever\.co/([^/]+)',
            'position_pattern': r'<h2[^>]*>([^<]+)</h2>',
        },
        'workday.com': {
            'company_pattern': r'/([^/]+)\.wd\d+\.myworkdayjobs\.com',
            'position_pattern': r'<h1[^>]*>([^<]+)</h1>',
        },
        'jobvite.com': {
            'company_pattern': r'//hire\.jobvite\.com/([^/]+)',
            'position_pattern': r'<h1[^>]*>([^<]+)</h1>',
        },
        'bamboohr.com': {
            'company_pattern': r'//([^.]+)\.bamboohr\.com',
            'position_pattern': r'<h1[^>]*>([^<]+)</h1>',
        }
    }
    
    # Common position title patterns
    POSITION_PATTERNS = [
        # Engineering roles
        r'Senior Software Engineer',
        r'Software Engineer',
        r'Senior Engineer',
        r'Staff Engineer',
        r'Principal Engineer',
        r'Engineering Manager',
        r'Software Engineering Manager',
        r'Manager, Software Engineering',
        r'Senior Engineering Manager',
        r'Director of Engineering',
        r'VP of Engineering',
        r'CTO',
        r'Tech Lead',
        r'Technical Lead',
        r'Lead Software Engineer',
        
        # Data roles
        r'Data Engineer',
        r'Senior Data Engineer',
        r'Data Engineering Manager',
        r'Staff Data Engineer',
        r'Principal Data Engineer',
        r'Data Scientist',
        r'Senior Data Scientist',
        r'Machine Learning Engineer',
        r'ML Engineer',
        
        # Product roles
        r'Product Manager',
        r'Senior Product Manager',
        r'Principal Product Manager',
        r'Director of Product',
        r'VP of Product',
        
        # DevOps/Platform
        r'DevOps Engineer',
        r'Site Reliability Engineer',
        r'SRE',
        r'Platform Engineer',
        r'Infrastructure Engineer',
        
        # Frontend/Backend
        r'Frontend Engineer',
        r'Backend Engineer',
        r'Full Stack Engineer',
        r'Full-Stack Engineer',
    ]
    
    @classmethod
    def extract_from_url(cls, url: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract company name from job posting URL"""
        try:
            parsed_url = urlparse(url.lower())
            domain = parsed_url.netloc
            
            # Remove www prefix
            domain = re.sub(r'^www\.', '', domain)
            
            # Check direct company domains
            if domain in cls.COMPANY_DOMAINS:
                return cls.COMPANY_DOMAINS[domain], None
            
            # Check job board patterns
            for job_board, patterns in cls.JOB_BOARD_PATTERNS.items():
                if job_board in domain:
                    company_match = re.search(patterns['company_pattern'], url, re.IGNORECASE)
                    if company_match:
                        company = company_match.group(1).replace('-', ' ').title()
                        return company, None
            
            # Try to extract company from subdomain
            subdomain_match = re.match(r'([^.]+)\.', domain)
            if subdomain_match:
                subdomain = subdomain_match.group(1)
                if subdomain not in ['www', 'jobs', 'careers', 'hire', 'apply']:
                    return subdomain.replace('-', ' ').title(), None
            
        except Exception as e:
            print(f"Error parsing URL: {e}")
        
        return None, None
    
    @classmethod
    def extract_from_content(cls, job_description: str, url: str = None) -> Tuple[Optional[str], Optional[str]]:
        """Extract company name and position title from job description content"""
        company = None
        position = None
        
        # Clean job description for parsing
        clean_text = re.sub(r'<[^>]+>', '', job_description)  # Remove HTML tags
        clean_text = re.sub(r'\s+', ' ', clean_text)  # Normalize whitespace
        
        # Prioritize content analysis over URL parsing
        company = cls._extract_company_name(clean_text)
        position = cls._extract_position_title(clean_text)
        
        # Only use URL extraction as fallback if content analysis failed
        if not company or not position:
            if url:
                url_company, url_position = cls.extract_from_url(url)
                if not company and url_company:
                    company = url_company
                if not position and url_position:
                    position = url_position
        
        return company, position
    
    @classmethod
    def _extract_position_title(cls, text: str) -> Optional[str]:
        """Extract position title from job description text"""
        # Look for position patterns in order of specificity
        for pattern in cls.POSITION_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0]
        
        # Look for common title indicators at the beginning of text
        title_indicators = [
            r'^([^.!?\n]{10,60}(?:Engineer|Manager|Developer|Analyst|Scientist|Lead|Director|VP|CTO))',
            r'Position:\s*([^.!?\n]{5,60})',
            r'Role:\s*([^.!?\n]{5,60})',
            r'Job Title:\s*([^.!?\n]{5,60})',
            r'We are looking for (?:a|an)\s+([^.!?\n]{5,60}(?:Engineer|Manager|Developer|Analyst|Scientist))',
        ]
        
        for pattern in title_indicators:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                title = match.group(1).strip()
                if 5 <= len(title) <= 60:  # Reasonable title length
                    return title
        
        return None
    
    @classmethod
    def _extract_company_name(cls, text: str) -> Optional[str]:
        """Extract company name from job description text"""
        # Look for common company indicators with better patterns
        company_patterns = [
            # Page titles and headers
            r'<title[^>]*>([^-|]+?)(?:\s*[-|]|\s*jobs?\s|careers?|hiring|$)',
            r'<h1[^>]*>([^<]+?)\s*(?:jobs?|careers?|hiring|$)',
            
            # Company introductions
            r'(?:About|Join|At)\s+([A-Z][a-zA-Z0-9\s&.,()-]{2,40})(?:\s*[,.:]|\s*$)',
            r'Company:\s*([A-Za-z0-9][a-zA-Z0-9\s&.,()-]{1,40})',
            r'Organization:\s*([A-Za-z0-9][a-zA-Z0-9\s&.,()-]{1,40})',
            
            # Company mentions
            r'([A-Z][a-zA-Z0-9\s&.,()-]{2,40})\s+is\s+(?:looking for|seeking|hiring|a leading|an?)',
            r'Join\s+(?:the\s+team\s+at\s+)?([A-Z][a-zA-Z0-9\s&.,()-]{2,40})',
            r'Work\s+(?:at|with)\s+([A-Z][a-zA-Z0-9\s&.,()-]{2,40})',
            
            # Job board patterns
            r'Apply\s+to\s+([A-Z][a-zA-Z0-9\s&.,()-]{2,40})',
            r'Career\s+(?:opportunity\s+)?at\s+([A-Z][a-zA-Z0-9\s&.,()-]{2,40})',
            
            # Direct mentions
            r'^([A-Z][a-zA-Z0-9\s&.,()-]{2,40})\s+(?:is|seeks|wants|needs)',
        ]
        
        # First try to get from the beginning of the text (most reliable)
        first_200_chars = text[:200]
        
        for pattern in company_patterns:
            matches = re.findall(pattern, first_200_chars, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                company = cls._clean_company_name(match.strip())
                if company:
                    return company
        
        # If not found in first part, search the full text
        for pattern in company_patterns[3:]:  # Skip title patterns for full text search
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                company = cls._clean_company_name(match.strip())
                if company:
                    return company
        
        return None
    
    @classmethod
    def _clean_company_name(cls, company: str) -> Optional[str]:
        """Clean and validate company name"""
        if not company:
            return None
            
        # Remove common prefixes/suffixes
        company = re.sub(r'^(?:the\s+)?', '', company, flags=re.IGNORECASE)
        company = re.sub(r'\s*(?:inc\.?|llc\.?|corp\.?|ltd\.?|co\.?)\s*$', '', company, flags=re.IGNORECASE)
        company = company.strip(' .,;:-')
        
        # Filter out common false positives
        false_positives = [
            'this', 'the', 'we', 'you', 'our', 'your', 'all', 'some', 'many', 'most', 
            'key', 'main', 'primary', 'current', 'new', 'next', 'first', 'last',
            'position', 'role', 'job', 'career', 'opportunity', 'team', 'company',
            'organization', 'department', 'division', 'group', 'candidate', 'applicant',
            'engineering', 'software', 'technology', 'technical', 'senior', 'junior',
            'full time', 'part time', 'remote', 'onsite', 'hybrid'
        ]
        
        if company.lower() in false_positives:
            return None
        
        # Check reasonable length and format
        if 2 <= len(company) <= 50 and not company.isdigit():
            # Must contain at least one letter
            if re.search(r'[a-zA-Z]', company):
                return company
        
        return None
    
    @classmethod
    def select_resume_template(cls, position_title: str) -> Optional[str]:
        """Select appropriate resume template based on position title"""
        if not position_title:
            return None
        
        position_lower = position_title.lower()
        
        # Senior Engineering Manager patterns
        if any(pattern in position_lower for pattern in [
            'senior engineering manager', 'senior eng manager', 'engineering director', 
            'director of engineering', 'vp engineering', 'head of engineering',
            'senior director engineering', 'principal engineering manager'
        ]):
            return 'senior_engineering_manager'
        
        # Data Engineering Manager patterns
        elif any(pattern in position_lower for pattern in [
            'data engineering manager', 'data eng manager', 'manager data engineering',
            'head of data engineering', 'director data engineering', 'data platform manager',
            'analytics engineering manager', 'data infrastructure manager'
        ]):
            return 'data_engineering_manager'
        
        # General Engineering Manager patterns (broader match)
        elif any(pattern in position_lower for pattern in [
            'engineering manager', 'eng manager', 'software engineering manager',
            'software eng manager', 'team lead', 'tech lead manager', 'development manager'
        ]):
            return 'engineering_manager'
        
        # Senior Software Engineer patterns (for individual contributor roles)
        elif any(pattern in position_lower for pattern in [
            'senior software engineer', 'senior engineer', 'staff engineer', 
            'principal engineer', 'senior developer', 'lead engineer',
            'senior data engineer', 'senior backend engineer', 'senior frontend engineer',
            'senior full stack engineer', 'senior platform engineer', 'senior sre',
            'senior devops engineer', 'senior software developer'
        ]):
            return 'senior_software_engineer'
        
        # Default to senior software engineer for other engineering roles
        elif any(pattern in position_lower for pattern in [
            'software engineer', 'engineer', 'developer', 'programmer',
            'data engineer', 'backend engineer', 'frontend engineer',
            'full stack', 'platform engineer', 'devops', 'sre'
        ]):
            return 'senior_software_engineer'
        
        # No match found
        return None
    
    @classmethod
    def parse_job_posting(cls, job_description: str, url: str = None) -> Dict[str, Optional[str]]:
        """Main method to parse job posting and return extracted information"""
        company, position = cls.extract_from_content(job_description, url)
        
        # Auto-select resume template based on position
        suggested_template = cls.select_resume_template(position) if position else None
        
        return {
            'company_name': company,
            'position_title': position,
            'suggested_template': suggested_template,
            'confidence': 'high' if (company and position) else 'medium' if (company or position) else 'low'
        }