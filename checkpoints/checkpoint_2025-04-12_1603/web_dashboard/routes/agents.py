"""
Agent management routes for the web dashboard.
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
import logging
import json
from datetime import datetime

from web_dashboard.models import db, AgentStatus, AgentPerformanceMetric
from web_dashboard.utils.permissions import requires_permission

logger = logging.getLogger(__name__)

# Create blueprint
agents_bp = Blueprint('agents', __name__, url_prefix='/agents')

@agents_bp.route('/')
@login_required
@requires_permission('view_dashboard')
def index():
    """Render the agent management page."""
    # Get all agent statuses
    agent_statuses = AgentStatus.query.all()
    
    return render_template(
        'agents/index.html',
        agent_statuses=agent_statuses
    )

@agents_bp.route('/<agent_id>')
@login_required
@requires_permission('view_dashboard')
def agent_detail(agent_id):
    """Render the agent detail page."""
    # Get agent status
    agent_status = AgentStatus.query.filter_by(agent_id=agent_id).first_or_404()
    
    # Get agent performance metrics
    metrics = AgentPerformanceMetric.query.filter_by(
        agent_id=agent_id
    ).order_by(
        AgentPerformanceMetric.metric_name,
        AgentPerformanceMetric.timestamp.desc()
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
    
    return render_template(
        'agents/detail.html',
        agent=agent_status,
        metrics=organized_metrics
    )

@agents_bp.route('/<agent_id>/restart', methods=['POST'])
@login_required
@requires_permission('manage_agents')
def restart_agent(agent_id):
    """Restart an agent."""
    # Get agent status
    agent_status = AgentStatus.query.filter_by(agent_id=agent_id).first_or_404()
    
    # In a real implementation, this would communicate with the agent system
    # to restart the agent. For now, we'll just update the status.
    agent_status.status = 'active'
    agent_status.error_message = None
    agent_status.last_active = datetime.utcnow()
    db.session.commit()
    
    # Log the restart
    logger.info(f'Agent {agent_id} restarted by user {current_user.username}')
    
    flash(f'Agent {agent_id} restarted successfully', 'success')
    return redirect(url_for('agents.agent_detail', agent_id=agent_id))

@agents_bp.route('/<agent_id>/stop', methods=['POST'])
@login_required
@requires_permission('manage_agents')
def stop_agent(agent_id):
    """Stop an agent."""
    # Get agent status
    agent_status = AgentStatus.query.filter_by(agent_id=agent_id).first_or_404()
    
    # In a real implementation, this would communicate with the agent system
    # to stop the agent. For now, we'll just update the status.
    agent_status.status = 'idle'
    agent_status.last_active = datetime.utcnow()
    db.session.commit()
    
    # Log the stop
    logger.info(f'Agent {agent_id} stopped by user {current_user.username}')
    
    flash(f'Agent {agent_id} stopped successfully', 'success')
    return redirect(url_for('agents.agent_detail', agent_id=agent_id))

@agents_bp.route('/<agent_id>/configure', methods=['GET', 'POST'])
@login_required
@requires_permission('manage_agents')
def configure_agent(agent_id):
    """Configure an agent."""
    # Get agent status
    agent_status = AgentStatus.query.filter_by(agent_id=agent_id).first_or_404()
    
    if request.method == 'POST':
        # Get configuration from form
        config = {}
        for key, value in request.form.items():
            if key.startswith('config_'):
                config_key = key[7:]  # Remove 'config_' prefix
                config[config_key] = value
        
        # Update agent metadata
        if agent_status.metadata is None:
            agent_status.metadata = {}
        
        agent_status.metadata['config'] = config
        db.session.commit()
        
        # Log the configuration update
        logger.info(f'Agent {agent_id} configured by user {current_user.username}')
        
        flash(f'Agent {agent_id} configuration updated successfully', 'success')
        return redirect(url_for('agents.agent_detail', agent_id=agent_id))
    
    # Get current configuration
    config = agent_status.metadata.get('config', {}) if agent_status.metadata else {}
    
    return render_template(
        'agents/configure.html',
        agent=agent_status,
        config=config
    )

@agents_bp.route('/api/status')
@login_required
@requires_permission('view_dashboard')
def api_status():
    """API endpoint to get all agent statuses."""
    agent_statuses = AgentStatus.query.all()
    
    statuses = []
    for status in agent_statuses:
        statuses.append({
            'id': status.agent_id,
            'type': status.agent_type,
            'status': status.status,
            'last_active': status.last_active.isoformat() if status.last_active else None,
            'error_message': status.error_message,
            'metadata': status.metadata
        })
    
    return jsonify(statuses)

@agents_bp.route('/api/<agent_id>/metrics')
@login_required
@requires_permission('view_dashboard')
def api_metrics(agent_id):
    """API endpoint to get metrics for a specific agent."""
    metrics = AgentPerformanceMetric.query.filter_by(
        agent_id=agent_id
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
    
    return jsonify(organized_metrics)

@agents_bp.route('/api/<agent_id>/update-status', methods=['POST'])
@login_required
@requires_permission('manage_agents')
def api_update_status(agent_id):
    """API endpoint to update an agent's status."""
    # Get agent status
    agent_status = AgentStatus.query.filter_by(agent_id=agent_id).first_or_404()
    
    # Get data from request
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Update status
    if 'status' in data:
        agent_status.status = data['status']
    
    if 'error_message' in data:
        agent_status.error_message = data['error_message']
    
    agent_status.last_active = datetime.utcnow()
    db.session.commit()
    
    # Log the update
    logger.info(f'Agent {agent_id} status updated by user {current_user.username}')
    
    return jsonify({'success': True})

@agents_bp.route('/api/add-metric', methods=['POST'])
@login_required
@requires_permission('manage_agents')
def api_add_metric():
    """API endpoint to add a performance metric."""
    # Get data from request
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Validate required fields
    required_fields = ['agent_id', 'agent_type', 'metric_name', 'metric_value']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    # Create new metric
    metric = AgentPerformanceMetric(
        agent_id=data['agent_id'],
        agent_type=data['agent_type'],
        metric_name=data['metric_name'],
        metric_value=float(data['metric_value']),
        metadata=data.get('metadata')
    )
    
    db.session.add(metric)
    db.session.commit()
    
    # Log the metric addition
    logger.info(f'Performance metric added for agent {data["agent_id"]}')
    
    return jsonify({'success': True, 'id': metric.id})
