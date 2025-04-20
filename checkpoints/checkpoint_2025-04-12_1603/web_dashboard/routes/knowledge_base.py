"""
Knowledge base management routes for the web dashboard.
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, send_file
from flask_login import login_required, current_user
import logging
import os
import json
from datetime import datetime
from werkzeug.utils import secure_filename

from web_dashboard.models import db, KnowledgeBaseEntry, KnowledgeBaseVersion
from web_dashboard.utils.permissions import requires_permission
from web_dashboard.config import Config

logger = logging.getLogger(__name__)

# Create blueprint
kb_bp = Blueprint('kb', __name__, url_prefix='/knowledge-base')

# Ensure upload directory exists
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(Config.KB_STORAGE_PATH, exist_ok=True)

@kb_bp.route('/')
@login_required
@requires_permission('view_dashboard')
def index():
    """Render the knowledge base management page."""
    # Get all knowledge base entries
    kb_entries = KnowledgeBaseEntry.query.order_by(KnowledgeBaseEntry.updated_at.desc()).all()
    
    return render_template(
        'kb/index.html',
        kb_entries=kb_entries
    )

@kb_bp.route('/<document_id>')
@login_required
@requires_permission('view_dashboard')
def document_detail(document_id):
    """Render the document detail page."""
    # Get document
    document = KnowledgeBaseEntry.query.filter_by(document_id=document_id).first_or_404()
    
    # Get document versions
    versions = KnowledgeBaseVersion.query.filter_by(
        entry_id=document.id
    ).order_by(
        KnowledgeBaseVersion.version.desc()
    ).all()
    
    return render_template(
        'kb/detail.html',
        document=document,
        versions=versions
    )

@kb_bp.route('/upload', methods=['GET', 'POST'])
@login_required
@requires_permission('manage_kb')
def upload_document():
    """Handle document upload."""
    if request.method == 'POST':
        # Check if file was uploaded
        if 'document' not in request.files:
            flash('No file selected', 'danger')
            return redirect(request.url)
        
        file = request.files['document']
        
        # Check if file was selected
        if file.filename == '':
            flash('No file selected', 'danger')
            return redirect(request.url)
        
        # Get form data
        title = request.form.get('title', 'Untitled Document')
        source = request.form.get('source', '')
        
        # Process file
        if file:
            # Secure filename
            filename = secure_filename(file.filename)
            file_type = os.path.splitext(filename)[1][1:].lower()
            
            # Generate document ID
            document_id = f"doc_{int(datetime.utcnow().timestamp())}_{secure_filename(title)}"
            
            # Save file
            file_path = os.path.join(Config.KB_STORAGE_PATH, f"{document_id}.{file_type}")
            file.save(file_path)
            
            # Create knowledge base entry
            kb_entry = KnowledgeBaseEntry(
                document_id=document_id,
                title=title,
                source=source,
                file_path=file_path,
                file_type=file_type,
                status='processing',  # Initial status
                created_by=current_user.id,
                metadata={
                    'original_filename': filename,
                    'size': os.path.getsize(file_path)
                }
            )
            
            db.session.add(kb_entry)
            db.session.commit()
            
            # Create initial version
            version = KnowledgeBaseVersion(
                entry_id=kb_entry.id,
                version=1,
                file_path=file_path,
                created_by=current_user.id,
                is_current=True,
                changes='Initial upload'
            )
            
            db.session.add(version)
            db.session.commit()
            
            # Log the upload
            logger.info(f'Document {document_id} uploaded by user {current_user.username}')
            
            # In a real implementation, this would trigger document processing
            # For now, we'll just update the status
            kb_entry.status = 'ready'
            db.session.commit()
            
            flash(f'Document "{title}" uploaded successfully', 'success')
            return redirect(url_for('kb.document_detail', document_id=document_id))
    
    return render_template('kb/upload.html')

@kb_bp.route('/<document_id>/update', methods=['GET', 'POST'])
@login_required
@requires_permission('manage_kb')
def update_document(document_id):
    """Handle document update."""
    # Get document
    document = KnowledgeBaseEntry.query.filter_by(document_id=document_id).first_or_404()
    
    if request.method == 'POST':
        # Update document metadata
        document.title = request.form.get('title', document.title)
        document.source = request.form.get('source', document.source)
        
        # Check if file was uploaded
        if 'document' in request.files and request.files['document'].filename != '':
            file = request.files['document']
            
            # Secure filename
            filename = secure_filename(file.filename)
            file_type = os.path.splitext(filename)[1][1:].lower()
            
            # Save file
            file_path = os.path.join(Config.KB_STORAGE_PATH, f"{document_id}_v{len(document.versions) + 1}.{file_type}")
            file.save(file_path)
            
            # Update document
            document.file_path = file_path
            document.file_type = file_type
            document.status = 'processing'  # Reset status
            document.updated_at = datetime.utcnow()
            
            if document.metadata is None:
                document.metadata = {}
            
            document.metadata['original_filename'] = filename
            document.metadata['size'] = os.path.getsize(file_path)
            
            # Create new version
            # First, mark all existing versions as not current
            for version in document.versions:
                version.is_current = False
            
            # Create new version
            version = KnowledgeBaseVersion(
                entry_id=document.id,
                version=len(document.versions) + 1,
                file_path=file_path,
                created_by=current_user.id,
                is_current=True,
                changes=request.form.get('changes', 'Updated document')
            )
            
            db.session.add(version)
            
            # In a real implementation, this would trigger document processing
            # For now, we'll just update the status
            document.status = 'ready'
        else:
            # Just update metadata
            document.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Log the update
        logger.info(f'Document {document_id} updated by user {current_user.username}')
        
        flash(f'Document "{document.title}" updated successfully', 'success')
        return redirect(url_for('kb.document_detail', document_id=document_id))
    
    return render_template('kb/update.html', document=document)

@kb_bp.route('/<document_id>/delete', methods=['POST'])
@login_required
@requires_permission('manage_kb')
def delete_document(document_id):
    """Delete a document."""
    # Get document
    document = KnowledgeBaseEntry.query.filter_by(document_id=document_id).first_or_404()
    
    # Delete file
    if document.file_path and os.path.exists(document.file_path):
        os.remove(document.file_path)
    
    # Delete versions
    for version in document.versions:
        if version.file_path and os.path.exists(version.file_path) and version.file_path != document.file_path:
            os.remove(version.file_path)
        db.session.delete(version)
    
    # Delete document
    db.session.delete(document)
    db.session.commit()
    
    # Log the deletion
    logger.info(f'Document {document_id} deleted by user {current_user.username}')
    
    flash('Document deleted successfully', 'success')
    return redirect(url_for('kb.index'))

@kb_bp.route('/<document_id>/download')
@login_required
@requires_permission('view_dashboard')
def download_document(document_id):
    """Download a document."""
    # Get document
    document = KnowledgeBaseEntry.query.filter_by(document_id=document_id).first_or_404()
    
    # Check if file exists
    if not document.file_path or not os.path.exists(document.file_path):
        flash('Document file not found', 'danger')
        return redirect(url_for('kb.document_detail', document_id=document_id))
    
    # Get original filename
    original_filename = document.metadata.get('original_filename') if document.metadata else None
    if not original_filename:
        original_filename = f"{document.title}.{document.file_type}"
    
    # Log the download
    logger.info(f'Document {document_id} downloaded by user {current_user.username}')
    
    return send_file(
        document.file_path,
        as_attachment=True,
        download_name=original_filename
    )

@kb_bp.route('/<document_id>/version/<int:version_id>/download')
@login_required
@requires_permission('view_dashboard')
def download_version(document_id, version_id):
    """Download a specific version of a document."""
    # Get document
    document = KnowledgeBaseEntry.query.filter_by(document_id=document_id).first_or_404()
    
    # Get version
    version = KnowledgeBaseVersion.query.filter_by(
        entry_id=document.id,
        version=version_id
    ).first_or_404()
    
    # Check if file exists
    if not version.file_path or not os.path.exists(version.file_path):
        flash('Version file not found', 'danger')
        return redirect(url_for('kb.document_detail', document_id=document_id))
    
    # Get original filename
    original_filename = document.metadata.get('original_filename') if document.metadata else None
    if not original_filename:
        original_filename = f"{document.title}_v{version.version}.{document.file_type}"
    else:
        name, ext = os.path.splitext(original_filename)
        original_filename = f"{name}_v{version.version}{ext}"
    
    # Log the download
    logger.info(f'Document {document_id} version {version_id} downloaded by user {current_user.username}')
    
    return send_file(
        version.file_path,
        as_attachment=True,
        download_name=original_filename
    )

@kb_bp.route('/api/documents')
@login_required
@requires_permission('view_dashboard')
def api_documents():
    """API endpoint to get all documents."""
    kb_entries = KnowledgeBaseEntry.query.all()
    
    documents = []
    for entry in kb_entries:
        documents.append({
            'id': entry.document_id,
            'title': entry.title,
            'source': entry.source,
            'file_type': entry.file_type,
            'status': entry.status,
            'created_at': entry.created_at.isoformat(),
            'updated_at': entry.updated_at.isoformat(),
            'version_count': len(entry.versions)
        })
    
    return jsonify(documents)

@kb_bp.route('/api/<document_id>')
@login_required
@requires_permission('view_dashboard')
def api_document(document_id):
    """API endpoint to get a specific document."""
    document = KnowledgeBaseEntry.query.filter_by(document_id=document_id).first_or_404()
    
    versions = []
    for version in document.versions:
        versions.append({
            'version': version.version,
            'created_at': version.created_at.isoformat(),
            'created_by': version.created_by,
            'is_current': version.is_current,
            'changes': version.changes
        })
    
    return jsonify({
        'id': document.document_id,
        'title': document.title,
        'source': document.source,
        'file_type': document.file_type,
        'status': document.status,
        'created_at': document.created_at.isoformat(),
        'updated_at': document.updated_at.isoformat(),
        'created_by': document.created_by,
        'metadata': document.metadata,
        'versions': versions
    })

@kb_bp.route('/api/search')
@login_required
@requires_permission('view_dashboard')
def api_search():
    """API endpoint to search documents."""
    query = request.args.get('q', '')
    
    if not query:
        return jsonify([])
    
    # Simple search implementation
    # In a real application, this would use the vector store
    results = KnowledgeBaseEntry.query.filter(
        KnowledgeBaseEntry.title.ilike(f'%{query}%') |
        KnowledgeBaseEntry.source.ilike(f'%{query}%')
    ).all()
    
    documents = []
    for entry in results:
        documents.append({
            'id': entry.document_id,
            'title': entry.title,
            'source': entry.source,
            'file_type': entry.file_type,
            'status': entry.status,
            'created_at': entry.created_at.isoformat(),
            'updated_at': entry.updated_at.isoformat()
        })
    
    return jsonify(documents)
