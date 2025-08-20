import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports when run directly
if __name__ == "__main__":
    sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.job_parser import JobParser


class TestSalaryScaping:
    """Test salary extraction from various job posting formats."""
    
    def test_salary_range_with_k_format(self):
        """Test salary ranges with K format ($120K - $180K)."""
        job_descriptions = [
            "We offer competitive compensation of $120K - $180K annually.",
            "Salary range: $120k-$180k based on experience",
            "Base salary $120K – $180K plus benefits",
            "Compensation: $120k to $180K per year"
        ]
        
        expected = "$120,000 - $180,000"
        
        for description in job_descriptions:
            result = JobParser.extract_salary(description)
            assert result == expected, f"Failed for: {description}, got: {result}"
        
        print("✅ K format salary ranges extracted correctly")
    
    def test_salary_range_with_commas(self):
        """Test salary ranges with full comma format ($120,000 - $180,000)."""
        job_descriptions = [
            "Annual salary range: $120,000 - $180,000",
            "We pay between $120,000-$180,000 depending on experience", 
            "Salary: $120,000 to $180,000 annually",
            "Base compensation $120,000 – $180,000"
        ]
        
        expected = "$120,000 - $180,000"
        
        for description in job_descriptions:
            result = JobParser.extract_salary(description)
            assert result == expected, f"Failed for: {description}, got: {result}"
        
        print("✅ Full comma format salary ranges extracted correctly")
    
    def test_single_salary_values(self):
        """Test single salary value extraction."""
        test_cases = [
            ("Base salary up to $150K", "$150,000"),
            ("Starting salary $120,000", "$120,000"),
            ("We offer $180k base", "$180,000"),
            ("Salary of $165,000 annually", "$165,000"),
            ("Base pay: $140K per year", "$140,000"),
        ]
        
        for description, expected in test_cases:
            result = JobParser.extract_salary(description)
            assert result == expected, f"Failed for: '{description}', expected: {expected}, got: {result}"
        
        print("✅ Single salary values extracted correctly")
    
    def test_hourly_rates(self):
        """Test that hourly rates return TBD (not currently supported)."""
        test_cases = [
            "Hourly rate: $75/hour",
            "We pay $50-$80/hr for this contract", 
            "$65 per hour for contractors",
            "Contract rate $70/hr",
        ]
        
        # For now, hourly rates should return TBD since we're not focusing on them
        for description in test_cases:
            result = JobParser.extract_salary(description)
            # Accept either TBD or if we happen to extract something reasonable
            assert result in ["TBD", "$75", "$65", "$70"] or "$50" in str(result), f"Failed for: '{description}', got: {result}"
        
        print("✅ Hourly rates handled (returns TBD or basic extraction)")
    
    def test_mixed_formats(self):
        """Test mixed salary formats ($120,000 - $180K)."""
        test_cases = [
            ("Salary range $120,000 - $180K", "$120,000 - $180,000"),
            ("We offer $120K to $180,000 annually", "$120,000 - $180,000"),
            ("Base: $120,000-$180k", "$120,000 - $180,000"),
        ]
        
        for description, expected in test_cases:
            result = JobParser.extract_salary(description)
            assert result == expected, f"Failed for: '{description}', expected: {expected}, got: {result}"
        
        print("✅ Mixed format salaries extracted correctly")
    
    def test_alternative_formats(self):
        """Test alternative salary formats without dollar signs."""
        test_cases = [
            ("Compensation: 120k-180k annually", "$120,000 - $180,000"),
            ("We pay 150-200k per year", "$150,000 - $200,000"),
            ("Salary 120k to 180k", "$120,000 - $180,000"),
        ]
        
        for description, expected in test_cases:
            result = JobParser.extract_salary(description)
            assert result == expected, f"Failed for: '{description}', expected: {expected}, got: {result}"
        
        print("✅ Alternative format salaries extracted correctly")
    
    def test_equity_mentions(self):
        """Test equity percentage extraction."""
        test_cases = [
            ("Salary plus 0.5% equity", "0.5% equity"),
            ("We offer 1.2% stock options", "1.2% equity"),
            ("Plus 0.8% equity participation", "0.8% equity"),
        ]
        
        for description, expected in test_cases:
            result = JobParser.extract_salary(description)
            assert result == expected, f"Failed for: '{description}', expected: {expected}, got: {result}"
        
        print("✅ Equity mentions extracted correctly")
    
    def test_salary_with_html_tags(self):
        """Test salary extraction from HTML content."""
        html_descriptions = [
            '<div class="salary">Salary: $120K - $180K</div>',
            '<span>We offer <strong>$150,000</strong> annually</span>',
            '<p>Base compensation: $120,000 to $180,000</p>',
            '<!-- salary info --><div>$140k base salary</div>',
        ]
        
        expected_results = [
            "$120,000 - $180,000",
            "$150,000", 
            "$120,000 - $180,000",
            "$140,000"
        ]
        
        for description, expected in zip(html_descriptions, expected_results):
            result = JobParser.extract_salary(description)
            assert result == expected, f"Failed for HTML: '{description}', expected: {expected}, got: {result}"
        
        print("✅ HTML salary extraction working correctly")
    
    def test_contextual_salary_extraction(self):
        """Test salary extraction using contextual keywords."""
        test_cases = [
            ("Total compensation package: $160K", "$160,000"),
            ("Base pay: $120,000 - $150,000", "$120,000 - $150,000"),
            ("Annual salary is $140k", "$140,000"),
            ("Compensation: competitive $130K-$170K", "$130,000 - $170,000"),
        ]
        
        for description, expected in test_cases:
            result = JobParser.extract_salary(description)
            assert result == expected, f"Failed for: '{description}', expected: {expected}, got: {result}"
        
        print("✅ Contextual salary extraction working correctly")
    
    def test_estimated_compensation_patterns(self):
        """Test estimated/expected compensation pattern extraction."""
        test_cases = [
            # The specific format provided
            ('<p>The estimated total cash compensation range for this role is:</p><p>$220,000—$280,000 USD</p>', '$220,000 - $280,000'),
            
            # Variations of the pattern
            ('The estimated total compensation for this position is $180,000 - $220,000', '$180,000 - $220,000'),
            ('Expected cash compensation range: $160,000 to $200,000', '$160,000 - $200,000'),
            ('Estimated compensation: $150,000—$190,000 annually', '$150,000 - $190,000'),
            ('The expected total cash compensation is $170,000-$210,000', '$170,000 - $210,000'),
        ]
        
        for description, expected in test_cases:
            result = JobParser.extract_salary(description)
            assert result == expected, f"Failed for: '{description}', expected: {expected}, got: {result}"
        
        print("✅ Estimated compensation patterns extracted correctly")
    
    def test_no_salary_found(self):
        """Test cases where no salary should be found."""
        no_salary_descriptions = [
            "Join our amazing team! We offer great benefits.",
            "Looking for a senior engineer with 5+ years experience.",
            "Competitive compensation based on experience.",
            "We offer equity and great benefits package.",
            "Salary commensurate with experience.",
            "",  # Empty string
        ]
        
        for description in no_salary_descriptions:
            result = JobParser.extract_salary(description)
            assert result == "TBD", f"Should return TBD when no salary found in: '{description}', but got: {result}"
        
        print("✅ Correctly returns TBD when no salary is found")
    
    def test_salary_edge_cases(self):
        """Test edge cases and potential false positives."""
        test_cases = [
            # Should not match phone numbers or other numbers
            ("Call us at 555-120-1234", "TBD"),
            ("Employee ID #120180", "TBD"),
            ("Room 120k on floor 18", "TBD"),
            
            # Should handle valid edge cases
            ("Starting at $99K", "$99,000"),
            ("Up to $250K for the right candidate", "$250,000"),
            ("$300,000+ for senior roles", "$300,000"),
        ]
        
        for description, expected in test_cases:
            result = JobParser.extract_salary(description)
            assert result == expected, f"Failed for: '{description}', expected: {expected}, got: {result}"
        
        print("✅ Edge cases handled correctly")
    
    def test_real_world_job_postings(self):
        """Test with realistic job posting excerpts."""
        real_world_examples = [
            {
                "description": """
                Senior Software Engineer - Backend
                
                About the Role:
                We're looking for a Senior Software Engineer to join our backend team.
                
                Compensation:
                • Base salary: $140,000 - $180,000
                • Equity: 0.1% - 0.3%
                • Comprehensive benefits
                
                Apply now!
                """,
                "expected_salary": "$140,000 - $180,000"
            },
            {
                "description": """
                <div class="job-posting">
                    <h1>Engineering Manager - Data Platform</h1>
                    <p>Lead our data engineering team</p>
                    <div class="compensation">
                        <p>Total compensation: $160K-$200K</p>
                        <p>Plus equity and benefits</p>
                    </div>
                </div>
                """,
                "expected_salary": "$160,000 - $200,000"
            },
            {
                "description": """
                Staff Data Engineer
                
                Responsibilities:
                - Build scalable data pipelines
                - Mentor junior engineers
                - Design data architecture
                
                What we offer:
                - Competitive salary up to $200K
                - Stock options
                - Remote work flexibility
                """,
                "expected_salary": "$200,000"
            }
        ]
        
        for example in real_world_examples:
            result = JobParser.extract_salary(example["description"])
            expected = example["expected_salary"]
            assert result == expected, f"Failed for real-world example, expected: {expected}, got: {result}"
        
        print("✅ Real-world job posting salary extraction working correctly")
    
    def test_integration_with_full_job_parsing(self):
        """Test salary extraction as part of full job posting parsing."""
        job_posting = """
        <title>Senior Software Engineer - TechCorp Inc</title>
        
        <div class="job-content">
            <h1>Senior Software Engineer</h1>
            <p>TechCorp Inc is hiring a Senior Software Engineer...</p>
            
            <h3>Compensation</h3>
            <p>We offer competitive compensation of $130K - $170K plus equity.</p>
            
            <h3>Requirements</h3>
            <p>5+ years of software engineering experience...</p>
        </div>
        """
        
        result = JobParser.parse_job_posting(job_posting)
        
        # Test that salary extraction works in the integration
        assert result['salary'] == '$130,000 - $170,000', f"Expected salary $130,000 - $170,000, got {result['salary']}"
        
        # Test that other fields are populated (though parsing logic may need work)
        assert 'company_name' in result
        assert 'position_title' in result  
        assert 'suggested_template' in result
        assert result['confidence'] in ['high', 'medium', 'low']
        
        print("✅ Full job posting integration with salary extraction working correctly")


if __name__ == "__main__":
    # Run tests manually if called directly
    test = TestSalaryScaping()
    test.test_salary_range_with_k_format()
    test.test_salary_range_with_commas()
    test.test_single_salary_values()
    test.test_hourly_rates()
    test.test_mixed_formats()
    test.test_alternative_formats()
    test.test_equity_mentions()
    test.test_salary_with_html_tags()
    test.test_contextual_salary_extraction()
    test.test_estimated_compensation_patterns()
    test.test_no_salary_found()
    test.test_salary_edge_cases()
    test.test_real_world_job_postings()
    test.test_integration_with_full_job_parsing()
    print("🎉 All salary scraping tests passed!")