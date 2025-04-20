"""
Dashboard routes for the web dashboard.
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
import logging
from datetime import datetime, timedelta

from web_dashboard.models import db, AgentStatus, Conversation, Message, AgentPerformanceMetric

logger = logging.getLogger(__name__)

# Create blueprint
dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    """Render the main dashboard page."""
    # Get agent statuses
    agent_statuses = AgentStatus.query.all()
    
    # Get recent conversations
    recent_conversations = Conversation.query.order_by(
        Conversation.updated_at.desc()
    ).limit(5).all()
    
    # Get agent performance metrics
    performance_metrics = {}
    for agent_status in agent_statuses:
        agent_id = agent_status.agent_id
        metrics = AgentPerformanceMetric.query.filter_by(
            agent_id=agent_id
        ).order_by(
            AgentPerformanceMetric.timestamp.desc()
        ).limit(10).all()
        
        performance_metrics[agent_id] = metrics
    
    # Get system stats
    total_conversations = Conversation.query.count()
    total_messages = Message.query.count()
    active_agents = AgentStatus.query.filter_by(status='active').count()
    
    return render_template(
        'dashboard/index.html',
        agent_statuses=agent_statuses,
        recent_conversations=recent_conversations,
        performance_metrics=performance_metrics,
        total_conversations=total_conversations,
        total_messages=total_messages,
        active_agents=active_agents
    )

@dashboard_bp.route('/agent-status')
@login_required
def agent_status():
    """Get the current status of all agents."""
    agent_statuses = AgentStatus.query.all()
    
    statuses = []
    for status in agent_statuses:
        statuses.append({
            'id': status.agent_id,
            'type': status.agent_type,
            'status': status.status,
            'last_active': status.last_active.isoformat() if status.last_active else None,
            'error_message': status.error_message
        })
    
    return jsonify(statuses)

@dashboard_bp.route('/performance-metrics')
@login_required
def performance_metrics():
    """Get performance metrics for all agents."""
    # Get time range from query parameters
    days = request.args.get('days', 7, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get metrics for all agents
    metrics = AgentPerformanceMetric.query.filter(
        AgentPerformanceMetric.timestamp >= start_date
    ).order_by(
        AgentPerformanceMetric.agent_id,
        AgentPerformanceMetric.metric_name,
        AgentPerformanceMetric.timestamp
    ).all()
    
    # Organize metrics by agent and metric name
    organized_metrics = {}
    for metric in metrics:
        agent_id = metric.agent_id
        metric_name = metric.metric_name
        
        if agent_id not in organized_metrics:
            organized_metrics[agent_id] = {}
        
        if metric_name not in organized_metrics[agent_id]:
            organized_metrics[agent_id][metric_name] = []
        
        organized_metrics[agent_id][metric_name].append({
            'value': metric.metric_value,
            'timestamp': metric.timestamp.isoformat()
        })
    
    return jsonify(organized_metrics)

@dashboard_bp.route('/recent-activity')
@login_required
def recent_activity():
    """Get recent activity for the dashboard."""
    # Get time range from query parameters
    hours = request.args.get('hours', 24, type=int)
    start_date = datetime.utcnow() - timedelta(hours=hours)
    
    # Get recent conversations
    recent_conversations = Conversation.query.filter(
        Conversation.updated_at >= start_date
    ).order_by(
        Conversation.updated_at.desc()
    ).limit(10).all()
    
    # Get recent messages
    recent_messages = Message.query.filter(
        Message.timestamp >= start_date
    ).order_by(
        Message.timestamp.desc()
    ).limit(20).all()
    
    # Format the data
    conversations = []
    for conv in recent_conversations:
        conversations.append({
            'id': conv.conversation_id,
            'title': conv.title or f"Conversation {conv.conversation_id}",
            'updated_at': conv.updated_at.isoformat(),
            'message_count': len(conv.messages)
        })
    
    messages = []
    for msg in recent_messages:
        messages.append({
            'conversation_id': msg.conversation.conversation_id,
            'sender_type': msg.sender_type,
            'sender_id': msg.sender_id,
            'content': msg.content[:100] + '...' if len(msg.content) > 100 else msg.content,
            'timestamp': msg.timestamp.isoformat()
        })
    
    return jsonify({
        'conversations': conversations,
        'messages': messages
    })

@dashboard_bp.route('/system-health')
@login_required
def system_health():
    """Get system health information."""
    # Count agents by status
    agent_counts = {
        'active': AgentStatus.query.filter_by(status='active').count(),
        'idle': AgentStatus.query.filter_by(status='idle').count(),
        'error': AgentStatus.query.filter_by(status='error').count()
    }
    
    # Get error messages
    error_agents = AgentStatus.query.filter_by(status='error').all()
    errors = []
    for agent in error_agents:
        errors.append({
            'agent_id': agent.agent_id,
            'agent_type': agent.agent_type,
            'error_message': agent.error_message,
            'last_active': agent.last_active.isoformat() if agent.last_active else None
        })
    
    # Get system stats
    stats = {
        'total_conversations': Conversation.query.count(),
        'total_messages': Message.query.count(),
        'active_agents': agent_counts['active'],
        'error_agents': agent_counts['error']
    }
    
    return jsonify({
        'agent_counts': agent_counts,
        'errors': errors,
        'stats': stats
    })
