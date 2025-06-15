"""
Async operations and background task management.
"""
import asyncio
import threading
from typing import Callable, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor
from gi.repository import GLib, GObject
from .services import PasswordService
from .managers import ToastManager


class BackgroundTask(GObject.Object):
    """Represents a background task with progress tracking."""
    
    __gsignals__ = {
        'progress': (GObject.SignalFlags.RUN_FIRST, None, (float, str)),
        'completed': (GObject.SignalFlags.RUN_FIRST, None, (bool, object)),
        'error': (GObject.SignalFlags.RUN_FIRST, None, (str,))
    }
    
    def __init__(self, name: str, description: str):
        super().__init__()
        self.name = name
        self.description = description
        self.is_running = False
        self.is_cancelled = False
        self.progress = 0.0
        self.result = None
        self.error = None
    
    def update_progress(self, progress: float, status: str = ""):
        """Update task progress."""
        self.progress = progress
        self.emit('progress', progress, status)
    
    def complete(self, success: bool, result: Any = None):
        """Mark task as completed."""
        self.is_running = False
        self.result = result
        self.emit('completed', success, result)
    
    def fail(self, error_message: str):
        """Mark task as failed."""
        self.is_running = False
        self.error = error_message
        self.emit('error', error_message)
    
    def cancel(self):
        """Cancel the task."""
        self.is_cancelled = True


class AsyncPasswordOperations:
    """Handles async password operations to prevent UI blocking."""
    
    def __init__(self, password_service: PasswordService, toast_manager: ToastManager):
        self.password_service = password_service
        self.toast_manager = toast_manager
        self.executor = ThreadPoolExecutor(max_workers=3)
        self._running_tasks = {}
    
    def load_passwords_async(self, callback: Callable[[bool, list], None]) -> BackgroundTask:
        """Load passwords asynchronously."""
        task = BackgroundTask("load_passwords", "Loading passwords...")
        
        def worker():
            try:
                task.update_progress(0.1, "Initializing...")
                
                if not self.password_service.is_initialized():
                    task.fail("Password store not initialized")
                    return
                
                task.update_progress(0.3, "Reading password store...")
                entries = self.password_service.get_all_entries()
                
                task.update_progress(0.8, "Processing entries...")
                # Simulate some processing time for large stores
                if len(entries) > 100:
                    import time
                    time.sleep(0.1)
                
                task.update_progress(1.0, "Complete")
                task.complete(True, entries)
                
                # Call callback on main thread
                GLib.idle_add(lambda: callback(True, entries))
                
            except Exception as e:
                error_msg = f"Failed to load passwords: {e}"
                task.fail(error_msg)
                GLib.idle_add(lambda: callback(False, []))
        
        task.is_running = True
        self.executor.submit(worker)
        return task
    
    def search_passwords_async(self, query: str, callback: Callable[[bool, list], None]) -> BackgroundTask:
        """Search passwords asynchronously."""
        task = BackgroundTask("search_passwords", f"Searching for '{query}'...")
        
        def worker():
            try:
                task.update_progress(0.2, "Starting search...")
                
                success, entries = self.password_service.search_entries(query)
                
                if not success:
                    task.fail("Search failed")
                    GLib.idle_add(lambda: callback(False, []))
                    return
                
                task.update_progress(0.8, f"Found {len(entries)} results")
                task.update_progress(1.0, "Search complete")
                task.complete(True, entries)
                
                GLib.idle_add(lambda: callback(True, entries))
                
            except Exception as e:
                error_msg = f"Search error: {e}"
                task.fail(error_msg)
                GLib.idle_add(lambda: callback(False, []))
        
        task.is_running = True
        self.executor.submit(worker)
        return task
    
    def get_entry_details_async(self, path: str, callback: Callable[[bool, Any], None]) -> BackgroundTask:
        """Get password entry details asynchronously."""
        task = BackgroundTask("get_details", f"Loading details for {path}...")
        
        def worker():
            try:
                task.update_progress(0.3, "Decrypting...")
                
                success, entry = self.password_service.get_entry_details(path)
                
                task.update_progress(0.8, "Processing details...")
                
                if not success:
                    task.fail("Failed to load entry details")
                    GLib.idle_add(lambda: callback(False, None))
                    return
                
                task.update_progress(1.0, "Complete")
                task.complete(True, entry)
                
                GLib.idle_add(lambda: callback(True, entry))
                
            except Exception as e:
                error_msg = f"Failed to get details: {e}"
                task.fail(error_msg)
                GLib.idle_add(lambda: callback(False, None))
        
        task.is_running = True
        self.executor.submit(worker)
        return task
    
    def save_entry_async(self, path: str, content: str, is_new: bool, 
                        callback: Callable[[bool, str], None]) -> BackgroundTask:
        """Save password entry asynchronously."""
        action = "Creating" if is_new else "Updating"
        task = BackgroundTask("save_entry", f"{action} {path}...")
        
        def worker():
            try:
                task.update_progress(0.2, "Validating...")
                
                if is_new:
                    success, message = self.password_service.create_entry(path, content)
                else:
                    success, message = self.password_service.update_entry(path, content)
                
                task.update_progress(0.8, "Saving...")
                
                if success:
                    task.update_progress(1.0, "Saved successfully")
                    task.complete(True, message)
                else:
                    task.fail(message)
                
                GLib.idle_add(lambda: callback(success, message))
                
            except Exception as e:
                error_msg = f"Failed to save entry: {e}"
                task.fail(error_msg)
                GLib.idle_add(lambda: callback(False, error_msg))
        
        task.is_running = True
        self.executor.submit(worker)
        return task
    
    def git_operation_async(self, operation: str, callback: Callable[[bool, str], None]) -> BackgroundTask:
        """Perform git operations asynchronously."""
        task = BackgroundTask("git_operation", f"Git {operation}...")
        
        def worker():
            try:
                task.update_progress(0.1, f"Starting git {operation}...")
                
                if operation == "pull":
                    success, message = self.password_service.sync_pull()
                elif operation == "push":
                    success, message = self.password_service.sync_push()
                else:
                    task.fail(f"Unknown git operation: {operation}")
                    GLib.idle_add(lambda: callback(False, f"Unknown operation: {operation}"))
                    return
                
                task.update_progress(0.8, f"Git {operation} in progress...")
                
                if success:
                    task.update_progress(1.0, f"Git {operation} completed")
                    task.complete(True, message)
                else:
                    task.fail(message)
                
                GLib.idle_add(lambda: callback(success, message))
                
            except Exception as e:
                error_msg = f"Git {operation} failed: {e}"
                task.fail(error_msg)
                GLib.idle_add(lambda: callback(False, error_msg))
        
        task.is_running = True
        self.executor.submit(worker)
        return task
    
    def shutdown(self):
        """Shutdown the executor and cancel running tasks."""
        self.executor.shutdown(wait=False)


class TaskManager(GObject.Object):
    """Manages background tasks and provides UI feedback."""
    
    __gsignals__ = {
        'task-started': (GObject.SignalFlags.RUN_FIRST, None, (object,)),
        'task-completed': (GObject.SignalFlags.RUN_FIRST, None, (object,)),
        'task-failed': (GObject.SignalFlags.RUN_FIRST, None, (object, str))
    }
    
    def __init__(self, toast_manager: ToastManager):
        super().__init__()
        self.toast_manager = toast_manager
        self.active_tasks = {}
        self.task_counter = 0
    
    def add_task(self, task: BackgroundTask) -> int:
        """Add a task to be managed."""
        task_id = self.task_counter
        self.task_counter += 1
        
        self.active_tasks[task_id] = task
        
        # Connect signals
        task.connect('progress', self._on_task_progress)
        task.connect('completed', self._on_task_completed, task_id)
        task.connect('error', self._on_task_error, task_id)
        
        self.emit('task-started', task)
        self.toast_manager.show_info(f"Started: {task.description}")
        
        return task_id
    
    def _on_task_progress(self, task: BackgroundTask, progress: float, status: str):
        """Handle task progress updates."""
        # Could update a progress bar in the UI
        pass
    
    def _on_task_completed(self, task: BackgroundTask, success: bool, result: Any, task_id: int):
        """Handle task completion."""
        if task_id in self.active_tasks:
            del self.active_tasks[task_id]
        
        if success:
            self.toast_manager.show_success(f"Completed: {task.description}")
            self.emit('task-completed', task)
        else:
            self.toast_manager.show_error(f"Failed: {task.description}")
            self.emit('task-failed', task, "Task failed")
    
    def _on_task_error(self, task: BackgroundTask, error_message: str, task_id: int):
        """Handle task errors."""
        if task_id in self.active_tasks:
            del self.active_tasks[task_id]
        
        self.toast_manager.show_error(f"Error: {task.description} - {error_message}")
        self.emit('task-failed', task, error_message)
    
    def cancel_all_tasks(self):
        """Cancel all active tasks."""
        for task in self.active_tasks.values():
            task.cancel()
        self.active_tasks.clear()
    
    def get_active_task_count(self) -> int:
        """Get number of active tasks."""
        return len(self.active_tasks)
