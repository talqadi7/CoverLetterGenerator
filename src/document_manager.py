import os
import logging
import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO)

class DocumentManager:
    """
    Class to handle document management operations
    """
    def __init__(self):
        self.data_dir = "Data"
        os.makedirs(self.data_dir, exist_ok=True)
        
    def get_documents(self):
        """
        Get all documents organized by type
        """
        resumes = []
        cover_letters = []
        other_documents = []
        
        # Make sure directory exists
        if not os.path.exists(self.data_dir):
            return resumes, cover_letters, other_documents
            
        for filename in os.listdir(self.data_dir):
            file_path = os.path.join(self.data_dir, filename)
            
            if not os.path.isfile(file_path):
                continue
            
            # Get file stats
            stats = os.stat(file_path)
            
            # Create document info
            doc_info = {
                'id': filename,  # Using filename as ID for simplicity
                'filename': filename,
                'file_size': self._format_file_size(stats.st_size),
                'upload_date': self._format_date(stats.st_mtime),
                'path': file_path
            }
            
            # Categorize by prefix
            if filename.startswith('resume'):
                resumes.append(doc_info)
            elif filename.startswith('cover_letter'):
                cover_letters.append(doc_info)
            else:
                other_documents.append(doc_info)
                
        return resumes, cover_letters, other_documents
    
    def get_document_by_id(self, document_id):
        """
        Get a document by its ID
        """
        file_path = os.path.join(self.data_dir, document_id)
        if not os.path.exists(file_path):
            return None
            
        stats = os.stat(file_path)
        
        return {
            'id': document_id,
            'filename': document_id,
            'file_size': self._format_file_size(stats.st_size),
            'upload_date': self._format_date(stats.st_mtime),
            'path': file_path
        }
    
    def delete_document(self, document_id):
        """
        Delete a document by its ID
        """
        file_path = os.path.join(self.data_dir, document_id)
        if not os.path.exists(file_path):
            return False
            
        try:
            os.remove(file_path)
            return True
        except Exception as e:
            logging.error(f"Error deleting document {document_id}: {e}")
            return False
    
    def _format_file_size(self, size_bytes):
        """
        Format file size in bytes to human-readable format
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def _format_date(self, timestamp):
        """
        Format timestamp to human-readable date
        """
        dt = datetime.datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")