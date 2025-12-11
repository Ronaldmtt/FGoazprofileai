"""
Centralized logging service for RPA monitoring.
Provides structured logging with event tracking for all system operations.
"""
import logging
import sys
from datetime import datetime
from functools import wraps
import traceback

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

class RPALogger:
    """Structured logger for RPA monitoring system."""
    
    def __init__(self, module_name: str):
        self.logger = logging.getLogger(module_name)
        self.module = module_name
    
    def _format_message(self, event_type: str, action: str, details: dict = None) -> str:
        """Format log message with structured data."""
        msg = f"[{event_type}] {action}"
        if details:
            detail_str = " | ".join([f"{k}={v}" for k, v in details.items()])
            msg += f" | {detail_str}"
        return msg
    
    def event_start(self, action: str, details: dict = None):
        """Log the start of an event/action."""
        msg = self._format_message("START", action, details)
        self.logger.info(msg)
    
    def event_end(self, action: str, details: dict = None):
        """Log the end of an event/action."""
        msg = self._format_message("END", action, details)
        self.logger.info(msg)
    
    def event_success(self, action: str, details: dict = None):
        """Log successful completion of an action."""
        msg = self._format_message("SUCCESS", action, details)
        self.logger.info(msg)
    
    def event_error(self, action: str, error: Exception = None, details: dict = None):
        """Log an error during an action."""
        error_details = details or {}
        if error:
            error_details['error_type'] = type(error).__name__
            error_details['error_message'] = str(error)
        msg = self._format_message("ERROR", action, error_details)
        self.logger.error(msg)
        if error:
            self.logger.error(f"[TRACEBACK] {traceback.format_exc()}")
    
    def event_warning(self, action: str, details: dict = None):
        """Log a warning during an action."""
        msg = self._format_message("WARNING", action, details)
        self.logger.warning(msg)
    
    def event_debug(self, action: str, details: dict = None):
        """Log debug information."""
        msg = self._format_message("DEBUG", action, details)
        self.logger.debug(msg)
    
    def event_info(self, action: str, details: dict = None):
        """Log general information."""
        msg = self._format_message("INFO", action, details)
        self.logger.info(msg)
    
    def user_action(self, user_id: str, action: str, details: dict = None):
        """Log a user-initiated action."""
        action_details = {'user_id': user_id}
        if details:
            action_details.update(details)
        msg = self._format_message("USER_ACTION", action, action_details)
        self.logger.info(msg)
    
    def api_request(self, method: str, endpoint: str, details: dict = None):
        """Log an API request."""
        request_details = {'method': method, 'endpoint': endpoint}
        if details:
            request_details.update(details)
        msg = self._format_message("API_REQUEST", f"{method} {endpoint}", request_details)
        self.logger.info(msg)
    
    def api_response(self, endpoint: str, status_code: int, details: dict = None):
        """Log an API response."""
        response_details = {'status_code': status_code, 'endpoint': endpoint}
        if details:
            response_details.update(details)
        msg = self._format_message("API_RESPONSE", endpoint, response_details)
        self.logger.info(msg)
    
    def db_operation(self, operation: str, table: str, details: dict = None):
        """Log a database operation."""
        db_details = {'operation': operation, 'table': table}
        if details:
            db_details.update(details)
        msg = self._format_message("DB", f"{operation} on {table}", db_details)
        self.logger.info(msg)
    
    def llm_call(self, model: str, action: str, details: dict = None):
        """Log an LLM API call."""
        llm_details = {'model': model}
        if details:
            llm_details.update(details)
        msg = self._format_message("LLM", action, llm_details)
        self.logger.info(msg)


def get_logger(module_name: str) -> RPALogger:
    """Get a logger instance for a specific module."""
    return RPALogger(module_name)


def log_route(action_name: str = None):
    """Decorator for logging route entry and exit."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger('routes')
            route_name = action_name or func.__name__
            logger.event_start(route_name)
            try:
                result = func(*args, **kwargs)
                logger.event_success(route_name)
                logger.event_end(route_name)
                return result
            except Exception as e:
                logger.event_error(route_name, error=e)
                logger.event_end(route_name, details={'status': 'failed'})
                raise
        return wrapper
    return decorator


def log_service(action_name: str = None):
    """Decorator for logging service method calls."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger('services')
            service_name = action_name or func.__name__
            logger.event_start(service_name)
            try:
                result = func(*args, **kwargs)
                logger.event_success(service_name)
                logger.event_end(service_name)
                return result
            except Exception as e:
                logger.event_error(service_name, error=e)
                logger.event_end(service_name, details={'status': 'failed'})
                raise
        return wrapper
    return decorator


admin_logger = get_logger('admin')
auth_logger = get_logger('auth')
assessment_logger = get_logger('assessment')
llm_logger = get_logger('llm')
db_logger = get_logger('database')
export_logger = get_logger('export')
analytics_logger = get_logger('analytics')
agent_logger = get_logger('agents')
