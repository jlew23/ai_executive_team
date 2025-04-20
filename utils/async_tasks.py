"""
Asynchronous task processing utilities for the AI Executive Team application.
"""

import logging
import threading
import queue
import time
import uuid
import functools
from datetime import datetime
import traceback

logger = logging.getLogger(__name__)

class TaskStatus:
    """Status constants for tasks."""
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELED = 'canceled'

class Task:
    """
    Represents an asynchronous task.
    """
    
    def __init__(self, func, args=None, kwargs=None, task_id=None, name=None):
        """
        Initialize a task.
        
        Args:
            func: Function to execute
            args: Positional arguments for the function
            kwargs: Keyword arguments for the function
            task_id: Optional task ID, generated if not provided
            name: Optional task name
        """
        self.func = func
        self.args = args or ()
        self.kwargs = kwargs or {}
        self.task_id = task_id or str(uuid.uuid4())
        self.name = name or func.__name__
        self.status = TaskStatus.PENDING
        self.result = None
        self.error = None
        self.created_at = datetime.utcnow()
        self.started_at = None
        self.completed_at = None
        self.progress = 0
        self.progress_message = None
        self.callbacks = []
    
    def execute(self):
        """
        Execute the task.
        
        Returns:
            Task result
        """
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.utcnow()
        
        try:
            self.result = self.func(*self.args, **self.kwargs)
            self.status = TaskStatus.COMPLETED
        except Exception as e:
            self.error = str(e)
            self.status = TaskStatus.FAILED
            logger.error(f"Task {self.task_id} ({self.name}) failed: {str(e)}")
            logger.error(traceback.format_exc())
        
        self.completed_at = datetime.utcnow()
        
        # Call callbacks
        for callback in self.callbacks:
            try:
                callback(self)
            except Exception as e:
                logger.error(f"Error in task callback: {str(e)}")
        
        return self.result
    
    def add_callback(self, callback):
        """
        Add a callback function to be called when the task completes.
        
        Args:
            callback: Function to call with the task as argument
        """
        self.callbacks.append(callback)
    
    def update_progress(self, progress, message=None):
        """
        Update the task progress.
        
        Args:
            progress: Progress value (0-100)
            message: Optional progress message
        """
        self.progress = progress
        if message:
            self.progress_message = message
    
    def cancel(self):
        """
        Cancel the task if it hasn't started yet.
        
        Returns:
            True if the task was canceled, False otherwise
        """
        if self.status == TaskStatus.PENDING:
            self.status = TaskStatus.CANCELED
            self.completed_at = datetime.utcnow()
            return True
        
        return False
    
    def get_duration(self):
        """
        Get the task duration in seconds.
        
        Returns:
            Duration in seconds or None if the task hasn't completed
        """
        if not self.started_at:
            return None
        
        end_time = self.completed_at or datetime.utcnow()
        return (end_time - self.started_at).total_seconds()
    
    def to_dict(self):
        """
        Convert the task to a dictionary.
        
        Returns:
            Dictionary representation of the task
        """
        return {
            'task_id': self.task_id,
            'name': self.name,
            'status': self.status,
            'result': self.result,
            'error': self.error,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'progress': self.progress,
            'progress_message': self.progress_message,
            'duration': self.get_duration()
        }

class TaskQueue:
    """
    Queue for managing asynchronous tasks.
    """
    
    def __init__(self, num_workers=4, max_queue_size=100):
        """
        Initialize the task queue.
        
        Args:
            num_workers: Number of worker threads
            max_queue_size: Maximum number of tasks in the queue
        """
        self.queue = queue.Queue(maxsize=max_queue_size)
        self.tasks = {}
        self.workers = []
        self.running = False
        self.lock = threading.RLock()
        self.num_workers = num_workers
    
    def start(self):
        """
        Start the worker threads.
        """
        with self.lock:
            if self.running:
                return
            
            self.running = True
            
            # Create and start worker threads
            for i in range(self.num_workers):
                worker = threading.Thread(target=self._worker_loop, name=f"TaskWorker-{i}")
                worker.daemon = True
                worker.start()
                self.workers.append(worker)
            
            logger.info(f"Task queue started with {self.num_workers} workers")
    
    def stop(self):
        """
        Stop the worker threads.
        """
        with self.lock:
            if not self.running:
                return
            
            self.running = False
            
            # Add None tasks to signal workers to stop
            for _ in range(self.num_workers):
                self.queue.put(None)
            
            # Wait for workers to finish
            for worker in self.workers:
                worker.join(timeout=1.0)
            
            self.workers = []
            
            logger.info("Task queue stopped")
    
    def submit(self, func, args=None, kwargs=None, task_id=None, name=None):
        """
        Submit a task to the queue.
        
        Args:
            func: Function to execute
            args: Positional arguments for the function
            kwargs: Keyword arguments for the function
            task_id: Optional task ID
            name: Optional task name
            
        Returns:
            Task object
        """
        # Create task
        task = Task(func, args, kwargs, task_id, name)
        
        # Store task
        with self.lock:
            self.tasks[task.task_id] = task
        
        # Add to queue
        self.queue.put(task)
        
        logger.debug(f"Task {task.task_id} ({task.name}) submitted")
        
        return task
    
    def get_task(self, task_id):
        """
        Get a task by ID.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task object or None if not found
        """
        with self.lock:
            return self.tasks.get(task_id)
    
    def get_tasks(self, status=None):
        """
        Get all tasks, optionally filtered by status.
        
        Args:
            status: Optional status filter
            
        Returns:
            List of tasks
        """
        with self.lock:
            if status:
                return [task for task in self.tasks.values() if task.status == status]
            else:
                return list(self.tasks.values())
    
    def cancel_task(self, task_id):
        """
        Cancel a task by ID.
        
        Args:
            task_id: Task ID
            
        Returns:
            True if the task was canceled, False otherwise
        """
        with self.lock:
            task = self.tasks.get(task_id)
            if task:
                return task.cancel()
            
            return False
    
    def clear_completed_tasks(self, max_age_seconds=3600):
        """
        Clear completed, failed, or canceled tasks older than the specified age.
        
        Args:
            max_age_seconds: Maximum age in seconds
            
        Returns:
            Number of tasks cleared
        """
        now = datetime.utcnow()
        cleared_count = 0
        
        with self.lock:
            task_ids = list(self.tasks.keys())
            
            for task_id in task_ids:
                task = self.tasks[task_id]
                
                if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELED):
                    if task.completed_at and (now - task.completed_at).total_seconds() > max_age_seconds:
                        del self.tasks[task_id]
                        cleared_count += 1
        
        return cleared_count
    
    def _worker_loop(self):
        """
        Worker thread loop.
        """
        while self.running:
            try:
                # Get task from queue
                task = self.queue.get(block=True, timeout=1.0)
                
                # None is a signal to stop
                if task is None:
                    break
                
                # Execute task
                logger.debug(f"Executing task {task.task_id} ({task.name})")
                task.execute()
                
                # Mark task as done
                self.queue.task_done()
            except queue.Empty:
                # Queue timeout, continue loop
                continue
            except Exception as e:
                logger.error(f"Error in worker thread: {str(e)}")
                logger.error(traceback.format_exc())

def async_task(queue=None, name=None):
    """
    Decorator to run a function as an asynchronous task.
    
    Args:
        queue: TaskQueue instance (uses global queue if None)
        name: Optional task name
        
    Returns:
        Decorated function
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            # Get task queue
            task_queue = queue or get_task_queue()
            
            # Submit task
            return task_queue.submit(func, args, kwargs, name=name or func.__name__)
        
        return wrapped
    
    return decorator

# Global task queue
_global_task_queue = None

def get_task_queue():
    """
    Get the global task queue.
    
    Returns:
        TaskQueue instance
    """
    global _global_task_queue
    
    if _global_task_queue is None:
        _global_task_queue = TaskQueue()
        _global_task_queue.start()
    
    return _global_task_queue

def shutdown_task_queue():
    """
    Shutdown the global task queue.
    """
    global _global_task_queue
    
    if _global_task_queue:
        _global_task_queue.stop()
        _global_task_queue = None
