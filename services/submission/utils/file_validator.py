"""
File validator for uploaded data files
Validates file structure, headers, and data types

Author: TUS Development Team
"""

import logging
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)


class FileValidator:
    """
    Validates uploaded files against templates and rules
    """
    
    def __init__(self):
        """Initialize file validator"""
        self.required_headers = ['submission_date', 'department', 'category']
    
    def validate_file(self, file_path, file_extension, template=None):
        """
        Validate uploaded file structure and content
        
        Args:
            file_path (str): Path to the uploaded file
            file_extension (str): File extension (xlsx, csv, tsv)
            template (UploadTemplate): Optional template for validation
        
        Returns:
            dict: Validation result with 'valid' boolean and error message
        """
        try:
            # Read file based on extension
            df = self._read_file(file_path, file_extension)
            
            if df is None or df.empty:
                return {
                    'valid': False,
                    'error': 'File is empty or could not be read'
                }
            
            # Validate headers
            header_validation = self._validate_headers(df, template)
            if not header_validation['valid']:
                return header_validation
            
            # Validate data types and content
            content_validation = self._validate_content(df, template)
            if not content_validation['valid']:
                return content_validation
            
            # Check row count
            if len(df) == 0:
                return {
                    'valid': False,
                    'error': 'File contains no data rows'
                }
            
            if len(df) > 10000:  # Configurable limit
                return {
                    'valid': False,
                    'error': f'File contains too many rows ({len(df)}). Maximum allowed: 10000'
                }
            
            logger.info(f"File validation successful: {len(df)} rows")
            
            return {
                'valid': True,
                'rows': len(df),
                'columns': list(df.columns)
            }
            
        except Exception as e:
            logger.error(f"Error validating file: {str(e)}")
            return {
                'valid': False,
                'error': f'Validation error: {str(e)}'
            }
    
    def _read_file(self, file_path, file_extension):
        """
        Read file into pandas DataFrame
        
        Args:
            file_path (str): Path to file
            file_extension (str): File extension
        
        Returns:
            pd.DataFrame: Loaded data or None
        """
        try:
            if file_extension in ['xlsx', 'xls']:
                df = pd.read_excel(file_path, engine='openpyxl' if file_extension == 'xlsx' else 'xlrd')
            elif file_extension == 'csv':
                df = pd.read_csv(file_path)
            elif file_extension == 'tsv':
                df = pd.read_csv(file_path, sep='\t')
            else:
                return None
            
            # Clean column names (strip whitespace)
            df.columns = df.columns.str.strip()
            
            return df
            
        except Exception as e:
            logger.error(f"Error reading file: {str(e)}")
            return None
    
    def _validate_headers(self, df, template):
        """
        Validate file headers against required fields and template
        
        Args:
            df (pd.DataFrame): Data to validate
            template (UploadTemplate): Optional template
        
        Returns:
            dict: Validation result
        """
        file_headers = set(df.columns)
        
        if template:
            # Validate against template headers
            template_headers = set(template.headers)
            
            missing_headers = template_headers - file_headers
            if missing_headers:
                return {
                    'valid': False,
                    'error': f'Missing required headers: {", ".join(missing_headers)}'
                }
            
            extra_headers = file_headers - template_headers
            if extra_headers:
                logger.warning(f'Extra headers found: {", ".join(extra_headers)}')
        
        else:
            # Validate against minimum required headers
            required = set(self.required_headers)
            missing = required - file_headers
            
            if missing:
                return {
                    'valid': False,
                    'error': f'Missing required headers: {", ".join(missing)}'
                }
        
        return {'valid': True}
    
    def _validate_content(self, df, template):
        """
        Validate data content and types
        
        Args:
            df (pd.DataFrame): Data to validate
            template (UploadTemplate): Optional template
        
        Returns:
            dict: Validation result
        """
        errors = []
        
        # Check for required field data
        for header in self.required_headers:
            if header in df.columns:
                # Count missing values
                missing_count = df[header].isna().sum()
                if missing_count > 0:
                    errors.append(f'{header}: {missing_count} missing values')
        
        # Validate date format if submission_date exists
        if 'submission_date' in df.columns:
            try:
                pd.to_datetime(df['submission_date'], errors='coerce')
            except Exception:
                errors.append('submission_date: Invalid date format')
        
        if errors:
            return {
                'valid': False,
                'error': 'Content validation failed: ' + '; '.join(errors)
            }
        
        return {'valid': True}
