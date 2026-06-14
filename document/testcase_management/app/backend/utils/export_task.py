import uuid
import threading
import time
import os
import logging
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

_tasks = {}
_lock = threading.Lock()
CLEANUP_INTERVAL = 300
MAX_AGE = 3600


class ExportTask:
    def __init__(self, task_id, report_id, format_type, report_name):
        self.task_id = task_id
        self.report_id = report_id
        self.format_type = format_type
        self.report_name = report_name
        self.status = 'pending'
        self.progress = 0
        self.status_message = ''
        self.file_path = None
        self.error = None
        self.created_at = datetime.now()


def _cleanup_old_tasks():
    now = datetime.now()
    with _lock:
        expired = [tid for tid, t in _tasks.items() if now - t.created_at > timedelta(seconds=MAX_AGE)]
        for tid in expired:
            t = _tasks.pop(tid)
            if t.file_path and os.path.exists(t.file_path):
                try:
                    os.remove(t.file_path)
                except OSError:
                    pass
        if expired:
            logger.info(f"[ExportTask] 清理过期任务: {len(expired)}个")


def start_export(report_id, format_type, report_name, target_func, *args, **kwargs):
    task_id = str(uuid.uuid4())
    task = ExportTask(task_id, report_id, format_type, report_name)
    with _lock:
        _tasks[task_id] = task

    def _run():
        try:
            task.status = 'processing'
            result = target_func(*args, **kwargs)
            file_path, filename = result
            with _lock:
                task.file_path = file_path
                task.report_name = filename
                task.status = 'completed'
                task.progress = 100
            logger.info(f"[ExportTask] 导出完成 task_id={task_id} file={file_path}")
        except Exception as e:
            with _lock:
                task.status = 'failed'
                task.error = str(e)
            logger.error(f"[ExportTask] 导出失败 task_id={task_id} error={e}")

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()

    if len(_tasks) % 10 == 0:
        _cleanup_old_tasks()

    return task_id


def get_task(task_id):
    with _lock:
        return _tasks.get(task_id)


def get_task_status(task_id):
    task = get_task(task_id)
    if not task:
        return None
    return {
        'task_id': task.task_id,
        'status': task.status,
        'progress': task.progress,
        'status_message': task.status_message,
        'error': task.error,
        'report_name': task.report_name,
    }


def set_progress(task_id, progress, message=None):
    with _lock:
        task = _tasks.get(task_id)
        if not task:
            return
        task.progress = progress
        if message is not None:
            task.status_message = message
