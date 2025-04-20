"""
API routes for the web dashboard.
"""

from flask import Blueprint, request, jsonify, g
from flask_login import current_user
import logging
import json
from datetime import datetime
from functools import wraps

from web_dashboard.models import db, User, ApiKey, AgentStatus, Conversation, Message, KnowledgeBaseEntry

logger = logging.getLogger(__name__)

# Create blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

def require_api_key(f):
    """Decorator to require API key for access."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get API key from header or query parameter
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        
        if not api_key:
            return jsonify({'error': 'API key is required'}), 401
        
        # Check if API key exists and is active
        key = ApiKey.query.filter_by(key=api_key, is_active=True).first()
        if not key:
            return jsonify({'error': 'Invalid or inactive API key'}), 401
        
        # Store user in g for access in the route
        g.user = User.query.get(key.user_id)
        
        # Update last used timestamp
        key.last_used_at = datetime.utcnow()
        db.session.commit()
        
        return f(*args, **kwargs)
    return decorated_function

@api_bp.route('/status')
@require_api_key
def status():
    """Get API status."""
    return jsonify({
        'status': 'ok',
        'version': '1.0.0',
        'timestamp': datetime.utcnow().isoformat()
    })

@api_bp.route('/agents')
@require_api_key
def agents():
    """Get all agents."""
    agent_statuses = AgentStatus.query.all()
    
    agents_list = []
    for status in agent_statuses:
        agents_list.append({
            'id': status.agent_id,
            'type': status.agent_type,
            'status': status.status,
            'last_active': status.last_active.isoformat() if status.last_active else None,
            'error_message': status.error_message,
            'metadata': status.metadata
        })
    
    return jsonify(agents_list)

@api_bp.route('/agents/<agent_id>')
@require_api_key
def agent(agent_id):
    """Get a specific agent."""
    agent_status = AgentStatus.query.filter_by(agent_id=agent_id).first()
    
    if not agent_status:
        return jsonify({'error': 'Agent not found'}), 404
    
    return jsonify({
        'id': agent_status.agent_id,
        'type': agent_status.agent_type,
        'status': agent_status.status,
        'last_active': agent_status.last_active.isoformat() if agent_status.last_active else None,
        'error_message': agent_status.error_message,
        'metadata': agent_status.metadata
    })

@api_bp.route('/agents/<agent_id>/update', methods=['POST'])
@require_api_key
def update_agent(agent_id):
    """Update an agent's status."""
    agent_status = AgentStatus.query.filter_by(agent_id=agent_id).first()
    
    if not agent_status:
        return jsonify({'error': 'Agent not found'}), 404
    
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Update fields
    if 'status' in data:
        agent_status.status = data['status']
    
    if 'error_message' in data:
        agent_status.error_message = data['error_message']
    
    if 'metadata' in data:
        if agent_status.metadata is None:
            agent_status.metadata = {}
        agent_status.metadata.update(data['metadata'])
    
    agent_status.last_active = datetime.utcnow()
    db.session.commit()
    
    logger.info(f'Agent {agent_id} updated via API by user {g.user.username}')
    
    return jsonify({'success': True})

@api_bp.route('/conversations')
@require_api_key
def conversations():
    """Get all conversations."""
    # Optional filtering by date range
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = Conversation.query
    
    if start_date:
        try:
            start_date = datetime.fromisoformat(start_date)
            query = query.filter(Conversation.created_at >= start_date)
        except ValueError:
            return jsonify({'error': 'Invalid start_date format'}), 400
    
    if end_date:
        try:
            end_date = datetime.fromisoformat(end_date)
            query = query.filter(Conversation.created_at <= end_date)
        except ValueError:
            return jsonify({'error': 'Invalid end_date format'}), 400
    
    conversations_list = []
    for conv in query.all():
        conversations_list.append({
            'id': conv.conversation_id,
            'title': conv.title,
            'created_at': conv.created_at.isoformat(),
            'updated_at': conv.updated_at.isoformat(),
            'is_archived': conv.is_archived,
            'message_count': len(conv.messages)
        })
    
    return jsonify(conversations_list)

@api_bp.route('/conversations/<conversation_id>')
@require_api_key
def conversation(conversation_id):
    """Get a specific conversation with messages."""
    conversation = Conversation.query.filter_by(conversation_id=conversation_id).first()
    
    if not conversation:
        return jsonify({'error': 'Conversation not found'}), 404
    
    messages_list = []
    for msg in conversation.messages:
        messages_list.append({
            'id': msg.id,
            'sender_type': msg.sender_type,
            'sender_id': msg.sender_id,
            'content': msg.content,
            'timestamp': msg.timestamp.isoformat(),
            'metadata': msg.metadata
        })
    
    return jsonify({
        'id': conversation.conversation_id,
        'title': conversation.title,
        'created_at': conversation.created_at.isoformat(),
        'updated_at': conversation.updated_at.isoformat(),
        'is_archived': conversation.is_archived,
        'messages': messages_list
    })

@api_bp.route('/conversations', methods=['POST'])
@require_api_key
def create_conversation():
    """Create a new conversation."""
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Generate conversation ID if not provided
    conversation_id = data.get('conversation_id', f"conv_{int(datetime.utcnow().timestamp())}")
    
    # Create conversation
    conversation = Conversation(
        conversation_id=conversation_id,
        title=data.get('title', 'New Conversation'),
        user_id=g.user.id,
        is_archived=data.get('is_archived', False)
    )
    
    db.session.add(conversation)
    db.session.commit()
    
    logger.info(f'Conversation {conversation_id} created via API by user {g.user.username}')
    
    return jsonify({
        'success': True,
        'conversation_id': conversation.conversation_id,
        'id': conversation.id
    })

@api_bp.route('/conversations/<conversation_id>/messages', methods=['POST'])
@require_api_key
def add_message(conversation_id):
    """Add a message to a conversation."""
    conversation = Conversation.query.filter_by(conversation_id=conversation_id).first()
    
    if not conversation:
        return jsonify({'error': 'Conversation not found'}), 404
    
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Validate required fields
    if 'content' not in data:
        return jsonify({'error': 'Message content is required'}), 400
    
    if 'sender_type' not in data:
        return jsonify({'error': 'Sender type is required'}), 400
    
    if 'sender_id' not in data:
        return jsonify({'error': 'Sender ID is required'}), 400
    
    # Create message
    message = Message(
        conversation_id=conversation.id,
        sender_type=data['sender_type'],
        sender_id=data['sender_id'],
        content=data['content'],
        metadata=data.get('metadata')
    )
    
    db.session.add(message)
    
    # Update conversation timestamp
    conversation.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    logger.info(f'Message added to conversation {conversation_id} via API by user {g.user.username}')
    
    return jsonify({
        'success': True,
        'message_id': message.id
    })

@api_bp.route('/knowledge-base')
@require_api_key
def knowledge_base():
    """Get all knowledge base entries."""
    kb_entries = KnowledgeBaseEntry.query.all()
    
    entries_list = []
    for entry in kb_entries:
        entries_list.append({
            'id': entry.document_id,
            'title': entry.title,
            'source': entry.source,
            'file_type': entry.file_type,
            'status': entry.status,
            'created_at': entry.created_at.isoformat(),
            'updated_at': entry.updated_at.isoformat(),
            'version_count': len(entry.versions)
        })
    
    return jsonify(entries_list)

@api_bp.route('/knowledge-base/<document_id>')
@require_api_key
def knowledge_base_document(document_id):
    """Get a specific knowledge base document."""
    document = KnowledgeBaseEntry.query.filter_by(document_id=document_id).first()
    
    if not document:
        return jsonify({'error': 'Document not found'}), 404
    
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

@api_bp.route('/knowledge-base/search')
@require_api_key
def knowledge_base_search():
    """Search the knowledge base."""
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

@api_bp.route('/user')
@require_api_key
def user_info():
    """Get information about the authenticated user."""
    user = g.user
    
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'is_admin': user.is_admin,
        'roles': [role.name for role in user.roles],
        'permissions': [perm.name for role in user.roles for perm in role.permissions]
    })
