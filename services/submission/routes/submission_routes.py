"""
Data submission routes for file upload and processing
Handles secure file uploads with validation

Author: TUS Development Team
"""

import os
import logging
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from database.db_connection import db_session
from database.submission_models import (
    User, UploadedFile, EngagementData, 
    UploadTemplate, AuditLog, UploadStatus
)
from utils.file_validator import FileValidator
from utils.file_processor import FileProcessor
from utils.auth_decorators import role_required
from config.submission_config import Config

# Initialize blueprint and logger
submission_bp = Blueprint('submission', __name__)
logger = logging.getLogger(__name__)

# Initialize validators and processors
file_validator = FileValidator()
file_processor = FileProcessor()


def allowed_file(filename):
    """
    Check if file extension is allowed
    
    Args:
        filename (str): Name of the file
        
    Returns:
        bool: True if file extension is allowed
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


@submission_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_file():
    """
    Upload and process data file
    
    Accepts: Excel (.xlsx, .xls), CSV, TSV files
    
    Form Data:
        file: File upload
        template_id (optional): Template ID for validation
    
    Returns:
        JSON response with upload status and processing results
    """
    try:
        current_user_id = get_jwt_identity()
        
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                'error': f'File type not allowed. Allowed types: {", ".join(Config.ALLOWED_EXTENSIONS)}'
            }), 400
        
        # Secure the filename
        original_filename = secure_filename(file.filename)
        file_extension = original_filename.rsplit('.', 1)[1].lower()
        stored_filename = f"{uuid.uuid4()}.{file_extension}"
        
        # Save file temporarily
        upload_path = os.path.join(Config.UPLOAD_FOLDER, stored_filename)
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        file.save(upload_path)
        
        # Get file size
        file_size = os.path.getsize(upload_path)
        
        # Create upload record
        uploaded_file = UploadedFile(
            original_filename=original_filename,
            stored_filename=stored_filename,
            file_size=file_size,
            file_type=file_extension,
            mime_type=file.content_type,
            upload_status=UploadStatus.pending,
            uploaded_by=current_user_id
        )
        
        db_session.add(uploaded_file)
        db_session.commit()
        
        # Log upload
        log_entry = AuditLog(
            user_id=current_user_id,
            action='FILE_UPLOADED',
            table_name='uploaded_files',
            record_id=uploaded_file.file_id,
            new_values={
                'filename': original_filename,
                'size': file_size
            },
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        db_session.add(log_entry)
        db_session.commit()
        
        # Process file in background (for now, process immediately)
        try:
            uploaded_file.upload_status = UploadStatus.processing
            db_session.commit()
            
            # Validate and process file
            template_id = request.form.get('template_id')
            template = None
            
            if template_id:
                template = db_session.query(UploadTemplate).filter_by(
                    template_id=template_id,
                    is_active=True
                ).first()
            
            # Read and validate file
            validation_result = file_validator.validate_file(
                upload_path,
                file_extension,
                template
            )
            
            if not validation_result['valid']:
                uploaded_file.upload_status = UploadStatus.rejected
                uploaded_file.error_message = validation_result['error']
                db_session.commit()
                
                return jsonify({
                    'error': 'File validation failed',
                    'details': validation_result['error']
                }), 400
            
            # Process file and insert data
            processing_result = file_processor.process_file(
                upload_path,
                file_extension,
                uploaded_file.file_id,
                db_session
            )
            
            # Update upload record
            uploaded_file.upload_status = UploadStatus.completed
            uploaded_file.processed_at = datetime.utcnow()
            uploaded_file.rows_processed = processing_result['rows_processed']
            uploaded_file.rows_failed = processing_result['rows_failed']
            uploaded_file.validation_notes = processing_result.get('notes')
            db_session.commit()
            
            logger.info(f"File processed successfully: {original_filename}")
            
            return jsonify({
                'message': 'File uploaded and processed successfully',
                'file': uploaded_file.to_dict(),
                'processing': processing_result
            }), 200
            
        except Exception as e:
            # Update status to failed
            uploaded_file.upload_status = UploadStatus.failed
            uploaded_file.error_message = str(e)
            db_session.commit()
            
            logger.error(f"Error processing file: {str(e)}")
            return jsonify({
                'error': 'File processing failed',
                'details': str(e)
            }), 500
            
    except Exception as e:
        db_session.rollback()
        logger.error(f"Error uploading file: {str(e)}")
        return jsonify({'error': 'File upload failed'}), 500


@submission_bp.route('/uploads', methods=['GET'])
@jwt_required()
def get_uploads():
    """
    Get list of uploaded files
    
    Query Parameters:
        status (str): Filter by upload status
        limit (int): Number of records to return
        offset (int): Number of records to skip
    
    Returns:
        JSON response with list of uploaded files
    """
    try:
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        user_role = claims.get('role', 'public')
        
        # Base query
        query = db_session.query(UploadedFile)
        
        # Filter by user if not admin/executive
        if user_role not in ['admin', 'executive']:
            query = query.filter(UploadedFile.uploaded_by == current_user_id)
        
        # Filter by status
        status = request.args.get('status')
        if status:
            try:
                status_enum = UploadStatus[status]
                query = query.filter(UploadedFile.upload_status == status_enum)
            except KeyError:
                return jsonify({'error': f'Invalid status: {status}'}), 400
        
        # Pagination
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        total = query.count()
        uploads = query.order_by(UploadedFile.uploaded_at.desc()).limit(limit).offset(offset).all()
        
        return jsonify({
            'total': total,
            'limit': limit,
            'offset': offset,
            'uploads': [upload.to_dict() for upload in uploads]
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting uploads: {str(e)}")
        return jsonify({'error': 'Failed to retrieve uploads'}), 500


@submission_bp.route('/uploads/<file_id>', methods=['GET'])
@jwt_required()
def get_upload_details(file_id):
    """
    Get detailed information about a specific upload
    
    Args:
        file_id (str): UUID of the uploaded file
    
    Returns:
        JSON response with upload details
    """
    try:
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        user_role = claims.get('role', 'public')
        
        upload = db_session.query(UploadedFile).filter_by(file_id=file_id).first()
        
        if not upload:
            return jsonify({'error': 'Upload not found'}), 404
        
        # Check permissions
        if user_role not in ['admin', 'executive'] and str(upload.uploaded_by) != current_user_id:
            return jsonify({'error': 'Unauthorized access'}), 403
        
        # Get associated data count
        data_count = db_session.query(EngagementData).filter_by(file_id=file_id).count()
        
        upload_dict = upload.to_dict()
        upload_dict['data_records'] = data_count
        
        return jsonify({
            'upload': upload_dict
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting upload details: {str(e)}")
        return jsonify({'error': 'Failed to retrieve upload details'}), 500


@submission_bp.route('/templates', methods=['GET'])
@jwt_required()
def get_templates():
    """
    Get list of available upload templates
    
    Returns:
        JSON response with list of templates
    """
    try:
        templates = db_session.query(UploadTemplate).filter_by(is_active=True).all()
        
        return jsonify({
            'templates': [template.to_dict() for template in templates]
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting templates: {str(e)}")
        return jsonify({'error': 'Failed to retrieve templates'}), 500


@submission_bp.route('/templates/download/<template_id>', methods=['GET'])
@jwt_required()
def download_template(template_id):
    """
    Download template file
    
    Args:
        template_id (str): UUID of the template
    
    Returns:
        Template file download
    """
    try:
        template = db_session.query(UploadTemplate).filter_by(
            template_id=template_id,
            is_active=True
        ).first()
        
        if not template:
            return jsonify({'error': 'Template not found'}), 404
        
        # Template files should be stored in templates folder
        template_path = os.path.join(
            Config.TEMPLATE_FOLDER,
            f"{template.template_name}_v{template.template_version}.xlsx"
        )
        
        if not os.path.exists(template_path):
            return jsonify({'error': 'Template file not found'}), 404
        
        return send_file(
            template_path,
            as_attachment=True,
            download_name=f"{template.template_name}_v{template.template_version}.xlsx"
        )
        
    except Exception as e:
        logger.error(f"Error downloading template: {str(e)}")
        return jsonify({'error': 'Failed to download template'}), 500


@submission_bp.route('/uploads/<file_id>', methods=['DELETE'])
@jwt_required()
@role_required(['admin', 'executive'])
def delete_upload(file_id):
    """
    Delete an uploaded file and associated data (Admin/Executive only)
    
    Args:
        file_id (str): UUID of the uploaded file
    
    Returns:
        JSON response with deletion status
    """
    try:
        current_user_id = get_jwt_identity()
        
        upload = db_session.query(UploadedFile).filter_by(file_id=file_id).first()
        
        if not upload:
            return jsonify({'error': 'Upload not found'}), 404
        
        # Delete physical file
        file_path = os.path.join(Config.UPLOAD_FOLDER, upload.stored_filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Log deletion
        log_entry = AuditLog(
            user_id=current_user_id,
            action='FILE_DELETED',
            table_name='uploaded_files',
            record_id=upload.file_id,
            old_values={'filename': upload.original_filename},
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        db_session.add(log_entry)
        
        # Delete database record (cascade will handle engagement_data)
        db_session.delete(upload)
        db_session.commit()
        
        logger.info(f"File deleted: {upload.original_filename}")
        
        return jsonify({
            'message': 'File deleted successfully'
        }), 200
        
    except Exception as e:
        db_session.rollback()
        logger.error(f"Error deleting upload: {str(e)}")
        return jsonify({'error': 'Failed to delete upload'}), 500
