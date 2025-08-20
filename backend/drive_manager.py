"""Google Drive integration for Resume Automation System"""

import os
import io
import time
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.http import BatchHttpRequest

from backend.config_manager import get_config


class DriveManager:
    """Manages Google Drive API operations for resume automation"""
    
    # Required scopes for Drive and Docs access
    SCOPES = [
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/documents'
    ]
    
    def __init__(self):
        self.config = get_config()
        self.drive_service = None
        self.docs_service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate using service account credentials"""
        try:
            service_account_file = self.config.get('google_drive.service_account_file')
            
            if not os.path.exists(service_account_file):
                raise FileNotFoundError(
                    f"Service account file not found: {service_account_file}. "
                    "Please download your service account JSON file from Google Cloud Console."
                )
            
            creds = service_account.Credentials.from_service_account_file(
                service_account_file, 
                scopes=self.SCOPES
            )
            
            self.drive_service = build('drive', 'v3', credentials=creds)
            self.docs_service = build('docs', 'v1', credentials=creds)
            
        except Exception as e:
            raise Exception(f"Failed to authenticate with Google Drive: {str(e)}")
    
    def _handle_api_errors(self, func, *args, **kwargs):
        """Handle API errors with exponential backoff"""
        max_retries = self.config.get('system.max_retries', 5)
        base_delay = self.config.get('system.rate_limit_delay', 1.0)
        
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except HttpError as error:
                if error.resp.status == 429:  # Rate limit exceeded (429 only)
                    if attempt == max_retries - 1:
                        raise error
                    
                    delay = base_delay * (2 ** attempt)
                    print(f"Rate limit hit. Waiting {delay} seconds... (attempt {attempt + 1})")
                    time.sleep(delay)
                elif error.resp.status == 403:  # Permission denied - don't retry
                    print(f"Permission denied (403): {error}")
                    raise error
                else:
                    raise error
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                time.sleep(base_delay)
    
    def list_template_files(self) -> List[Dict[str, str]]:
        """List all Google Docs in the templates folder"""
        try:
            templates_folder_id = self.config.get('google_drive.templates_folder_id')
            
            query = (
                f"'{templates_folder_id}' in parents and "
                "mimeType='application/vnd.google-apps.document' and "
                "trashed=false"
            )
            
            def _list_files():
                return self.drive_service.files().list(
                    q=query,
                    fields="nextPageToken, files(id, name, mimeType, modifiedTime)",
                    pageSize=100
                ).execute()
            
            results = self._handle_api_errors(_list_files)
            return results.get('files', [])
            
        except Exception as e:
            print(f"Error listing template files: {str(e)}")
            return []
    
    def find_template_by_name(self, template_name: str) -> Optional[str]:
        """Find template file ID by name"""
        templates = self.list_template_files()
        
        # First try exact match
        for template in templates:
            if template['name'].lower() == template_name.lower():
                return template['id']
        
        # Then try partial match (template_name contains part of document name)
        for template in templates:
            if template_name.lower() in template['name'].lower():
                return template['id']
        
        # Finally try reverse match (document name contains part of template_name)
        for template in templates:
            if template['name'].lower() in template_name.lower():
                return template['id']
        
        print(f"Template not found: '{template_name}'")
        print(f"Available templates: {[t['name'] for t in templates]}")
        return None
    
    def create_job_folder(self, company_name: str, position_title: str) -> str:
        """Create folder structure for job application"""
        try:
            output_folder_id = self.config.get('google_drive.output_folder_id')
            folder_structure = self.config.get('file_organization.folder_structure')
            
            # Format folder name
            folder_name = folder_structure.format(
                company_name=company_name,
                position_title=position_title
            ).strip('/')
            
            # Check if folder already exists
            existing_folder = self._find_folder_by_name(folder_name, output_folder_id)
            if existing_folder:
                return existing_folder
            
            # Create new folder
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [output_folder_id]
            }
            
            def _create_folder():
                return self.drive_service.files().create(
                    body=folder_metadata,
                    fields='id, name'
                ).execute()
            
            folder = self._handle_api_errors(_create_folder)
            return folder.get('id')
            
        except Exception as e:
            print(f"Error creating job folder: {str(e)}")
            return output_folder_id  # Fallback to main output folder
    
    def _find_folder_by_name(self, folder_name: str, parent_id: str) -> Optional[str]:
        """Find folder by name within parent folder"""
        try:
            query = (
                f"'{parent_id}' in parents and "
                f"name='{folder_name}' and "
                "mimeType='application/vnd.google-apps.folder' and "
                "trashed=false"
            )
            
            def _search_folder():
                return self.drive_service.files().list(
                    q=query,
                    fields="files(id)"
                ).execute()
            
            results = self._handle_api_errors(_search_folder)
            files = results.get('files', [])
            
            return files[0]['id'] if files else None
            
        except Exception as e:
            print(f"Error finding folder: {str(e)}")
            return None
    
    def get_document_content(self, document_id: str) -> Optional[str]:
        """Get the text content of a Google Doc"""
        try:
            def _get_doc():
                return self.docs_service.documents().get(documentId=document_id).execute()
            
            document = self._handle_api_errors(_get_doc)
            
            # Extract text content from document structure
            content = ""
            doc_content = document.get('body', {}).get('content', [])
            
            for element in doc_content:
                if 'paragraph' in element:
                    paragraph = element['paragraph']
                    for content_element in paragraph.get('elements', []):
                        if 'textRun' in content_element:
                            content += content_element['textRun'].get('content', '')
            
            return content.strip()
            
        except Exception as e:
            print(f"Error getting document content: {str(e)}")
            return None
    
    def copy_template(self, template_id: str, new_name: str, destination_folder_id: str) -> Optional[str]:
        """Copy template document to destination folder"""
        try:
            copy_metadata = {
                'name': new_name,
                'parents': [destination_folder_id]
            }
            
            def _copy_file():
                return self.drive_service.files().copy(
                    fileId=template_id,
                    body=copy_metadata,
                    fields='id, name, webViewLink'
                ).execute()
            
            copied_file = self._handle_api_errors(_copy_file)
            return copied_file.get('id')
            
        except Exception as e:
            print(f"Error copying template: {str(e)}")
            return None
    
    def create_document(self, title: str, folder_id: str) -> Optional[str]:
        """Create a new Google Doc in the specified folder"""
        try:
            # Create the document
            def _create_doc():
                return self.docs_service.documents().create(
                    body={'title': title}
                ).execute()
            
            document = self._handle_api_errors(_create_doc)
            doc_id = document.get('documentId')
            
            # Move to specified folder
            if doc_id and folder_id:
                def _move_file():
                    return self.drive_service.files().update(
                        fileId=doc_id,
                        addParents=folder_id,
                        removeParents='root'
                    ).execute()
                
                self._handle_api_errors(_move_file)
            
            return doc_id
            
        except Exception as e:
            print(f"Error creating document: {str(e)}")
            # Fallback: create a plain text file instead
            return self._create_text_file(title, folder_id)
    
    def _create_text_file(self, title: str, folder_id: str) -> Optional[str]:
        """Fallback: Create a plain text file instead of Google Doc"""
        try:
            from googleapiclient.http import MediaIoBaseUpload
            import io
            
            # Create empty text content
            content = f"# {title}\n\n[Content will be updated after creation]"
            media = MediaIoBaseUpload(
                io.BytesIO(content.encode('utf-8')),
                mimetype='text/plain'
            )
            
            file_metadata = {
                'name': f"{title}.txt",
                'parents': [folder_id]
            }
            
            def _create_file():
                return self.drive_service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id'
                ).execute()
            
            file_result = self._handle_api_errors(_create_file)
            return file_result.get('id')
            
        except Exception as e:
            print(f"Error creating text file fallback: {str(e)}")
            return None
    
    def update_document_content(self, document_id: str, content: str) -> bool:
        """Update document content by replacing all text"""
        try:
            # First, get the document to find its length
            def _get_doc():
                return self.docs_service.documents().get(documentId=document_id).execute()
            
            document = self._handle_api_errors(_get_doc)
            
            # Calculate the end index (length of document content)
            doc_content = document.get('body', {}).get('content', [])
            end_index = 1  # Start at 1 (Google Docs default)
            
            for element in doc_content:
                if 'paragraph' in element:
                    for content_element in element['paragraph'].get('elements', []):
                        if 'textRun' in content_element:
                            text_run = content_element['textRun']
                            if 'content' in text_run:
                                end_index += len(text_run['content'])
            
            # Replace all content
            requests = [
                {
                    'deleteContentRange': {
                        'range': {
                            'startIndex': 1,
                            'endIndex': end_index
                        }
                    }
                },
                {
                    'insertText': {
                        'location': {
                            'index': 1
                        },
                        'text': content
                    }
                }
            ]
            
            def _batch_update():
                return self.docs_service.documents().batchUpdate(
                    documentId=document_id,
                    body={'requests': requests}
                ).execute()
            
            self._handle_api_errors(_batch_update)
            return True
            
        except Exception as e:
            print(f"Error updating document content: {str(e)}")
            return False
    
    def export_as_pdf(self, file_id: str, output_path: str) -> bool:
        """Export Google Doc as PDF"""
        try:
            def _export_pdf():
                return self.drive_service.files().export_media(
                    fileId=file_id,
                    mimeType='application/pdf'
                ).execute()
            
            pdf_content = self._handle_api_errors(_export_pdf)
            
            # Ensure output directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Write PDF content to file
            with open(output_path, 'wb') as f:
                f.write(pdf_content)
            
            return True
            
        except Exception as e:
            print(f"Error exporting PDF: {str(e)}")
            return False
    
    def get_document_link(self, file_id: str) -> str:
        """Get shareable link to Google Doc"""
        return f"https://docs.google.com/document/d/{file_id}/edit"
    
    def create_resume_package(self, template_type: str, company_name: str, 
                            position_title: str, resume_content: str, 
                            cover_letter_content: str) -> Dict[str, str]:
        """Create complete resume package with resume and cover letter (using copy method for service account compatibility)"""
        try:
            # Use copy-based approach since service accounts can't create new documents
            return self._create_resume_package_by_copy(template_type, company_name, position_title, resume_content, cover_letter_content)
        except Exception as e:
            print(f"Error in create_resume_package: {str(e)}")
            return {}
    
    def _create_resume_package_by_copy(self, template_type: str, company_name: str, 
                                     position_title: str, resume_content: str, 
                                     cover_letter_content: str) -> Dict[str, str]:
        """Create resume package by copying templates (workaround for service account limitations)"""
        try:
            # Get template mapping
            template_mapping = self.config.get_template_mapping()
            template_name = template_mapping.get(template_type)
            
            if not template_name:
                raise ValueError(f"Unknown template type: {template_type}")
            
            # Find template file
            template_id = self.find_template_by_name(template_name)
            if not template_id:
                raise ValueError(f"Template not found: {template_name}")
            
            # Create job folder
            job_folder_id = self.create_job_folder(company_name, position_title)
            
            # Generate file names
            file_config = self.config.get_file_organization_config()
            resume_name = file_config.get('resume_filename', 'Resume').format(
                company_name=company_name,
                position_title=position_title
            )
            cover_letter_name = file_config.get('cover_letter_filename', 'Cover Letter').format(
                company_name=company_name,
                position_title=position_title
            )
            
            results = {}
            
            # Create resume
            resume_id = self.copy_template(template_id, resume_name, job_folder_id)
            if resume_id:
                if self.update_document_content(resume_id, resume_content):
                    results['resume_id'] = resume_id
                    results['resume_link'] = self.get_document_link(resume_id)
                    
                    # Generate PDF if configured
                    if file_config.get('generate_pdf', True):
                        pdf_path = f"output/{resume_name}.pdf"
                        if self.export_as_pdf(resume_id, pdf_path):
                            results['resume_pdf_path'] = pdf_path
            
            # Create cover letter by copying template
            cover_letter_template_id = self.config.get('google_drive.cover_letter_template_id')
            if cover_letter_template_id:
                cover_letter_id = self.copy_template(cover_letter_template_id, cover_letter_name, job_folder_id)
                if cover_letter_id:
                    if self.update_document_content(cover_letter_id, cover_letter_content):
                        results['cover_letter_id'] = cover_letter_id
                        results['cover_letter_link'] = self.get_document_link(cover_letter_id)
                        
                        # Generate PDF if configured
                        if file_config.get('generate_pdf', True):
                            pdf_path = f"output/{cover_letter_name}.pdf"
                            if self.export_as_pdf(cover_letter_id, pdf_path):
                                results['cover_letter_pdf_path'] = pdf_path
                else:
                    print(f"Failed to copy cover letter template: {cover_letter_template_id}")
            else:
                print("No cover letter template configured")
            
            results['folder_id'] = job_folder_id
            return results
            
        except Exception as e:
            print(f"Error creating resume package: {str(e)}")
            return {}
    
    def test_connection(self) -> bool:
        """Test Google Drive API connection"""
        try:
            def _test():
                return self.drive_service.about().get(fields="user").execute()
            
            result = self._handle_api_errors(_test)
            return bool(result)
            
        except Exception as e:
            print(f"Drive connection test failed: {str(e)}")
            return False