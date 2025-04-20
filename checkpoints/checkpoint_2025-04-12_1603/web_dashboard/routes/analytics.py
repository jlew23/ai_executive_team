"""
Analytics and reporting routes for the web dashboard.
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
import logging
from datetime import datetime, timedelta
import json

from web_dashboard.models import db, AnalyticsEvent, AgentPerformanceMetric, Conversation, Message
from web_dashboard.utils.permissions import requires_permission

logger = logging.getLogger(__name__)

# Create blueprint
analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')

@analytics_bp.route('/')
@login_required
@requires_permission('view_analytics')
def index():
    """Render the analytics dashboard page."""
    return render_template('analytics/index.html')

@analytics_bp.route('/agent-performance')
@login_required
@requires_permission('view_analytics')
def agent_performance():
    """Render the agent performance page."""
    # Get time range from query parameters
    days = request.args.get('days', 7, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get agent types
    agent_types = db.session.query(AgentPerformanceMetric.agent_type).distinct().all()
    agent_types = [t[0] for t in agent_types]
    
    # Get metrics for each agent type
    metrics_by_type = {}
    for agent_type in agent_types:
        metrics = AgentPerformanceMetric.query.filter(
            AgentPerformanceMetric.agent_type == agent_type,
            AgentPerformanceMetric.timestamp >= start_date
        ).order_by(
            AgentPerformanceMetric.metric_name,
            AgentPerformanceMetric.timestamp
        ).all()
        
        # Organize metrics by name
        organized_metrics = {}
        for metric in metrics:
            if metric.metric_name not in organized_metrics:
                organized_metrics[metric.metric_name] = []
            
            organized_metrics[metric.metric_name].append({
                'value': metric.metric_value,
                'timestamp': metric.timestamp
            })
        
        metrics_by_type[agent_type] = organized_metrics
    
    return render_template(
        'analytics/agent_performance.html',
        agent_types=agent_types,
        metrics_by_type=metrics_by_type,
        days=days
    )

@analytics_bp.route('/conversation-analytics')
@login_required
@requires_permission('view_analytics')
def conversation_analytics():
    """Render the conversation analytics page."""
    # Get time range from query parameters
    days = request.args.get('days', 30, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get conversation counts by day
    conversation_counts = db.session.query(
        db.func.date(Conversation.created_at).label('date'),
        db.func.count().label('count')
    ).filter(
        Conversation.created_at >= start_date
    ).group_by(
        db.func.date(Conversation.created_at)
    ).all()
    
    # Get message counts by day
    message_counts = db.session.query(
        db.func.date(Message.timestamp).label('date'),
        db.func.count().label('count')
    ).filter(
        Message.timestamp >= start_date
    ).group_by(
        db.func.date(Message.timestamp)
    ).all()
    
    # Get message counts by sender type
    sender_counts = db.session.query(
        Message.sender_type,
        db.func.count().label('count')
    ).filter(
        Message.timestamp >= start_date
    ).group_by(
        Message.sender_type
    ).all()
    
    # Format data for charts
    conversation_data = {str(row.date): row.count for row in conversation_counts}
    message_data = {str(row.date): row.count for row in message_counts}
    sender_data = {row.sender_type: row.count for row in sender_counts}
    
    return render_template(
        'analytics/conversation_analytics.html',
        conversation_data=conversation_data,
        message_data=message_data,
        sender_data=sender_data,
        days=days
    )

@analytics_bp.route('/user-activity')
@login_required
@requires_permission('view_analytics')
def user_activity():
    """Render the user activity page."""
    # Get time range from query parameters
    days = request.args.get('days', 30, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get analytics events
    events = AnalyticsEvent.query.filter(
        AnalyticsEvent.timestamp >= start_date
    ).order_by(
        AnalyticsEvent.timestamp.desc()
    ).all()
    
    # Get event counts by type
    event_counts = db.session.query(
        AnalyticsEvent.event_type,
        db.func.count().label('count')
    ).filter(
        AnalyticsEvent.timestamp >= start_date
    ).group_by(
        AnalyticsEvent.event_type
    ).all()
    
    # Get event counts by day
    daily_counts = db.session.query(
        db.func.date(AnalyticsEvent.timestamp).label('date'),
        db.func.count().label('count')
    ).filter(
        AnalyticsEvent.timestamp >= start_date
    ).group_by(
        db.func.date(AnalyticsEvent.timestamp)
    ).all()
    
    # Format data for charts
    event_data = {row.event_type: row.count for row in event_counts}
    daily_data = {str(row.date): row.count for row in daily_counts}
    
    return render_template(
        'analytics/user_activity.html',
        events=events,
        event_data=event_data,
        daily_data=daily_data,
        days=days
    )

@analytics_bp.route('/knowledge-base-analytics')
@login_required
@requires_permission('view_analytics')
def kb_analytics():
    """Render the knowledge base analytics page."""
    # This would typically integrate with the knowledge base system
    # to provide analytics on document usage, search queries, etc.
    # For now, we'll just render a template with placeholder data
    
    return render_template('analytics/kb_analytics.html')

@analytics_bp.route('/api/agent-performance')
@login_required
@requires_permission('view_analytics')
def api_agent_performance():
    """API endpoint to get agent performance data."""
    # Get time range from query parameters
    days = request.args.get('days', 7, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get agent types
    agent_types = db.session.query(AgentPerformanceMetric.agent_type).distinct().all()
    agent_types = [t[0] for t in agent_types]
    
    # Get metrics for each agent type
    metrics_by_type = {}
    for agent_type in agent_types:
        metrics = AgentPerformanceMetric.query.filter(
            AgentPerformanceMetric.agent_type == agent_type,
            AgentPerformanceMetric.timestamp >= start_date
        ).order_by(
            AgentPerformanceMetric.metric_name,
            AgentPerformanceMetric.timestamp
        ).all()
        
        # Organize metrics by name
        organized_metrics = {}
        for metric in metrics:
            if metric.metric_name not in organized_metrics:
                organized_metrics[metric.metric_name] = []
            
            organized_metrics[metric.metric_name].append({
                'value': metric.metric_value,
                'timestamp': metric.timestamp.isoformat()
            })
        
        metrics_by_type[agent_type] = organized_metrics
    
    return jsonify(metrics_by_type)

@analytics_bp.route('/api/conversation-analytics')
@login_required
@requires_permission('view_analytics')
def api_conversation_analytics():
    """API endpoint to get conversation analytics data."""
    # Get time range from query parameters
    days = request.args.get('days', 30, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get conversation counts by day
    conversation_counts = db.session.query(
        db.func.date(Conversation.created_at).label('date'),
        db.func.count().label('count')
    ).filter(
        Conversation.created_at >= start_date
    ).group_by(
        db.func.date(Conversation.created_at)
    ).all()
    
    # Get message counts by day
    message_counts = db.session.query(
        db.func.date(Message.timestamp).label('date'),
        db.func.count().label('count')
    ).filter(
        Message.timestamp >= start_date
    ).group_by(
        db.func.date(Message.timestamp)
    ).all()
    
    # Get message counts by sender type
    sender_counts = db.session.query(
        Message.sender_type,
        db.func.count().label('count')
    ).filter(
        Message.timestamp >= start_date
    ).group_by(
        Message.sender_type
    ).all()
    
    # Format data for charts
    conversation_data = {str(row.date): row.count for row in conversation_counts}
    message_data = {str(row.date): row.count for row in message_counts}
    sender_data = {row.sender_type: row.count for row in sender_counts}
    
    return jsonify({
        'conversation_data': conversation_data,
        'message_data': message_data,
        'sender_data': sender_data
    })

@analytics_bp.route('/api/user-activity')
@login_required
@requires_permission('view_analytics')
def api_user_activity():
    """API endpoint to get user activity data."""
    # Get time range from query parameters
    days = request.args.get('days', 30, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get event counts by type
    event_counts = db.session.query(
        AnalyticsEvent.event_type,
        db.func.count().label('count')
    ).filter(
        AnalyticsEvent.timestamp >= start_date
    ).group_by(
        AnalyticsEvent.event_type
    ).all()
    
    # Get event counts by day
    daily_counts = db.session.query(
        db.func.date(AnalyticsEvent.timestamp).label('date'),
        db.func.count().label('count')
    ).filter(
        AnalyticsEvent.timestamp >= start_date
    ).group_by(
        db.func.date(AnalyticsEvent.timestamp)
    ).all()
    
    # Format data for charts
    event_data = {row.event_type: row.count for row in event_counts}
    daily_data = {str(row.date): row.count for row in daily_counts}
    
    return jsonify({
        'event_data': event_data,
        'daily_data': daily_data
    })

@analytics_bp.route('/api/record-event', methods=['POST'])
@login_required
def api_record_event():
    """API endpoint to record an analytics event."""
    # Get data from request
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Validate required fields
    if 'event_type' not in data:
        return jsonify({'error': 'Missing required field: event_type'}), 400
    
    # Create new event
    event = AnalyticsEvent(
        event_type=data['event_type'],
        event_data=data.get('event_data'),
        user_id=current_user.id
    )
    
    db.session.add(event)
    db.session.commit()
    
    # Log the event
    logger.info(f'Analytics event recorded: {data["event_type"]}')
    
    return jsonify({'success': True, 'id': event.id})
