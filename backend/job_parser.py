"""Job description parsing utilities for Resume Automation System"""

import re
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup


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
            'position_pattern': r'<h1[^>]*>([^<]+)</h1>',  # Fallback pattern
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
        },
        'ashbyhq.com': {
            'company_pattern': r'/([^/]+)/[^/]+/application',
            'position_pattern': r'<title[^>]*>([^<]+)</title>',
        },
        'ats.rippling.com': {
            'company_pattern': r'/([^/-]+)-careers-page',  # Extract company from URL path
            'position_pattern': r'<title[^>]*>([^<]+)</title>',
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
                        from urllib.parse import unquote
                        company = unquote(company_match.group(1))  # URL decode
                        company = company.replace('-', ' ').replace('_', ' ').strip()
                        # Don't title case for known company names that have specific casing
                        if company.lower() in ['jasper', 'jasper ai']:
                            return 'Jasper', None
                        return company.title(), None
            
            # Try to extract company from subdomain
            subdomain_match = re.match(r'([^.]+)\.', domain)
            if subdomain_match:
                subdomain = subdomain_match.group(1)
                if subdomain not in ['www', 'jobs', 'careers', 'hire', 'apply', 'ats']:
                    return subdomain.replace('-', ' ').title(), None
            
            # If subdomain extraction failed, try extracting from root domain
            domain_parts = domain.split('.')
            if len(domain_parts) >= 2:
                # Extract company name from the main domain (e.g., "toasttab" from "careers.toasttab.com")
                company_name = domain_parts[-2]
                # For known special cases, use the full domain name as company name
                if company_name in ['toasttab']:
                    return 'Toast', None
                # Clean up common domain artifacts only if they're clearly suffixes
                company_name = re.sub(r'(labs?|inc|corp|llc|ltd)$', '', company_name, flags=re.IGNORECASE).strip()
                if company_name and len(company_name) > 2:  # Must be reasonable length
                    return company_name.replace('-', ' ').title(), None
        except Exception as e:
            print(f"Error parsing URL: {e}")
        
        return None, None
    
    @classmethod
    def extract_from_content(cls, job_description: str, url: str = None) -> Tuple[Optional[str], Optional[str]]:
        """Extract company name and position title from job description content"""
        company = None
        position = None
        
        # First try to extract from HTML title tag if present (most reliable for job boards)
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', job_description, re.IGNORECASE)
        if title_match:
            title_content = title_match.group(1).strip()
            
            # Handle common title formats for job boards
            title_company, title_position = cls._parse_job_title(title_content, url)
            if title_company:
                company = title_company
            if title_position:
                position = title_position
        
        # Clean job description for parsing if we still need company or position
        if not company or not position:
            clean_text = re.sub(r'<[^>]+>', '', job_description)  # Remove HTML tags
            clean_text = re.sub(r'\s+', ' ', clean_text)  # Normalize whitespace
            
            # Extract from content if not found in title
            if not company:
                company = cls._extract_company_name(clean_text)
            if not position:
                position = cls._extract_position_title(clean_text)
        
        # Use URL extraction as final fallback
        if not company or not position:
            if url:
                url_company, url_position = cls.extract_from_url(url)
                if not company and url_company:
                    company = url_company
                if not position and url_position:
                    position = url_position
        
        return company, position
    
    @classmethod
    def _parse_job_title(cls, title_content: str, url: str = None) -> Tuple[Optional[str], Optional[str]]:
        """Parse job title from HTML title tag to extract company and position"""
        company = None
        position = None
        
        # Common job board title formats
        title_patterns = [
            # "Company Name - Job Title" (lever.co, greenhouse.io, etc.)
            r'^([^-]+?)\s*[-–—]\s*(.+?)(?:\s*[-–—].*)?$',
            # "Job Title at Company Name"
            r'^(.+?)\s+at\s+([^|]+?)(?:\s*[|].*)?$',
            # "Job Title | Company Name"
            r'^(.+?)\s*[|]\s*([^|]+?)(?:\s*[|].*)?$',
            # "Company: Job Title"
            r'^([^:]+?):\s*(.+?)(?:\s*[-–—].*)?$'
        ]
        
        for pattern in title_patterns:
            match = re.match(pattern, title_content.strip(), re.IGNORECASE)
            if match:
                part1, part2 = match.groups()
                part1 = part1.strip()
                part2 = part2.strip()
                
                # For "Company - Position" format (most common)
                if pattern == title_patterns[0]:
                    # Check if part2 looks like a location instead of a job title
                    # Common location patterns: "Remote", "City, State", "City, Country"
                    location_indicators = ['remote', 'onsite', 'hybrid', 'united states', 'usa', 'us', 'uk', 'canada']
                    is_location = (
                        any(indicator in part2.lower() for indicator in location_indicators) or
                        re.search(r'^[A-Za-z\s]+,\s*[A-Za-z\s]+$', part2)  # "City, State" format
                    )
                    
                    if is_location:
                        # This is "Position - Location" format, not "Company - Position"
                        position = cls._clean_position_title(part1)
                        # Try to get company from URL instead
                        if url:
                            url_company, _ = cls.extract_from_url(url)
                            company = url_company
                    else:
                        # Standard "Company - Position" format
                        company = cls._clean_company_name(part1)
                        position = cls._clean_position_title(part2)
                # For "Position at Company" format
                elif pattern == title_patterns[1]:
                    position = cls._clean_position_title(part1)
                    company = cls._clean_company_name(part2)
                # For "Position | Company" format
                elif pattern == title_patterns[2]:
                    position = cls._clean_position_title(part1)
                    company = cls._clean_company_name(part2)
                # For "Company: Position" format
                elif pattern == title_patterns[3]:
                    company = cls._clean_company_name(part1)
                    position = cls._clean_position_title(part2)
                
                # If we successfully parsed both, return them
                if company and position:
                    return company, position
        
        # If no pattern matched, try to extract company from URL and position from title
        if url and not company:
            url_company, _ = cls.extract_from_url(url)
            if url_company:
                company = url_company
                # Title might be just the position if company is in URL
                position = cls._clean_position_title(title_content)
        
        return company, position
    
    @classmethod
    def _clean_position_title(cls, position: str) -> Optional[str]:
        """Clean and validate position title"""
        if not position:
            return None
            
        # Remove common suffixes/prefixes that aren't part of the actual position
        position = re.sub(r'\s*[-–—]\s*.*(?:jobs?|careers?|hiring|apply|remote|onsite).*$', '', position, flags=re.IGNORECASE)
        position = re.sub(r'\s*[|]\s*.*(?:jobs?|careers?).*$', '', position, flags=re.IGNORECASE)
        position = position.strip(' .,;:-')
        
        # Check reasonable length and format
        if 5 <= len(position) <= 80 and not position.isdigit():
            # Must contain at least one letter
            if re.search(r'[a-zA-Z]', position):
                return position
        
        return None
    
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
        for pattern in company_patterns[1:]:  # Skip first pattern for full text search
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
            'manager, data engineer', 'manager, data engineering',  # Comma-separated formats
            'head of data engineering', 'director data engineering', 'data platform manager',
            'analytics engineering manager', 'data infrastructure manager'
        ]):
            return 'data_engineering_manager'
        
        # General Engineering Manager patterns (broader match)
        elif any(pattern in position_lower for pattern in [
            'engineering manager', 'eng manager', 'software engineering manager',
            'software eng manager', 'team lead', 'tech lead manager', 'development manager',
            'manager, software development', 'software development manager',
            'manager software', 'technical manager', 'engineering lead'
        ]) or any(
            # Handle numbered manager positions like "Manager 1, Software Development"
            ('manager' in position_lower and pattern in position_lower) for pattern in [
                'software development', 'software engineering', 'engineering', 'development'
            ]
        ):
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
    def _extract_salary_from_spa(cls, html_content: str, url: str = None) -> Optional[str]:
        """Extract salary from SPA pages by looking for embedded JSON or metadata"""
        try:
            import json
            import re
            
            # Look for JSON data embedded in the page that might contain salary info
            # Common patterns: window.__INITIAL_STATE__, __NUXT__, __NEXT_DATA__
            json_patterns = [
                r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\});',
                r'window\.__NUXT__\s*=\s*(\{.*?\});',
                r'window\.__NEXT_DATA__\s*=\s*(\{.*?\});',
                r'data-nuxt-data="[^"]*"[^>]*>([^<]*)</script>',
                r'"salary":\s*"([^"]*)"',
                r'"compensation":\s*"([^"]*)"',
                r'"pay":\s*"([^"]*)"'
            ]
            
            for pattern in json_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE | re.DOTALL)
                for match in matches:
                    try:
                        if match.strip().startswith('{'):
                            # Try to parse as JSON
                            data = json.loads(match)
                            salary_info = cls._search_json_for_salary(data)
                            if salary_info:
                                return salary_info
                        else:
                            # Direct string match for salary/compensation
                            if any(keyword in match.lower() for keyword in ['$', 'k', 'salary', 'compensation']):
                                extracted = cls.extract_salary(match)
                                if extracted and extracted != "TBD":
                                    return extracted
                    except (json.JSONDecodeError, TypeError):
                        continue
            
            # Try to fetch job data from potential API endpoints
            if url:
                api_salary = cls._try_api_endpoints(url)
                if api_salary:
                    return api_salary
            
            # Look for URL parameters that might contain salary info
            if url:
                from urllib.parse import urlparse, parse_qs
                parsed = urlparse(url)
                params = parse_qs(parsed.query)
                
                for key, values in params.items():
                    if any(salary_key in key.lower() for salary_key in ['salary', 'pay', 'compensation', 'wage']):
                        for value in values:
                            extracted = cls.extract_salary(value)
                            if extracted and extracted != "TBD":
                                return extracted
            
            # Look for meta tags or structured data
            meta_patterns = [
                r'<meta[^>]*property="(?:job:)?salary"[^>]*content="([^"]*)"',
                r'<meta[^>]*name="salary"[^>]*content="([^"]*)"',
                r'"@type":\s*"JobPosting"[^}]*"baseSalary":\s*\{[^}]*"value":\s*"([^"]*)"'
            ]
            
            for pattern in meta_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                for match in matches:
                    extracted = cls.extract_salary(match)
                    if extracted and extracted != "TBD":
                        return extracted
            
            return None
            
        except Exception as e:
            print(f"Error extracting salary from SPA: {e}")
            return None
    
    @classmethod
    def _try_api_endpoints(cls, job_url: str) -> Optional[str]:
        """Try to fetch salary data from potential API endpoints"""
        try:
            import re
            from urllib.parse import urlparse
            
            # Extract job ID from URL if present
            job_id_pattern = r'/([A-F0-9]{32})/'
            job_id_match = re.search(job_id_pattern, job_url)
            
            if not job_id_match:
                return None
                
            job_id = job_id_match.group(1)
            parsed_url = urlparse(job_url)
            base_domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            # Common API endpoint patterns for job boards
            api_endpoints = [
                f"{base_domain}/api/jobs/{job_id}",
                f"{base_domain}/api/job/{job_id}",
                f"{base_domain}/api/job-details/{job_id}",
                f"{base_domain}/api/positions/{job_id}",
                f"https://api.dejobs.org/jobs/{job_id}",
                f"https://api.dejobs.org/job/{job_id}"
            ]
            
            # Try each endpoint with a short timeout
            for endpoint in api_endpoints:
                try:
                    print(f"🔍 Trying API endpoint: {endpoint}")
                    response = requests.get(endpoint, timeout=5, headers={
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                        'Accept': 'application/json, text/plain, */*'
                    })
                    
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            salary_info = cls._search_json_for_salary(data)
                            if salary_info:
                                print(f"✅ Found salary in API: {salary_info}")
                                return salary_info
                        except:
                            # Try extracting from text response
                            salary_info = cls.extract_salary(response.text)
                            if salary_info and salary_info != "TBD":
                                print(f"✅ Found salary in API text: {salary_info}")
                                return salary_info
                                
                except requests.RequestException:
                    continue  # Try next endpoint
                    
            return None
            
        except Exception as e:
            print(f"Error trying API endpoints: {e}")
            return None
    
    @classmethod
    def _search_json_for_salary(cls, data, max_depth=3):
        """Recursively search JSON data for salary information"""
        if max_depth <= 0:
            return None
            
        try:
            if isinstance(data, dict):
                # Look for salary-related keys
                for key, value in data.items():
                    if any(salary_key in key.lower() for salary_key in ['salary', 'compensation', 'pay', 'wage', 'base']):
                        if isinstance(value, str):
                            extracted = cls.extract_salary(value)
                            if extracted and extracted != "TBD":
                                return extracted
                        elif isinstance(value, (dict, list)):
                            result = cls._search_json_for_salary(value, max_depth - 1)
                            if result:
                                return result
                
                # Recursively search nested objects
                for value in data.values():
                    if isinstance(value, (dict, list)):
                        result = cls._search_json_for_salary(value, max_depth - 1)
                        if result:
                            return result
                            
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, (dict, list)):
                        result = cls._search_json_for_salary(item, max_depth - 1)
                        if result:
                            return result
                            
        except Exception:
            pass
            
        return None
    
    @classmethod
    def extract_salary(cls, job_description: str) -> Optional[str]:
        """Extract salary information from job description"""
        if not job_description:
            return "TBD"
        
        # Clean HTML tags for text analysis
        clean_text = re.sub(r'<[^>]+>', '', job_description)
        clean_text = re.sub(r'\s+', ' ', clean_text)
        
        # Salary patterns - ordered from most specific to least specific
        salary_patterns = [
            # Specific ranges with K (e.g., "$120K - $180K", "$120k-$180k", "$120k to $180K")
            r'\$(\d{2,3})[kK]?\s*(?:[-–—]|to)\s*\$?(\d{2,3})[kK]\b',
            
            # Full numbers with commas (e.g., "$120,000 - $180,000", "$120,000 to $180,000")
            r'\$(\d{1,3}(?:,\d{3})+)\s*(?:[-–—]|to)\s*\$?(\d{1,3}(?:,\d{3})+)',
            
            # Mixed format (e.g., "$120,000 - $180K", "$120K to $180,000")
            r'\$(\d{1,3}(?:,\d{3})*)[kK]?\s*(?:[-–—]|to)\s*\$?(\d{1,3}(?:,\d{3})*)[kK]?',
            
            # Single salary with K (e.g., "up to $180K", "$150K+", "$120K base")
            r'(?:up to|base of|starting at|base salary|salary of)\s+\$(\d{2,3})[kK]\+?(?:\s+(?:base|annually|per year))?',
            r'\$(\d{2,3})[kK]\+?(?:\s+(?:base|annually|per year))',
            r'\$(\d{2,3})[kK]\b',
            
            # Single salary full format (e.g., "up to $180,000", "$300,000+")
            r'(?:up to|base of|starting at|base salary|salary of)\s+\$(\d{1,3}(?:,\d{3})+)\+?(?:\s+(?:base|annually|per year))?',
            r'\$(\d{1,3}(?:,\d{3})+)\+?(?:\s+(?:base|annually|per year))?',
            
            # Hourly rates (e.g., "$75/hour", "$50-$80/hr", "$65 per hour")
            r'\$(\d{2,3})\s*(?:/|\s+per\s+)(?:hour|hr)\b',
            r'\$(\d{2,3})\s*[-–—]\s*\$?(\d{2,3})\s*(?:/|\s+per\s+)(?:hour|hr)\b',
            
            # Alternative formats (e.g., "120-180k", "120k to 180k")
            r'(\d{2,3})[kK]?\s*(?:[-–—]|to)\s*(\d{2,3})[kK](?:\s+(?:annually|per year))?',
            
            # Equity mentions (capture for context)
            r'(\d+\.?\d*)%\s*(?:equity|stock|options)',
            
            # Compensation package mentions
            r'(?:total compensation|tc|package|total cash compensation):\s*\$?(\d{1,3}(?:[,k]\d{3})*)[k]?',
            
            # Estimated compensation patterns (common in job postings)
            r'(?:estimated|expected)\s+(?:total\s+)?(?:cash\s+)?compensation.*?\$(\d{1,3}(?:,\d{3})+)(?:\s*[-–—]\s*\$?(\d{1,3}(?:,\d{3})+))?',
        ]
        
        # Search for salary patterns
        for pattern in salary_patterns:
            matches = re.findall(pattern, clean_text, re.IGNORECASE)
            if matches:
                # Process the first match found
                match = matches[0]
                # Ensure match is always a tuple for consistent handling
                if isinstance(match, str):
                    match = (match,)
                salary_str = cls._format_salary_match(match, pattern)
                if salary_str:
                    return salary_str
        
        # Look for specific salary-related keywords in context
        salary_keywords = [
            'compensation', 'salary', 'pay', 'wage', 'remuneration', 
            'package', 'total comp', 'base pay', 'annual salary'
        ]
        
        for keyword in salary_keywords:
            # Look for keyword followed by salary information
            keyword_pattern = rf'{keyword}[:\s]+([^\n.!?]+)'
            keyword_matches = re.findall(keyword_pattern, clean_text, re.IGNORECASE)
            for keyword_match in keyword_matches:
                # Try to extract salary from the context
                context_salary = cls._extract_salary_from_context(keyword_match)
                if context_salary:
                    return context_salary
        
        return "TBD"
    
    @classmethod
    def _format_salary_match(cls, match: tuple, pattern: str) -> Optional[str]:
        """Format salary match into standardized string"""
        try:
            if len(match) == 2 and match[1]:  # Range format
                low, high = match
                # Handle different formats - check if pattern expects K values
                if '[kK]' in pattern:
                    # Pattern expects K values - check each value individually
                    low_val = cls._parse_salary_value(low + 'k' if not low.endswith('k') and not low.endswith('K') and ',' not in low else low)
                    high_val = cls._parse_salary_value(high + 'k' if not high.endswith('k') and not high.endswith('K') and ',' not in high else high)
                else:
                    # Pattern expects full numbers
                    low_val = cls._parse_salary_value(low)
                    high_val = cls._parse_salary_value(high)
                
                if low_val and high_val:
                    return f"${low_val:,} - ${high_val:,}"
            
            elif len(match) >= 1:  # Single value
                value = match[0]
                if '/hour' in pattern or '/hr' in pattern:
                    # Hourly rate
                    return f"${value}/hour"
                elif '%' in pattern:
                    # Equity
                    return f"{value}% equity"
                else:
                    # Annual salary - check if pattern expects K values
                    if '[kK]' in pattern:
                        # Pattern expects K values, so append 'k' for parsing
                        parsed_val = cls._parse_salary_value(value + 'k')
                    else:
                        # Pattern expects full numbers
                        parsed_val = cls._parse_salary_value(value)
                    
                    if parsed_val:
                        return f"${parsed_val:,}"
            
        except (ValueError, TypeError) as e:
            print(f"Error formatting salary match: {e}")
        
        return None
    
    @classmethod
    def _parse_salary_value(cls, value: str) -> Optional[int]:
        """Parse salary value string into integer"""
        if not value:
            return None
        
        # Remove non-numeric characters except K and commas
        cleaned = re.sub(r'[^\d,kK]', '', str(value))
        
        try:
            if cleaned.lower().endswith('k'):
                # Handle K values (e.g., "120k" -> 120000)
                num = int(cleaned[:-1].replace(',', ''))
                return num * 1000
            else:
                # Handle full numbers (e.g., "120,000" -> 120000)
                return int(cleaned.replace(',', ''))
        except ValueError:
            return None
    
    @classmethod
    def _extract_salary_from_context(cls, context: str) -> Optional[str]:
        """Extract salary from contextual text around salary keywords"""
        # Simple patterns for context extraction
        context_patterns = [
            r'\$(\d{2,3})[kK]\s*(?:[-–—]|to)\s*\$?(\d{2,3})[kK]',
            r'\$(\d{1,3}(?:,\d{3})+)\s*(?:[-–—]|to)\s*\$?(\d{1,3}(?:,\d{3})+)',
            r'\$(\d{2,3})[kK]',
            r'\$(\d{1,3}(?:,\d{3})+)',
        ]
        
        for pattern in context_patterns:
            matches = re.findall(pattern, context, re.IGNORECASE)
            if matches:
                match = matches[0]
                # Ensure match is always a tuple for consistent handling
                if isinstance(match, str):
                    match = (match,)
                formatted = cls._format_salary_match(match, pattern)
                if formatted:
                    return formatted
        
        return None

    @classmethod 
    def _is_spa_page(cls, html_content: str) -> bool:
        """Check if page is a Single Page Application that needs JavaScript rendering"""
        spa_indicators = [
            'id="__nuxt"',
            'id="__next"', 
            'data-reactroot',
            'ng-app',
            'data-ssr="false"',
            'vue-app'
        ]
        
        # Check if page has SPA indicators and minimal content
        has_spa_indicator = any(indicator in html_content for indicator in spa_indicators)
        
        if has_spa_indicator:
            # Check if body is essentially empty (less than 200 chars of actual text)
            soup = BeautifulSoup(html_content, 'html.parser')
            body = soup.find('body')
            if body:
                body_text = body.get_text().strip()
                if len(body_text) < 200:
                    return True
        
        return False
    
    @classmethod
    def _extract_from_url_path(cls, url: str) -> Optional[str]:
        """Extract position title from URL path for job boards"""
        try:
            from urllib.parse import urlparse, unquote
            
            parsed = urlparse(url)
            path = unquote(parsed.path)  # Decode URL encoding
            
            # Common job board URL patterns
            # e.g., /columbus-oh/senior-software-engineering-manager/ID/job/
            path_parts = [part for part in path.split('/') if part]
            
            for i, part in enumerate(path_parts):
                # Look for job title patterns in URL
                if any(keyword in part.lower() for keyword in ['manager', 'engineer', 'developer', 'analyst', 'director', 'lead']):
                    # Clean up the URL slug
                    cleaned = part.replace('-', ' ').title()
                    return cleaned
            
            return None
            
        except Exception:
            return None
    
    @classmethod
    def parse_job_posting(cls, job_description: str, url: str = None) -> Dict[str, Optional[str]]:
        """Main method to parse job posting and return extracted information"""
        company, position = cls.extract_from_content(job_description, url)
        
        # If position not found and we have a URL, try extracting from URL path
        if not position and url:
            # Check if this might be a SPA page
            if cls._is_spa_page(job_description):
                print(f"🔄 Detected SPA page, trying URL path extraction for: {url}")
                url_position = cls._extract_from_url_path(url)
                if url_position:
                    position = url_position
                    print(f"✅ Extracted position from URL path: {position}")
                else:
                    print(f"❌ Could not extract position from URL path")
        
        # Extract salary information
        salary = cls.extract_salary(job_description)
        
        # If salary not found and this is a SPA page, try SPA-specific extraction
        if salary == "TBD" and cls._is_spa_page(job_description) and url:
            print(f"🔄 SPA page detected, trying advanced salary extraction...")
            spa_salary = cls._extract_salary_from_spa(job_description, url)
            if spa_salary:
                salary = spa_salary
                print(f"✅ Found salary in SPA data: {salary}")
            else:
                print(f"❌ No salary found in SPA data")
        
        # Auto-select resume template based on position
        suggested_template = cls.select_resume_template(position) if position else None
        template_source = 'auto-detected' if suggested_template else 'none'
        
        confidence = 'high' if (company and position) else 'medium' if (company or position) else 'low'
        if cls._is_spa_page(job_description):
            # Lower confidence for SPA pages since we can't fully parse content
            confidence = 'medium' if confidence == 'high' else 'low'
        
        return {
            'company_name': company,
            'position_title': position,
            'salary': salary,
            'suggested_template': suggested_template,
            'template_source': template_source,
            'confidence': confidence
        }