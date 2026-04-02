import os
import uuid
from flask import render_template, request, flash, redirect, url_for, current_app, jsonify
from flask_login import current_user
from app.blueprints.catalog import catalog_bp
from app.utils.decorators import management_required
from app.utils.api_client import APIClient


# ─────────────────────────────────────────────────────────────────────────────
# Assign Building to Admin
# ─────────────────────────────────────────────────────────────────────────────
@catalog_bp.route('/assign_building', methods=['GET', 'POST'])
@management_required
async def assign_building():
    api = APIClient(current_user.id)
    if request.method == 'POST':
        admin_id = request.form.get('admin_id')
        building_ids = request.form.getlist('building_ids')

        if admin_id and building_ids:
            try:
                # Convert building_ids to integers
                b_ids = [int(bid) for bid in building_ids if bid and bid != 'none']
                if b_ids:
                    await api.post('/buildings/assign', json={"admin_id": int(admin_id), "building_ids": b_ids})
                    flash('Edificios asignados correctamente.', 'success')
                else:
                    flash('No se especificaron edificios válidos.', 'error')
            except Exception as e:
                flash(f'Error al asignar edificios: {str(e)}', 'error')
        else:
            flash('Selecciona tanto al administrador como al menos un edificio.', 'error')
        return redirect(url_for('catalog.assign_building'))

    try:
        admins = await api.get('/users/', params={'role': 'admin'})
        buildings = await api.get('/buildings/')
        return render_template('catalog/assign_building.html', admins=admins, buildings=buildings)
    except Exception as e:
        flash(f'Error al cargar datos: {str(e)}', 'error')
        return redirect(url_for('dashboard.index'))


# ─────────────────────────────────────────────────────────────────────────────
# Create New Building
# ─────────────────────────────────────────────────────────────────────────────
@catalog_bp.route('/buildings/new', methods=['GET', 'POST'])
@management_required
async def create_building():
    api = APIClient(current_user.id)
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        address = request.form.get('address', '').strip()
        departments_count = request.form.get('departments_count', type=int, default=0)
        admin_id = request.form.get('admin_id') or None

        imagen_frontis = None
        if 'imagen_frontis' in request.files:
            file = request.files['imagen_frontis']
            if file.filename:
                ext = os.path.splitext(file.filename)[1]
                filename = f"{uuid.uuid4().hex}{ext}"
                upload_path = os.path.join(current_app.root_path, 'static', 'uploads')
                os.makedirs(upload_path, exist_ok=True)
                file.save(os.path.join(upload_path, filename))
                imagen_frontis = filename

        if not name:
            flash('El nombre del edificio es obligatorio.', 'error')
            return redirect(url_for('catalog.create_building'))

        try:
            building_data = {
                "name": name,
                "address": address,
                "departments_count": departments_count,
                "admin_id": int(admin_id) if admin_id and admin_id != 'none' else None,
                "imagen_frontis": imagen_frontis
            }
            await api.post('/buildings/', json=building_data)
            flash(f'Edificio "{name}" creado correctamente.', 'success')
            return redirect(url_for('catalog.list_buildings'))
        except Exception as e:
             flash(f'Error al crear edificio: {str(e)}', 'error')
             return redirect(url_for('catalog.create_building'))

    try:
        admins = await api.get('/users/', params={'role': 'admin'})
        return render_template('catalog/create_building.html', admins=admins)
    except Exception as e:
        flash(f'Error al cargar administradores: {str(e)}', 'error')
        return render_template('catalog/create_building.html', admins=[])


# ─────────────────────────────────────────────────────────────────────────────
# List Buildings
# ─────────────────────────────────────────────────────────────────────────────
@catalog_bp.route('/buildings', methods=['GET'])
@management_required
async def list_buildings():
    api = APIClient(current_user.id)
    try:
        buildings = await api.get('/buildings/')
        return render_template('catalog/list_buildings_admin.html', buildings=buildings)
    except Exception as e:
        flash(f'Error al listar edificios: {str(e)}', 'error')
        return render_template('catalog/list_buildings_admin.html', buildings=[])


# ─────────────────────────────────────────────────────────────────────────────
# Edit Building
# ─────────────────────────────────────────────────────────────────────────────
@catalog_bp.route('/buildings/<int:building_id>/edit', methods=['GET', 'POST'])
@management_required
async def edit_building(building_id):
    api = APIClient(current_user.id)
    try:
        building = await api.get(f'/buildings/{building_id}')
    except Exception as e:
        flash(f'Edificio no encontrado: {str(e)}', 'error')
        return redirect(url_for('catalog.list_buildings'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        address = request.form.get('address', '').strip()
        departments_count = request.form.get('departments_count', type=int, default=0)
        admin_id = request.form.get('admin_id')

        if not name:
            flash('El nombre del edificio es obligatorio.', 'error')
            return redirect(url_for('catalog.edit_building', building_id=building_id))

        update_data = {
            "name": name,
            "address": address,
            "departments_count": departments_count,
            "admin_id": int(admin_id) if admin_id and admin_id != 'none' else None
        }

        if 'imagen_frontis' in request.files:
            file = request.files['imagen_frontis']
            if file.filename:
                ext = os.path.splitext(file.filename)[1]
                filename = f"{uuid.uuid4().hex}{ext}"
                upload_path = os.path.join(current_app.root_path, 'static', 'uploads')
                os.makedirs(upload_path, exist_ok=True)
                file.save(os.path.join(upload_path, filename))
                update_data["imagen_frontis"] = filename

        try:
            await api.put(f'/buildings/{building_id}', json=update_data)
            flash(f'Edificio "{name}" actualizado correctamente.', 'success')
            return redirect(url_for('catalog.list_buildings'))
        except Exception as e:
            flash(f'Error al actualizar edificio: {str(e)}', 'error')
            return redirect(url_for('catalog.edit_building', building_id=building_id))

    try:
        admins = await api.get('/users/', params={'role': 'admin'})
        return render_template('catalog/edit_building.html', building=building, admins=admins)
    except Exception as e:
        flash(f'Error al cargar administradores: {str(e)}', 'error')
        return render_template('catalog/edit_building.html', building=building, admins=[])


# ─────────────────────────────────────────────────────────────────────────────
# Delete Building
# ─────────────────────────────────────────────────────────────────────────────
@catalog_bp.route('/buildings/<int:building_id>/delete', methods=['POST'])
@management_required
async def delete_building(building_id):
    api = APIClient(current_user.id)
    try:
        await api.delete(f'/buildings/{building_id}')
        flash('Edificio eliminado correctamente.', 'success')
    except Exception as e:
        flash(f'Error al eliminar: {str(e)}', 'error')
    return redirect(url_for('catalog.list_buildings'))

# ─────────────────────────────────────────────────────────────────────────────
# Create New Admin User
# ─────────────────────────────────────────────────────────────────────────────
@catalog_bp.route('/admins/new', methods=['GET', 'POST'])
@management_required
async def create_admin():
    api = APIClient(current_user.id)
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        confirm  = request.form.get('confirm_password', '').strip()
        role = request.form.get('role', 'admin')

        if not username or not password:
            flash('Usuario y contraseña son obligatorios.', 'error')
            return redirect(url_for('catalog.create_admin'))

        if role not in ['admin', 'manager']:
            flash('El rol seleccionado no es válido.', 'error')
            return redirect(url_for('catalog.create_admin'))

        if role == 'manager' and current_user.role != 'superadmin':
            flash('Solo un Superadmin puede asignar el rol de Manager.', 'error')
            return redirect(url_for('catalog.create_admin'))

        if password != confirm:
            flash('Las contraseñas no coinciden.', 'error')
            return redirect(url_for('catalog.create_admin'))

        if len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres.', 'error')
            return redirect(url_for('catalog.create_admin'))

        try:
            user_data = {
                "username": username,
                "name": name,
                "password": password,
                "role": role
            }
            await api.post('/users/', json=user_data)
            flash(f'Administrador "{username}" creado correctamente.', 'success')
            return redirect(url_for('catalog.list_admins'))
        except Exception as e:
            flash(f'Error al crear administrador: {str(e)}', 'error')
            return redirect(url_for('catalog.create_admin'))

    return render_template('catalog/create_admin.html')


# ─────────────────────────────────────────────────────────────────────────────
# List Admins
# ─────────────────────────────────────────────────────────────────────────────
@catalog_bp.route('/admins', methods=['GET'])
@management_required
async def list_admins():
    api = APIClient(current_user.id)
    try:
        admins = await api.get('/users/')
        # Find active building for each admin if any
        admin_buildings = {}
        for admin in admins:
            admin_buildings[admin['id']] = [b['name'] for b in admin.get('assigned_buildings', [])]
        return render_template('catalog/list_admins.html', admins=admins, admin_buildings=admin_buildings)
    except Exception as e:
        flash(f'Error al listar administradores: {str(e)}', 'error')
        return render_template('catalog/list_admins.html', admins=[], admin_buildings={})


# ─────────────────────────────────────────────────────────────────────────────
# Edit Admin
# ─────────────────────────────────────────────────────────────────────────────
@catalog_bp.route('/admins/<int:admin_id>/edit', methods=['GET', 'POST'])
@management_required
async def edit_admin(admin_id):
    api = APIClient(current_user.id)
    try:
        admin = await api.get(f'/users/{admin_id}')
    except Exception as e:
        flash(f'Administrador no encontrado: {str(e)}', 'error')
        return redirect(url_for('catalog.list_admins'))

    if admin['role'] == 'superadmin':
        flash('No puedes editar cuentas de Superadmin.', 'error')
        return redirect(url_for('catalog.list_admins'))

    if admin['role'] == 'manager' and current_user.role != 'superadmin' and current_user.id != admin['id']:
        flash('Solo un Superadmin puede editar a otros Managers.', 'error')
        return redirect(url_for('catalog.list_admins'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        role = request.form.get('role')
        building_ids = request.form.getlist('building_ids')

        if not name or not username:
            flash('Nombre y usuario son obligatorios.', 'error')
            return redirect(url_for('catalog.edit_admin', admin_id=admin_id))

        try:
            user_data = {
                "name": name,
                "username": username
            }
            if role in ['admin', 'manager']:
                if role == 'manager' and current_user.role != 'superadmin':
                    flash('Solo un Superadmin puede asignar el rol de Manager.', 'error')
                else:
                    user_data["role"] = role

            if password:
                if len(password) < 6:
                    flash('La nueva contraseña debe tener al menos 6 caracteres.', 'error')
                else:
                    user_data["password"] = password

            # Re-assign buildings if building_ids is provided
            b_ids = [int(bid) for bid in building_ids if bid and bid != 'none']
            
            await api.put(f'/users/{admin_id}', json=user_data, params={'building_ids': b_ids} if building_ids else None)
            flash(f'Administrador "{name}" actualizado correctamente.', 'success')
            return redirect(url_for('catalog.list_admins'))
        except Exception as e:
            flash(f'Error al actualizar: {str(e)}', 'error')
            return redirect(url_for('catalog.edit_admin', admin_id=admin_id))

    try:
        buildings = await api.get('/buildings/')
        assigned = admin.get('assigned_buildings', [])
        assigned_building_ids = [building['id'] for building in assigned]
        current_building = assigned[0] if assigned else None
        return render_template(
            'catalog/edit_admin.html',
            admin=admin,
            buildings=buildings,
            current_building=current_building,
            assigned_building_ids=assigned_building_ids,
        )
    except Exception as e:
        flash(f'Error al cargar datos suplementarios: {str(e)}', 'error')
        return render_template('catalog/edit_admin.html', admin=admin, buildings=[], current_building=None, assigned_building_ids=[])


# ─────────────────────────────────────────────────────────────────────────────
# Delete Admin
# ─────────────────────────────────────────────────────────────────────────────
@catalog_bp.route('/admins/<int:admin_id>/delete', methods=['POST'])
@management_required
async def delete_admin(admin_id):
    api = APIClient(current_user.id)
    try:
        await api.delete(f'/users/{admin_id}')
        flash('Administrador eliminado correctamente.', 'success')
    except Exception as e:
        flash(f'Error al eliminar administrador: {str(e)}', 'error')
    return redirect(url_for('catalog.list_admins'))

# ─────────────────────────────────────────────────────────────────────────────
# CSV Upload for Product Catalog
# ─────────────────────────────────────────────────────────────────────────────
@catalog_bp.route('/upload', methods=['GET', 'POST'])
@management_required
async def upload_csv():
    """Upload a CSV file to create or update products in the master catalog."""
    api = APIClient(current_user.id)
    if request.method == 'POST':
        if 'csv_file' not in request.files:
            flash('No se seleccionó ningún archivo.', 'error')
            return redirect(url_for('catalog.upload_csv'))

        file = request.files['csv_file']
        if file.filename == '':
            flash('No se seleccionó ningún archivo.', 'error')
            return redirect(url_for('catalog.upload_csv'))

        try:
            # Call FastAPI import endpoint
            files = {'file': (file.filename, file.stream, 'text/csv')}
            result = await api.post('/catalog/import-csv', files=files)
            
            created = result.get('products_created', 0)
            updated = result.get('products_updated', 0)
            
            if created or updated:
                flash(f'CSV procesado: {created} creados, {updated} actualizados.', 'success')
            else:
                flash('No se procesaron productos nuevos.', 'info')
                
            if result.get('errors'):
                flash(f'Algunos errores: {"; ".join(result["errors"][:3])}', 'warning')
                
        except Exception as e:
            flash(f'Error al procesar el CSV en el servidor: {str(e)}', 'error')

        return redirect(url_for('catalog.upload_csv'))

    try:
        products = await api.get('/catalog/')
        # Local uploads viewing would require an endpoint, but we can show products for now
        return render_template('catalog/upload_csv.html', products=products, uploads=[])
    except Exception as e:
        flash(f'Error al cargar catálogo: {str(e)}', 'error')
        return render_template('catalog/upload_csv.html', products=[], uploads=[])

@catalog_bp.route('/upload/<int:upload_id>/delete', methods=['POST'])
@management_required
async def delete_csv_upload(upload_id):
    api = APIClient(current_user.id)
    try:
        await api.delete(f'/catalog/uploads/{upload_id}')
        flash('Lote de subida eliminado correctamente.', 'success')
    except Exception as e:
        flash(f'Error al eliminar lote: {str(e)}', 'error')
    return redirect(url_for('catalog.upload_csv'))

# ─────────────────────────────────────────────────────────────────────────────
# Local Warehouse (Products CRUD)
# ─────────────────────────────────────────────────────────────────────────────
@catalog_bp.route('/warehouse', methods=['GET'])
@management_required
async def warehouse():
    api = APIClient(current_user.id)
    page = request.args.get('page', 1, type=int)
    per_page = 20
    q = request.args.get('q', '').strip()
    
    skip = (page - 1) * per_page
    
    try:
        products = await api.get('/catalog/all', params={
            'skip': skip,
            'limit': per_page,
            'q': q if q else None
        })
        
        # If it's an HTMX request for search or infinite scroll, return only the rows
        if request.headers.get('HX-Request'):
            return render_template('catalog/warehouse_rows.html', products=products, page=page, q=q)
            
        return render_template('catalog/warehouse.html', products=products, page=page, q=q)
    except Exception as e:
        flash(f'Error al cargar almacén: {str(e)}', 'error')
        if request.headers.get('HX-Request'):
            return '', 500
        return render_template('catalog/warehouse.html', products=[], page=1, q='')

@catalog_bp.route('/warehouse/product/new', methods=['GET', 'POST'])
@management_required
async def create_product():
    api = APIClient(current_user.id)
    if request.method == 'POST':
        sku = request.form.get('sku', '').strip()
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        unit = request.form.get('unit', '').strip()
        precio = request.form.get('precio', type=float, default=0.0)
        stock = request.form.get('stock_actual', type=int, default=0)
        
        imagen_url = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                ext = os.path.splitext(file.filename)[1]
                filename = f"prod_{uuid.uuid4().hex}{ext}"
                upload_path = os.path.join(current_app.root_path, 'static', 'uploads')
                os.makedirs(upload_path, exist_ok=True)
                file.save(os.path.join(upload_path, filename))
                imagen_url = f'/static/uploads/{filename}'
        
        if not name:
            flash('El nombre del producto es obligatorio.', 'error')
            return redirect(url_for('catalog.create_product'))
            
        try:
            product_data = {
                "sku": sku if sku else None,
                "name": name,
                "description": description,
                "unit": unit,
                "precio": precio,
                "stock_actual": stock,
                "imagen_url": imagen_url or "/static/img/default-product.png"
            }
            await api.post('/catalog/', json=product_data)
            flash(f'Producto "{name}" creado correctamente.', 'success')
            return redirect(url_for('catalog.warehouse'))
        except Exception as e:
            flash(f'Error al crear producto: {str(e)}', 'error')
            return redirect(url_for('catalog.create_product'))
        
    return render_template('catalog/create_product.html')

@catalog_bp.route('/warehouse/product/<int:product_id>/edit', methods=['GET', 'POST'])
@management_required
async def edit_product(product_id):
    api = APIClient(current_user.id)
    try:
        product = await api.get(f'/catalog/{product_id}')
    except Exception as e:
        flash(f'Producto no encontrado: {str(e)}', 'error')
        return redirect(url_for('catalog.warehouse'))

    if request.method == 'POST':
        update_data = {
            "sku": request.form.get('sku', '').strip() or None,
            "name": request.form.get('name', '').strip(),
            "description": request.form.get('description', '').strip(),
            "unit": request.form.get('unit', '').strip(),
            "precio": request.form.get('precio', type=float, default=0.0),
            "stock_actual": request.form.get('stock_actual', type=int, default=0)
        }
        
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                ext = os.path.splitext(file.filename)[1]
                filename = f"prod_{uuid.uuid4().hex}{ext}"
                upload_path = os.path.join(current_app.root_path, 'static', 'uploads')
                os.makedirs(upload_path, exist_ok=True)
                file.save(os.path.join(upload_path, filename))
                update_data["imagen_url"] = f'/static/uploads/{filename}'
        
        try:
            await api.put(f'/catalog/{product_id}', json=update_data)
            flash(f'Producto actualizado correctamente.', 'success')
            return redirect(url_for('catalog.warehouse'))
        except Exception as e:
            flash(f'Error al actualizar: {str(e)}', 'error')
            return redirect(url_for('catalog.edit_product', product_id=product_id))
        
    return render_template('catalog/edit_product.html', product=product)

@catalog_bp.route('/warehouse/product/<int:product_id>/toggle', methods=['POST'])
@management_required
async def toggle_product(product_id):
    api = APIClient(current_user.id)
    try:
        await api.patch(f'/catalog/{product_id}/toggle')
        flash('Estado del producto actualizado.', 'success')
    except Exception as e:
        flash(f'Error al actualizar estado: {str(e)}', 'error')
    return redirect(url_for('catalog.warehouse'))

# ─────────────────────────────────────────────────────────────────────────────
# Dynamic Catalog Proxy Routes (to FastAPI)
# ─────────────────────────────────────────────────────────────────────────────

@catalog_bp.route('/warehouse/catalog/preview', methods=['POST'])
@management_required
async def catalog_preview():
    payload = request.get_json(silent=True) or {}
    url = payload.get('url')
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    try:
        data = await APIClient(current_user.id).post('/catalog/preview', params={'url': url})
        return jsonify(data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@catalog_bp.route('/warehouse/catalog/sync/<int:product_id>', methods=['POST'])
@management_required
async def catalog_sync(product_id):
    api = APIClient(current_user.id)
    try:
        await api.put(f'/catalog/{product_id}/sync')
        flash("Producto sincronizado con éxito.", "success")
        return redirect(url_for('catalog.warehouse'))
    except Exception as e:
        flash(f"Error de conexión con el motor de scraping: {str(e)}", "error")
        return redirect(url_for('catalog.warehouse'))
