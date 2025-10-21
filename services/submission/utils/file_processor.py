"""
File processor for parsing and storing uploaded data
Processes validated files and inserts data into database

Author: TUS Development Team
"""

import logging
import pandas as pd
from datetime import datetime
from database.submission_models import EngagementData

logger = logging.getLogger(__name__)


class FileProcessor:
    """
    Processes uploaded files and stores data in database
    """
    
    def __init__(self):
        """Initialize file processor"""
        pass
    
    def process_file(self, file_path, file_extension, file_id, db_session):
        """
        Process file and insert data into database
        
        Args:
            file_path (str): Path to the file
            file_extension (str): File extension
            file_id (UUID): ID of the uploaded file record
            db_session: Database session
        
        Returns:
            dict: Processing results with row counts
        """
        try:
            # Read file
            df = self._read_file(file_path, file_extension)
            
            if df is None:
                raise Exception("Failed to read file")
            
            rows_processed = 0
            rows_failed = 0
            error_details = []
            
            # Process each row
            for idx, row in df.iterrows():
                try:
                    # Extract core fields
                    submission_date = self._parse_date(row.get('submission_date'))
                    department = str(row.get('department', '')).strip() if pd.notna(row.get('department')) else None
                    category = str(row.get('category', '')).strip() if pd.notna(row.get('category')) else None
                    
                    # Build data_fields JSONB - include all columns
                    data_fields = {}
                    for col in df.columns:
                        value = row[col]
                        # Convert pandas/numpy types to Python types
                        if pd.isna(value):
                            data_fields[col] = None
                        elif isinstance(value, (pd.Timestamp, datetime)):
                            data_fields[col] = value.isoformat()
                        elif isinstance(value, (int, float, bool)):
                            data_fields[col] = value
                        else:
                            data_fields[col] = str(value)
                    
                    # Create engagement data record
                    engagement_record = EngagementData(
                        file_id=file_id,
                        row_number=idx + 2,  # +2 because idx starts at 0 and we skip header
                        submission_date=submission_date,
                        department=department,
                        category=category,
                        data_fields=data_fields
                    )
                    
                    db_session.add(engagement_record)
                    rows_processed += 1
                    
                    # Commit in batches for better performance
                    if rows_processed % 100 == 0:
                        db_session.commit()
                        logger.debug(f"Processed {rows_processed} rows")
                    
                except Exception as e:
                    rows_failed += 1
                    error_msg = f"Row {idx + 2}: {str(e)}"
                    error_details.append(error_msg)
                    logger.error(error_msg)
                    
                    # Don't fail entire import for individual row errors
                    continue
            
            # Final commit
            db_session.commit()
            
            logger.info(f"File processing completed: {rows_processed} rows processed, {rows_failed} rows failed")
            
            return {
                'rows_processed': rows_processed,
                'rows_failed': rows_failed,
                'total_rows': len(df),
                'notes': f'{len(error_details)} errors encountered' if error_details else 'All rows processed successfully'
            }
            
        except Exception as e:
            logger.error(f"Error processing file: {str(e)}")
            db_session.rollback()
            raise
    
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
            
            # Clean column names
            df.columns = df.columns.str.strip()
            
            return df
            
        except Exception as e:
            logger.error(f"Error reading file: {str(e)}")
            return None
    
    def _parse_date(self, date_value):
        """
        Parse date value into datetime.date object
        
        Args:
            date_value: Date value in various formats
        
        Returns:
            datetime.date: Parsed date or None
        """
        if pd.isna(date_value):
            return None
        
        try:
            if isinstance(date_value, datetime):
                return date_value.date()
            elif isinstance(date_value, pd.Timestamp):
                return date_value.date()
            else:
                # Try to parse string
                parsed = pd.to_datetime(date_value, errors='coerce')
                if pd.notna(parsed):
                    return parsed.date()
                return None
        except Exception:
            return None
