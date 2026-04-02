import io

from flask import flash, redirect, render_template, request, send_file, url_for
from flask_login import current_user

from app.blueprints.dispatch import dispatch_bp
from app.utils.api_client import APIClient
from app.utils.decorators import management_required


@dispatch_bp.route("/pending")
@management_required
def list_pending():
    """List submitted orders ready for consolidation."""
    api = APIClient(current_user.id)
    try:
        orders = api.get("/dispatch/pending-orders")
        return render_template("dispatch/pending_orders.html", orders=orders)
    except Exception as exc:
        flash(f"Error al listar pedidos pendientes: {str(exc)}", "error")
        return render_template("dispatch/pending_orders.html", orders=[])


@dispatch_bp.route("/consolidate", methods=["POST"])
@management_required
def consolidate_orders():
    """Create a dispatch batch from selected submitted orders."""
    api = APIClient(current_user.id)
    order_ids = [int(order_id) for order_id in request.form.getlist("order_ids") if order_id.isdigit()]
    if not order_ids:
        flash("Selecciona al menos un pedido para consolidar.", "warning")
        return redirect(url_for("dispatch.list_pending"))

    try:
        result = api.post(
            "/dispatch/consolidate",
            json=order_ids,
        )
        flash("Lote consolidado correctamente.", "success")
        return redirect(url_for("dispatch.batch_detail", batch_id=result["batch_id"]))
    except Exception as exc:
        flash(f"Error al consolidar pedidos: {str(exc)}", "error")
        return redirect(url_for("dispatch.list_pending"))


@dispatch_bp.route("/batch/<int:batch_id>")
@management_required
def batch_detail(batch_id):
    """Show consolidated dispatch batch detail."""
    api = APIClient(current_user.id)
    try:
        batch = api.get(f"/dispatch/batch/{batch_id}")
        return render_template("dispatch/batch_detail.html", batch=batch)
    except Exception as exc:
        flash(f"Error al cargar lote: {str(exc)}", "error")
        return redirect(url_for("dispatch.list_pending"))


@dispatch_bp.route("/batch/<int:batch_id>/picking")
@management_required
def picking(batch_id):
    """Render the final picking confirmation view."""
    api = APIClient(current_user.id)
    try:
        batch = api.get(f"/dispatch/batch/{batch_id}")
        return render_template("dispatch/picking.html", batch=batch)
    except Exception as exc:
        flash(f"Error al cargar picking: {str(exc)}", "error")
        return redirect(url_for("dispatch.batch_detail", batch_id=batch_id))


@dispatch_bp.route("/batch/<int:batch_id>/confirm", methods=["POST"])
@management_required
def confirm_dispatch(batch_id):
    """Confirm dispatch and deduct central stock."""
    api = APIClient(current_user.id)
    try:
        api.post(f"/dispatch/batch/{batch_id}/confirm")
        flash("Despacho confirmado y stock central actualizado.", "success")
    except Exception as exc:
        flash(f"Error al confirmar despacho: {str(exc)}", "error")
    return redirect(url_for("dispatch.batch_detail", batch_id=batch_id))


@dispatch_bp.route("/batch/<int:batch_id>/reject-order/<int:order_id>", methods=["POST"])
@management_required
def reject_order(batch_id, order_id):
    """Return one order from a pending batch to the admin with a rejection note."""
    api = APIClient(current_user.id)
    note = request.form.get("rejection_note", "").strip()
    params = {"rejection_note": note} if note else None
    try:
        api.post(f"/dispatch/batch/{batch_id}/reject-order/{order_id}", params=params)
        flash("Pedido devuelto al administrador.", "success")
    except Exception as exc:
        flash(f"Error al rechazar pedido: {str(exc)}", "error")
    return redirect(url_for("dispatch.batch_detail", batch_id=batch_id))


@dispatch_bp.route("/batch/<int:batch_id>/export_consolidated")
@management_required
def export_batch(batch_id):
    """Download the consolidated PDF for a batch."""
    api = APIClient(current_user.id)
    try:
        response = api.get(
            f"/dispatch/batch/{batch_id}/export/consolidated",
            return_response=True,
            stream=True,
        )
        return send_file(
            io.BytesIO(response.content),
            mimetype=response.headers.get("content-type", "application/pdf"),
            as_attachment=True,
            download_name=f"consolidado_lote_{batch_id}.pdf",
        )
    except Exception as exc:
        flash(f"Error al exportar consolidado: {str(exc)}", "error")
        return redirect(url_for("dispatch.batch_detail", batch_id=batch_id))


@dispatch_bp.route("/batch/<int:batch_id>/export_buildings")
@management_required
def export_batch_buildings(batch_id):
    """Download the per-building PDF for a batch."""
    api = APIClient(current_user.id)
    try:
        response = api.get(
            f"/dispatch/batch/{batch_id}/export/buildings",
            return_response=True,
            stream=True,
        )
        return send_file(
            io.BytesIO(response.content),
            mimetype=response.headers.get("content-type", "application/pdf"),
            as_attachment=True,
            download_name=f"distribucion_edificios_lote_{batch_id}.pdf",
        )
    except Exception as exc:
        flash(f"Error al exportar detalle por edificio: {str(exc)}", "error")
        return redirect(url_for("dispatch.batch_detail", batch_id=batch_id))


@dispatch_bp.route("/history")
@management_required
def history():
    """Show dispatch history."""
    api = APIClient(current_user.id)
    try:
        data = api.get("/dispatch/history")
        return render_template(
            "dispatch/history.html",
            batches=data.get("batches", []),
            orders=data.get("orders", []),
        )
    except Exception as exc:
        flash(f"Error al cargar historial: {str(exc)}", "error")
        return render_template("dispatch/history.html", batches=[], orders=[])


@dispatch_bp.route("/purchases")
@management_required
def list_purchases():
    """List direct purchases."""
    api = APIClient(current_user.id)
    try:
        purchases = api.get("/dispatch/purchases/")
        return render_template("dispatch/purchases/list.html", purchases=purchases)
    except Exception as exc:
        flash(f"Error al cargar compras: {str(exc)}", "error")
        return render_template("dispatch/purchases/list.html", purchases=[])


@dispatch_bp.route("/purchases/<int:purchase_id>")
@management_required
def purchase_detail(purchase_id):
    """Show one purchase detail."""
    api = APIClient(current_user.id)
    try:
        purchase = api.get(f"/dispatch/purchases/{purchase_id}")
        return render_template("dispatch/purchases/detail.html", purchase=purchase)
    except Exception as exc:
        flash(f"Error al cargar compra: {str(exc)}", "error")
        return redirect(url_for("dispatch.list_purchases"))


@dispatch_bp.route("/purchases/new", methods=["GET", "POST"])
@management_required
def create_purchase():
    """Create a direct purchase through the FastAPI backend."""
    api = APIClient(current_user.id)
    if request.method == "POST":
        product_ids = request.form.getlist("product_ids")
        quantities = request.form.getlist("quantities")
        unit_prices = request.form.getlist("unit_prices")
        new_product_names = request.form.getlist("new_product_names")

        try:
            items = []
            new_name_index = 0

            for index, raw_product_id in enumerate(product_ids):
                quantity = int(quantities[index]) if index < len(quantities) and quantities[index] else 0
                unit_price = float(unit_prices[index]) if index < len(unit_prices) and unit_prices[index] else 0.0
                if quantity <= 0:
                    continue

                product_id = int(raw_product_id) if raw_product_id and raw_product_id.isdigit() else None
                if product_id is None and new_name_index < len(new_product_names):
                    product_name = new_product_names[new_name_index].strip()
                    new_name_index += 1
                    if product_name:
                        product = api.post(
                            "/catalog/",
                            json={
                                "sku": None,
                                "name": product_name,
                                "categoria": "General",
                                "description": None,
                                "unit": "Unidad",
                                "precio": unit_price,
                                "imagen_url": "/static/img/default-product.png",
                                "stock_actual": 0,
                                "stock_minimo": 10,
                                "is_active": True,
                                "source_url": None,
                                "is_dynamic": False,
                                "last_synced_at": None,
                            },
                        )
                        product_id = product["id"]

                if product_id is None:
                    continue

                items.append(
                    {
                        "product_id": product_id,
                        "quantity": quantity,
                        "unit_price": unit_price,
                    }
                )

            if not items:
                flash("Debes agregar al menos un artículo válido.", "warning")
                return redirect(url_for("dispatch.create_purchase"))

            purchase = api.post(
                "/dispatch/purchases/",
                json={
                    "supplier": request.form.get("supplier", "").strip() or None,
                    "invoice_number": request.form.get("invoice_number", "").strip() or None,
                    "purchase_date": request.form.get("purchase_date"),
                    "notes": request.form.get("notes", "").strip() or None,
                    "items": items,
                },
            )
            flash("Compra registrada correctamente.", "success")
            return redirect(url_for("dispatch.purchase_detail", purchase_id=purchase["id"]))
        except Exception as exc:
            flash(f"Error al registrar compra: {str(exc)}", "error")
            return redirect(url_for("dispatch.create_purchase"))

    try:
        products = api.get("/catalog/all")
        return render_template("dispatch/purchases/create.html", products=products)
    except Exception as exc:
        flash(f"Error al cargar catálogo para compras: {str(exc)}", "error")
        return render_template("dispatch/purchases/create.html", products=[])
