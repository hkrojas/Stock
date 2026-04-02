from flask import current_app, jsonify, render_template, session
import requests
from flask_login import current_user, login_required
from app.blueprints.dashboard import dashboard_bp
from app.utils.api_client import APIClient


@dashboard_bp.route('/')
@login_required
def index():
    """Main hub: renders superadmin analytics OR admin operations panel, based on role."""
    api = APIClient(current_user.id)

    # ── Manager route: warehouse operations dashboard ──
    if current_user.role == 'manager' and not session.get('view_as_admin'):
        try:
            data = api.get('/analytics/manager')
            return render_template('dashboard/manager_dashboard.html',
                pedidos_submitted=data.get('pedidos_submitted'),
                lotes_pendientes=data.get('lotes_pendientes'),
                alertas_stock=data.get('alertas_stock'),
                compras_recientes=data.get('compras_recientes'),
            )
        except Exception as e:
            return f"Error al cargar dashboard de manager: {str(e)}", 500

    # ── Admin route: show the admin's operational dashboard ──
    if current_user.role == 'admin' or session.get('view_as_admin'):
        try:
            data = api.get('/analytics/admin')
            return render_template('dashboard/admin_dashboard.html',
                buildings=data.get('buildings'),
                pedidos_activos=data.get('pedidos_activos'),
                pedidos_en_transito=data.get('pedidos_en_transito'),
                historial_pedidos=data.get('historial_pedidos'),
                pedidos_despachados=data.get('pedidos_despachados'),
            )
        except Exception as e:
            return f"Error al cargar dashboard de administrador: {str(e)}", 500

    # ── Superadmin route: full analytics dashboard ──
    try:
        data = api.get('/analytics/superadmin')
        return render_template('dashboard/index.html',
            total_pedidos_pendientes=data.get('total_pedidos_pendientes'),
            total_edificios_activos=data.get('total_edificios_activos'),
            costo_despachado_mes=data.get('costo_despachado_mes'),
            total_productos=data.get('total_productos'),
            alertas_stock=data.get('alertas_stock'),
            costos_por_edificio=data.get('costos_por_edificio'),
            chart_edificios_labels=data.get('chart_edificios_labels'),
            chart_edificios_data=data.get('chart_edificios_data'),
            chart_productos_labels=data.get('chart_productos_labels'),
            chart_productos_data=data.get('chart_productos_data'),
            lotes_recientes=data.get('lotes_recientes')
        )
    except Exception as e:
        return f"Error al cargar dashboard de superadmin: {str(e)}", 500

@dashboard_bp.route('/api_status')
@login_required
def api_status():
    """Check if the FastAPI backend is reachable."""
    try:
        api_base = current_app.config["API_BASE_URL"]
        health_url = api_base.rsplit("/api/v1", 1)[0] + "/health"
        response = requests.get(health_url, timeout=2)
        if response.status_code == 200:
            return jsonify({"status": "online", "message": "Backend connected"}), 200
        else:
            return jsonify({"status": "error", "message": f"Backend returned {response.status_code}"}), 500
    except Exception:
        return jsonify({"status": "offline", "message": "Backend unreachable"}), 500
