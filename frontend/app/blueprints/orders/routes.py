import os
import uuid
from flask import render_template, request, redirect, url_for, flash, abort, current_app
from flask_login import current_user
from app.blueprints.orders import orders_bp
from app.utils.api_client import APIClient
from app.utils.decorators import admin_required


# ─────────────────────────────────────────────────────────────────────────────
# List buildings assigned to the current admin
# ─────────────────────────────────────────────────────────────────────────────
@orders_bp.route('/buildings')
@admin_required
def list_buildings():
    """List buildings assigned to the current logged-in admin."""
    api = APIClient(current_user.id)
    try:
        buildings = api.get('/buildings/')
        return render_template('orders/list_buildings.html', buildings=buildings, user=current_user)
    except Exception as e:
        flash(f'Error al listar edificios: {str(e)}', 'error')
        return render_template('orders/list_buildings.html', buildings=[], user=current_user)


# ─────────────────────────────────────────────────────────────────────────────
# Create a new draft order for a building
# ─────────────────────────────────────────────────────────────────────────────
@orders_bp.route('/create/<int:building_id>', methods=['POST'])
@admin_required
def create_order(building_id):
    """Create a new draft order for the selected building."""
    api = APIClient(current_user.id)
    try:
        order_data = {"building_id": building_id}
        order = api.post('/orders/', json=order_data)
        
        if order.get('status') == 'draft':
            flash(f'Pedido en borrador abierto.', 'info')
        
        return redirect(url_for('orders.order_detail', order_id=order['id']))
    except Exception as e:
        flash(f'Error al crear pedido: {str(e)}', 'error')
        return redirect(url_for('orders.list_buildings'))


# ─────────────────────────────────────────────────────────────────────────────
# View the details of a specific order
# ─────────────────────────────────────────────────────────────────────────────
@orders_bp.route('/<int:order_id>')
@admin_required
def order_detail(order_id):
    """View the details of a specific order (draft) and allow adding products."""
    api = APIClient(current_user.id)
    try:
        order = api.get(f'/orders/{order_id}')
        products = api.get('/catalog/')

        critical_inventory = []
        inventory = api.get('/inventory/', params={'building_id': order['building_id']})
        for inv in inventory:
            if inv['quantity'] < inv['product']['stock_minimo']:
                critical_inventory.append(inv)

        return render_template('orders/order_detail.html', order=order, products=products, critical_inventory=critical_inventory)
    except Exception as e:
        flash(f'Error al cargar pedido: {str(e)}', 'error')
        return redirect(url_for('orders.list_buildings'))

@orders_bp.route('/<int:order_id>/receive', methods=['POST'])
@admin_required
def receive_order(order_id):
    """Confirm receipt of a dispatched order and increase local building inventory."""
    api = APIClient(current_user.id)
    try:
        api.post(f'/orders/{order_id}/receive')
        flash('¡Recepción confirmada! El stock ha ingresado a tu inventario local.', 'success')
    except Exception as e:
        flash(f'Error al confirmar recepción: {str(e)}', 'error')
    
    return redirect(url_for('dashboard.index'))


# ─────────────────────────────────────────────────────────────────────────────
# HTMX: Add an item to the order
# ─────────────────────────────────────────────────────────────────────────────
@orders_bp.route('/<int:order_id>/add_item', methods=['POST'])
@admin_required
def add_item(order_id):
    """HTMX endpoint to add an item to the order."""
    api = APIClient(current_user.id)
    product_id = request.form.get('product_id', type=int)
    quantity = request.form.get('quantity', 1, type=int)
    
    try:
        item_data = {"product_id": product_id, "quantity": quantity}
        api.post(f'/orders/{order_id}/items', json=item_data)
        
        # Get updated order for partial render
        order = api.get(f'/orders/{order_id}')
        return render_template('orders/partials/order_items.html', order=order)
    except Exception as e:
        return f'<div class="alert alert-danger">{str(e)}</div>', 400


# ─────────────────────────────────────────────────────────────────────────────
# HTMX: Remove an item from the order
# ─────────────────────────────────────────────────────────────────────────────
@orders_bp.route('/<int:order_id>/remove_item/<int:item_id>', methods=['POST'])
@admin_required
def remove_item(order_id, item_id):
    """HTMX endpoint to remove an item from the order."""
    api = APIClient(current_user.id)
    try:
        api.delete(f'/orders/{order_id}/items/{item_id}')
        # Get updated order for partial render
        order = api.get(f'/orders/{order_id}')
        return render_template('orders/partials/order_items.html', order=order)
    except Exception as e:
        return f'<div class="alert alert-danger">{str(e)}</div>', 400


# ─────────────────────────────────────────────────────────────────────────────
# Submit the order (draft → submitted)
# ─────────────────────────────────────────────────────────────────────────────
@orders_bp.route('/<int:order_id>/submit', methods=['POST'])
@admin_required
def submit_order(order_id):
    """Move an order from 'draft' to 'submitted'."""
    api = APIClient(current_user.id)
    try:
        api.post(f'/orders/{order_id}/submit')
        flash(f'Pedido enviado correctamente. El almacén lo procesará pronto.', 'success')
    except Exception as e:
        flash(f'Error al enviar pedido: {str(e)}', 'error')
    
    return redirect(url_for('dashboard.index'))


# ─────────────────────────────────────────────────────────────────────────────
# Reopen a submitted order for editing (submitted → draft)
# ─────────────────────────────────────────────────────────────────────────────
@orders_bp.route('/<int:order_id>/reopen', methods=['POST'])
@admin_required
def reopen_order(order_id):
    """Move an order from 'submitted' back to 'draft' so the admin can edit it."""
    api = APIClient(current_user.id)
    try:
        api.post(f'/orders/{order_id}/reopen')
        flash('El pedido se ha reabierto.', 'info')
    except Exception as e:
        flash(f'Error al reabrir pedido: {str(e)}', 'error')
        
    return redirect(url_for('orders.order_detail', order_id=order_id))


# ─────────────────────────────────────────────────────────────────────────────
# Local Inventory Phase 2
# ─────────────────────────────────────────────────────────────────────────────
@orders_bp.route('/my_inventory')
@admin_required
def my_inventory():
    """View local building inventory for the current admin."""
    api = APIClient(current_user.id)
    try:
        inventory = api.get('/inventory/')
        return render_template('orders/my_inventory.html', inventory=inventory)
    except Exception as e:
        flash(f'Error al cargar inventario: {str(e)}', 'error')
        return render_template('orders/my_inventory.html', inventory=[])

@orders_bp.route('/consume/<int:inventory_id>', methods=['POST'])
@admin_required
def consume_inventory(inventory_id):
    """HTMX endpoint to report consumption of local inventory."""
    api = APIClient(current_user.id)
    quantity = request.form.get('quantity', 1, type=int)
    
    try:
        consume_data = {"quantity": quantity}
        inv = api.post(f'/inventory/{inventory_id}/consume', json=consume_data)
        return render_template('orders/partials/inventory_card.html', inv=inv)
    except Exception as e:
        return f'<div class="alert alert-danger">{str(e)}</div>', 400


@orders_bp.route('/adjust_stock/<int:inventory_id>', methods=['POST'])
@admin_required
def adjust_stock(inventory_id):
    """HTMX endpoint to manually adjust stock."""
    api = APIClient(current_user.id)
    action = request.form.get('action')
    quantity = request.form.get('quantity', 1, type=int)
    
    try:
        # First get current to calculate new total if needed, or if API supports +/-
        # Our the backend adjust seems to set absolute value based onschemas
        # So we need to fetch first
        curr = api.get(f'/inventory/{inventory_id}')
        new_qty = curr['quantity'] + quantity if action == 'add' else curr['quantity'] - quantity
        
        adjust_data = {"quantity": max(0, new_qty)}
        api.post(f'/inventory/{inventory_id}/adjust', json=adjust_data)
        
        flash(f'Stock actualizado correctamente.', 'success')
    except Exception as e:
        flash(f'Error al ajustar stock: {str(e)}', 'error')
        
    return redirect(url_for('orders.my_inventory'))


@orders_bp.route('/my_orders')
@admin_required
def my_orders():
    """Full paginated order history with state tracking for the current admin."""
    api = APIClient(current_user.id)
    status_filter = request.args.get('status', '')
    building_filter = request.args.get('building_id', type=int)

    try:
        params = {}
        if status_filter: params['status'] = status_filter
        if building_filter: params['building_id'] = building_filter
        
        orders = api.get('/orders/', params=params)
        buildings = api.get('/buildings/')
        
        return render_template('orders/my_orders.html',
            orders=orders, buildings=buildings,
            status_filter=status_filter, building_filter=building_filter)
    except Exception as e:
        flash(f'Error al cargar histórico: {str(e)}', 'error')
        return render_template('orders/my_orders.html', orders=[], buildings=[], status_filter=status_filter)


@orders_bp.route('/<int:order_id>/cancel', methods=['POST'])
@admin_required
def cancel_order(order_id):
    """Cancel a draft or submitted order."""
    api = APIClient(current_user.id)
    try:
        api.post(f'/orders/{order_id}/cancel')
        flash(f'Pedido cancelado.', 'info')
    except Exception as e:
        flash(f'Error al cancelar: {str(e)}', 'error')
    return redirect(url_for('orders.my_orders'))


@orders_bp.route('/consumption_report')
@admin_required
def consumption_report():
    """View consumption logs grouped by building and product."""
    api = APIClient(current_user.id)
    building_filter = request.args.get('building_id', type=int)
    
    try:
        params = {}
        if building_filter: params['building_id'] = building_filter
        
        rows = api.get('/orders/consumption-report', params=params)
        buildings = api.get('/buildings/')
        
        return render_template('orders/consumption_report.html',
            rows=rows, buildings=buildings,
            building_filter=building_filter)
    except Exception as e:
        flash(f'Error al cargar reporte: {str(e)}', 'error')
        return render_template('orders/consumption_report.html', rows=[], buildings=[], building_filter=building_filter)


@orders_bp.route('/add_inventory', methods=['GET', 'POST'])
@admin_required
def add_inventory_item():
    """Add a new product to local building inventory."""
    api = APIClient(current_user.id)
    if request.method == 'POST':
        product_id = request.form.get('product_id', type=int)
        building_id = request.form.get('building_id', type=int)
        quantity = request.form.get('quantity', 1, type=int)
        
        try:
            inv_data = {
                "product_id": product_id,
                "building_id": building_id,
                "quantity": quantity
            }
            api.post('/inventory/', json=inv_data)
            flash(f'Producto agregado al inventario del edificio.', 'success')
            return redirect(url_for('orders.my_inventory'))
        except Exception as e:
            flash(f'Error al agregar inventario: {str(e)}', 'error')
            return redirect(url_for('orders.add_inventory_item'))
    
    try:
        buildings = api.get('/buildings/')
        products = api.get('/catalog/')
        return render_template('orders/add_inventory.html', buildings=buildings, products=products)
    except Exception as e:
        flash(f'Error al cargar datos: {str(e)}', 'error')
        return render_template('orders/add_inventory.html', buildings=[], products=[])
