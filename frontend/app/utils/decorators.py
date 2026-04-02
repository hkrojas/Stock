from functools import wraps
from flask import abort, current_app, session
from flask_login import current_user, login_required

def superadmin_required(f):
    """Decorator that requires the user to be logged in AND have the 'superadmin' role."""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'superadmin' or session.get('view_as_admin'):
            abort(403)
        return current_app.ensure_sync(f)(*args, **kwargs)
    return decorated_function

def management_required(f):
    """Decorator that requires the user to be logged in AND have 'manager' or 'superadmin' role."""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        # Superadmins should always have access to management tools unless we want strict emulation.
        # But even then, blocking the warehouse might be too much.
        is_management = current_user.role in ('manager', 'superadmin')
        if not current_user.is_authenticated or not is_management:
            abort(403)
        # Only block managers/superadmins if they are explicitly viewing as a regular admin AND the route is management-only.
        # We allow superadmins to bypass the toggle for critical views like the warehouse.
        if session.get('view_as_admin') and current_user.role != 'superadmin':
            abort(403)
        return current_app.ensure_sync(f)(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator that requires the user to be logged in AND have the 'admin' role."""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ('admin', 'superadmin'):
            abort(403)
        return current_app.ensure_sync(f)(*args, **kwargs)
    return decorated_function
