import json
import os
from datetime import datetime

from flask import Flask, jsonify, render_template, request

import database

app = Flask(__name__)

# Initialize database on startup
database.init_database()

# --- Driver Management ---
DRIVERS_FILE = "drivers.json"


def load_drivers():
    if not os.path.exists(DRIVERS_FILE):
        return []
    try:
        with open(DRIVERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_drivers(drivers):
    with open(DRIVERS_FILE, "w", encoding="utf-8") as f:
        json.dump(drivers, f, ensure_ascii=False, indent=2)


# --- History (orders) ---
HISTORY_FILE = "historial_pedidos.json"

PRODUCT_COSTS_FILE = "product_costs.json"


def load_product_costs():
    if os.path.exists(PRODUCT_COSTS_FILE):
        try:
            with open(PRODUCT_COSTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_product_costs(data):
    try:
        with open(PRODUCT_COSTS_FILE, "w", encoding="utf-8") as f:
            json.dump(data or {}, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


# Menu categories with prices and costs (in ARS)
MENU_CATEGORIES = {
    "Hamburguesas": {
        "Hamburguesa Completa": {
            "price": 2500,
            "cost": 800,
            "modifiers": [
                {
                    "id": "no_lechuga",
                    "label": "Sin lechuga",
                    "type": "toggle",
                    "price_delta": 0,
                    "default": False,
                },
                {
                    "id": "no_tomate",
                    "label": "Sin tomate",
                    "type": "toggle",
                    "price_delta": 0,
                    "default": False,
                },
                {
                    "id": "extra_queso",
                    "label": "Extra queso",
                    "type": "toggle",
                    "price_delta": 200,
                    "default": False,
                },
            ],
        },
        "Hamburguesa Simple": {"price": 1800, "cost": 600},
        "Hamburguesa con Queso": {"price": 2000, "cost": 650},
        "Hamburguesa Especial": {"price": 3000, "cost": 1000},
        "Hamburguesa con Huevo": {"price": 2200, "cost": 700},
    },
    "Milanesas": {
        "Milanesa a la Napolitana": {"price": 2800, "cost": 900},
        "Milanesa con Papas Fritas": {"price": 2800, "cost": 950},
        "Milanesa Completa": {"price": 3200, "cost": 1100},
        "Milanesa Simple": {"price": 2300, "cost": 750},
        "Milanesa con Puré": {"price": 2700, "cost": 850},
    },
    "Pizzas": {
        "Pizza Muzzarella": {"price": 3000, "cost": 1200},
        "Pizza Especial": {"price": 3500, "cost": 1400},
        "Pizza Napolitana": {"price": 3200, "cost": 1300},
        "Pizza Fugazzeta": {"price": 3300, "cost": 1350},
        "Pizza Rúcula y Jamón Crudo": {"price": 3800, "cost": 1600},
    },
    "Bauru": {
        "Bauru Simple": {"price": 1800, "cost": 550},
        "Bauru Completo": {"price": 2200, "cost": 700},
        "Bauru Especial": {"price": 2500, "cost": 800},
        "Bauru con Huevo": {"price": 2000, "cost": 650},
        "Bauru Mixto": {"price": 2300, "cost": 750},
    },
    "Refrescos": {
        "Gaseosa 500ml": {"price": 800, "cost": 200},
        "Agua Mineral 500ml": {"price": 500, "cost": 100},
        "Jugo de Naranja 500ml": {"price": 700, "cost": 250},
        "Limonada 500ml": {"price": 600, "cost": 180},
        "Agua Saborizada 500ml": {"price": 600, "cost": 150},
    },
    "Postres": {
        "Flan con Crema": {"price": 900, "cost": 300},
        "Postre Helado": {"price": 1200, "cost": 400},
        "Ensalada de Frutas": {"price": 1000, "cost": 350},
        "Tarta de Chocolate": {"price": 1100, "cost": 380},
        "Tiramisú": {"price": 1300, "cost": 450},
    },
}


def find_menu_item(name):
    for cat, items in MENU_CATEGORIES.items():
        for iname, idata in items.items():
            if iname == name:
                return idata
    return None


def compute_item_price(item_name, details):
    """Compute validated line price and breakdown for an item with modifiers.
    details can be: integer quantity, or dict { quantity, options } or { quantity }
    Returns tuple (line_total, per_unit_price, breakdown_dict)
    """
    # allow details to supply original_name when UI sends a display key
    item_data = find_menu_item(item_name)
    if item_data is None and isinstance(details, dict) and details.get("original_name"):
        item_data = find_menu_item(details.get("original_name"))
        # use the canonical name for later
        item_name = details.get("original_name")
    if item_data is None:
        return (0, 0, {"error": "item-not-found"})

    # base price
    base_price = (
        item_data.get("price") if isinstance(item_data, dict) else float(item_data)
    )
    try:
        base_price = float(base_price)
    except Exception:
        base_price = 0.0

    qty = 1
    options = {}
    if isinstance(details, dict):
        qty = int(details.get("quantity", 1) or 1)
        options = details.get("options", {}) or {}
    else:
        try:
            qty = int(details)
        except Exception:
            qty = 1

    per_unit = base_price
    breakdown = {"base": base_price, "modifiers": []}
    # defensive: modifiers may be missing or null in data; coerce to empty list
    mods = []
    if isinstance(item_data, dict):
        mods = item_data.get("modifiers") or []
        if not isinstance(mods, list):
            mods = []
    for mod in mods:
        # ensure mod is a dict
        if not isinstance(mod, dict):
            continue
        mid = mod.get("id")
        if not mid:
            continue
        selected = options.get(mid)
        # for toggle: selected true means apply price_delta
        if mod.get("type") == "toggle" and selected:
            try:
                delta = float(mod.get("price_delta", 0) or 0)
            except Exception:
                delta = 0.0
            per_unit += delta
            breakdown["modifiers"].append(
                {"id": mid, "label": mod.get("label"), "delta": delta}
            )
        # other types (choice/multiple) can be added later

    line_total = per_unit * max(qty, 1)
    breakdown["per_unit"] = per_unit
    breakdown["quantity"] = qty
    breakdown["line_total"] = line_total
    return (line_total, per_unit, breakdown)


@app.route("/api/quote", methods=["POST"])
def api_quote():
    data = request.get_json() or {}
    item = data.get("item")
    if not item:
        return jsonify({"error": "item required"}), 400
    details = data.get("details", 1)
    line_total, per_unit, breakdown = compute_item_price(item, details)
    return jsonify({"price": line_total, "per_unit": per_unit, "breakdown": breakdown})


# --- Routes ---
@app.route("/")
def index():
    return render_template("index.html", menu=MENU_CATEGORIES, is_index=True)


@app.route("/pedidos")
def orders_dashboard():
    return render_template("pedidos.html")


@app.route("/analytics")
def analytics():
    return render_template("analytics.html")


@app.route("/drivers")
def drivers_page():
    return render_template("drivers.html")


@app.route("/deliveries")
def deliveries_page():
    return render_template("deliveries.html")


# --- API endpoints ---
@app.route("/api/drivers", methods=["GET"])
def api_get_drivers():
    # Return a sanitized list of drivers (no empty names, unique)
    drivers = load_drivers()
    cleaned = []
    seen = set()
    for d in drivers:
        name = ""
        try:
            name = (d.get("name") or "").strip()
        except Exception:
            continue
        if name and name not in seen:
            cleaned.append({"name": name})
            seen.add(name)
    # persist cleanup if it differs
    if cleaned != drivers:
        save_drivers(cleaned)
    return jsonify(cleaned)


@app.route("/api/drivers", methods=["POST"])
def api_add_driver():
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Nombre requerido"}), 400

    drivers = load_drivers()
    # sanitize existing entries and keep unique names
    cleaned = []
    seen = set()
    for d in drivers:
        if not isinstance(d, dict):
            continue
        n = (d.get("name") or "").strip()
        if n and n not in seen:
            cleaned.append({"name": n})
            seen.add(n)

    # add new driver if not duplicate
    if name not in seen:
        cleaned.append({"name": name})
        save_drivers(cleaned)

    return jsonify({"ok": True, "drivers": cleaned}), 201
@app.route("/api/drivers/<int:idx>", methods=["DELETE"])
def api_delete_driver(idx):
    drivers = load_drivers()
    if 0 <= idx < len(drivers):
        drivers.pop(idx)
        save_drivers(drivers)
        return jsonify({"ok": True})
    return jsonify({"error": "Índice inválido"}), 404


@app.route("/api/history")
def get_history():
    return jsonify(load_history())


@app.route("/api/history/clear", methods=["POST"])
def clear_history():
    save_history([])
    return jsonify({"success": True})


@app.route("/api/menu")
def get_menu():
    return jsonify(MENU_CATEGORIES)


@app.route("/api/product_costs", methods=["GET", "POST"])
def api_product_costs():
    if request.method == "GET":
        return jsonify(load_product_costs())
    # POST: accept JSON map { "Product Name": cost }
    data = request.get_json() or {}
    # normalize values to numbers where possible
    norm = {}
    for k, v in data.items():
        try:
            norm[k] = float(v)
        except Exception:
            try:
                norm[k] = float(str(v).replace(",", "."))
            except Exception:
                norm[k] = v
    ok = save_product_costs(norm)
    if ok:
        return jsonify({"ok": True})
    return jsonify({"error": "failed to save"}), 500


@app.route("/api/order", methods=["POST"])
def create_order():
    data = request.json or {}
    if not data.get("items"):
        return jsonify({"error": "No hay ítems en el pedido"}), 400
    history = load_history()
    order_num = len(history) + 1
    order_code = f"P{order_num:03d}"
    # Validate and compute prices server-side
    raw_items = data.get("items", {})
    validated_items = {}
    total = 0.0
    for name, details in raw_items.items():
        line_total, per_unit, breakdown = compute_item_price(name, details)
        qty = breakdown.get("quantity", 1)
        validated_items[name] = {
            "quantity": qty,
            "per_unit": per_unit,
            "price": per_unit,  # compatibility for templates expecting `price`
            "line_total": line_total,
            "options": (details.get("options") if isinstance(details, dict) else {}),
        }
        total += line_total

    order = {
        "id": order_num,
        "code": order_code,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "customer": data.get("customer", "").strip() or "Cliente Ocasional",
        "address": data.get("address", "").strip(),
        "items": validated_items,
        "notes": data.get("notes", "").strip(),
        "total": total,
        "status": "pending",
    }
    history.append(order)
    save_history(history)

    # Also save to database for Metabase analytics
    try:
        database.save_order_to_db(order)
    except Exception as e:
        print(f"Error saving to database: {e}")
        # Continue even if DB save fails

    return jsonify({"success": True, "order": order})


@app.route("/api/order/<int:order_id>/status", methods=["POST"])
def update_order_status(order_id):
    data = request.json or {}
    new_status = data.get("status")
    if new_status not in ["pending", "finished"]:
        return jsonify({"error": "Estado inválido"}), 400
    history = load_history()
    for order in history:
        if order.get("id") == order_id:
            order["status"] = new_status
            # record finished timestamp when moving out of pending
            if new_status != "pending":
                order["finished_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            else:
                order.pop("finished_at", None)
            save_history(history)
            # Update database
            try:
                database.update_order_status(order_id, new_status)
            except Exception as e:
                print(f"Error updating database: {e}")
            return jsonify({"success": True, "order": order})
    return jsonify({"error": "Pedido no encontrado"}), 404


@app.route("/api/order/<int:order_id>/assign_driver", methods=["POST"])
def assign_driver(order_id):
    data = request.get_json() or {}
    driver = (data.get("driver") or "").strip()
    if not driver:
        return jsonify({"error": "Driver required"}), 400
    history = load_history()
    for order in history:
        if order.get("id") == order_id:
            order["driver"] = driver
            # record assignment time for client-side timers
            order["assigned_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # default TTL (minutes) for assignment timers
            order["assigned_ttl"] = int(order.get("assigned_ttl") or 30)
            save_history(history)
            # Update database
            try:
                database.assign_driver_to_order(order_id, driver)
            except Exception as e:
                print(f"Error updating database: {e}")
            return jsonify({"ok": True})
    return jsonify({"error": "Pedido no encontrado"}), 404


@app.route("/api/order/<int:order_id>/extend_assignment", methods=["POST"])
def extend_assignment(order_id):
    data = request.get_json() or {}
    add_minutes = data.get("add_minutes")
    new_ttl = data.get("new_ttl")
    if add_minutes is None and new_ttl is None:
        return jsonify({"error": "add_minutes or new_ttl required"}), 400
    try:
        history = load_history()
        for order in history:
            if order.get("id") == order_id:
                current = int(order.get("assigned_ttl") or 30)
                if add_minutes is not None:
                    try:
                        add = int(add_minutes)
                    except Exception:
                        add = 0
                    current = current + add
                else:
                    try:
                        current = int(new_ttl)
                    except Exception:
                        return jsonify({"error": "invalid new_ttl"}), 400
                order["assigned_ttl"] = current
                save_history(history)
                return jsonify({"ok": True, "assigned_ttl": current})
        return jsonify({"error": "Pedido no encontrado"}), 404
    except Exception as e:
        print(f"Error extending assignment TTL: {e}")
        return jsonify({"error": "internal error"}), 500


@app.route("/api/order/<int:order_id>/unassign", methods=["POST"])
def unassign_driver(order_id):
    history = load_history()
    for order in history:
        if order.get("id") == order_id:
            if "driver" in order:
                order.pop("driver", None)
                save_history(history)
            # Update database
            try:
                database.unassign_driver_from_order(order_id)
            except Exception as e:
                print(f"Error updating database: {e}")
            return jsonify({"ok": True})
    return jsonify({"error": "Pedido no encontrado"}), 404


@app.route("/api/order/<int:order_id>/complete", methods=["POST"])
def complete_order(order_id):
    history = load_history()
    for order in history:
        if order.get("id") == order_id:
            order["status"] = "completed"
            order["finished_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_history(history)
            # Update database
            try:
                database.update_order_status(order_id, "completed")
            except Exception as e:
                print(f"Error updating database: {e}")
            return jsonify({"success": True, "order": order})
    return jsonify({"error": "Pedido no encontrado"}), 404


# Fallback route to accept non-int path segments (some clients may send string ids)
@app.route("/api/order/<order_id>/complete", methods=["POST"])
def complete_order_fallback(order_id):
    try:
        oid = int(order_id)
    except Exception:
        return jsonify({"error": "Invalid order id"}), 400
    return complete_order(oid)


@app.route("/api/analytics")
def get_analytics():
    history = load_history()
    daily_sales = {}
    daily_orders = {}
    daily_costs = {}
    daily_profits = {}
    daily_product_cogs = {}
    daily_product_counts = {}
    daily_courier_counts = {}
    popular_items = {}
    hourly_orders = {}
    item_costs = {}
    item_profits = {}

    # Read cost settings from query params (allow client to pass configuration)
    try:
        monthly_rent = float(request.args.get("monthly_rent", 0))
    except Exception:
        monthly_rent = 0.0
    try:
        courier_cost_per_order = float(request.args.get("courier_cost", 0))
    except Exception:
        courier_cost_per_order = 0.0
    try:
        hourly_wage = float(request.args.get("hourly_wage", 0))
    except Exception:
        hourly_wage = 0.0
    try:
        daily_hours = float(request.args.get("daily_hours", 0))
    except Exception:
        daily_hours = 0.0

    # load product cost overrides
    product_costs = load_product_costs()

    # accumulate per-day intermediate values
    for order in history:
        # Treat both 'completed' and legacy 'finished' statuses as completed for analytics
        if order.get("status") not in ["completed", "finished"]:
            continue
        timestamp = order.get("timestamp", "1970-01-01 00:00:00")
        date = timestamp.split(" ")[0]
        hour = timestamp.split(" ")[1].split(":")[0]

        daily_sales.setdefault(date, 0)
        daily_orders.setdefault(date, 0)
        # we'll accumulate product costs separately per day (no longer needed here)
        # increment revenue and order count
        total_revenue = order.get("total", 0)

        # Calculate item costs for this order and update global trackers
        order_item_cost_total = 0
        total_items_count = 0
        for item, details in order.get("items", {}).items():
            qty = 0
            if isinstance(details, dict):
                qty = details.get("quantity", 0)
            else:
                try:
                    qty = int(details)
                except Exception:
                    qty = 0
            total_items_count += qty

            # Get cost from overrides first, then menu: prefer 'cost_price', fallback to 'cost'
            item_cost = 0
            if product_costs and item in product_costs:
                try:
                    item_cost = float(product_costs[item])
                except Exception:
                    try:
                        item_cost = float(str(product_costs[item]).replace(",", "."))
                    except Exception:
                        item_cost = 0
            else:
                for category, items in MENU_CATEGORIES.items():
                    if item in items:
                        if isinstance(items[item], dict):
                            item_cost = items[item].get(
                                "cost_price", items[item].get("cost", 0)
                            )
                        break

            order_item_cost_total += item_cost * qty

            # Track popular items
            popular_items.setdefault(item, 0)
            popular_items[item] += qty

            # Track per-day product counts
            daily_product_counts.setdefault(date, {})
            daily_product_counts[date].setdefault(item, 0)
            daily_product_counts[date][item] += qty

            # Track item costs and profits
            item_costs.setdefault(item, 0)
            item_costs[item] += item_cost * qty
            # approximate revenue share for this item
            try:
                if isinstance(list(order.get("items", {}).values())[0], int):
                    denom = sum(order.get("items", {}).values())
                else:
                    denom = sum(
                        d.get("quantity", 0) for d in order.get("items", {}).values()
                    )
            except Exception:
                denom = max(total_items_count, 1)
            item_revenue_share = (total_revenue / max(denom, 1)) * qty
            item_profits.setdefault(item, 0)
            item_profits[item] += item_revenue_share - item_cost * qty

        # Update daily aggregates
        daily_sales[date] += total_revenue
        daily_orders[date] += 1
        daily_costs.setdefault(date, 0)
        # add product COGS and per-order delivery cost
        daily_costs[date] += order_item_cost_total + courier_cost_per_order
        daily_product_cogs.setdefault(date, 0)
        daily_product_cogs[date] += order_item_cost_total
        daily_profits.setdefault(date, 0)
        daily_profits[date] += total_revenue - (
            order_item_cost_total + courier_cost_per_order
        )

        hourly_orders.setdefault(hour, 0)
        hourly_orders[hour] += 1

        # Track courier/driver counts per day
        driver = order.get("driver")
        if driver:
            daily_courier_counts.setdefault(date, {})
            daily_courier_counts[date].setdefault(driver, 0)
            daily_courier_counts[date][driver] += 1

    # After processing orders, add fixed daily costs (rent, labor) to each day
    rent_per_day = monthly_rent / 30.0
    labor_per_day = hourly_wage * daily_hours
    for date in list(daily_sales.keys()):
        # add rent and labor once per day
        daily_costs[date] = daily_costs.get(date, 0) + rent_per_day + labor_per_day
        # recompute profit for the day
        daily_profits[date] = daily_sales.get(date, 0) - daily_costs.get(date, 0)

    # Build per-day breakdowns for frontend detail view
    daily_breakdowns = []
    for d, _ in sorted(daily_sales.items()):
        bd = {
            "product_cogs": daily_product_cogs.get(d, 0),
            "revenue": daily_sales.get(d, 0),
            "rent": rent_per_day,
            "labor": labor_per_day,
            "courier": courier_cost_per_order * daily_orders.get(d, 0),
            "total_cost": daily_costs.get(d, 0),
            "profit": daily_profits.get(d, 0),
            "orders": daily_orders.get(d, 0),
        }
        # attach product list (array of [product, qty]) and courier list ([driver, count])
        prod_counts = daily_product_counts.get(d, {})
        courier_counts = daily_courier_counts.get(d, {})
        bd["products"] = sorted(
            list(prod_counts.items()), key=lambda x: x[1], reverse=True
        )
        bd["couriers"] = sorted(
            list(courier_counts.items()), key=lambda x: x[1], reverse=True
        )
        daily_breakdowns.append([d, bd])

    sorted_daily = sorted(daily_sales.items())
    sorted_hourly = sorted(hourly_orders.items())
    sorted_items = sorted(popular_items.items(), key=lambda x: x[1], reverse=True)[:10]

    # Consider both 'completed' and legacy 'finished' as completed for totals
    finished = [o for o in history if o.get("status") in ["completed", "finished"]]
    total_revenue = sum(o.get("total", 0) for o in finished)
    total_costs = sum(daily_costs.values())
    total_profits = sum(daily_profits.values())
    avg_order = round(total_revenue / max(len(finished), 1), 2)
    avg_profit = round(total_profits / max(len(finished), 1), 2)

    # Calculate profit margins for items
    item_margins = {}
    for item in popular_items:
        revenue = item_profits.get(item, 0) + item_costs.get(item, 0)
        cost = item_costs.get(item, 0)
        if revenue > 0:
            item_margins[item] = round(((revenue - cost) / revenue) * 100, 1)
        else:
            item_margins[item] = 0

    return jsonify(
        {
            "daily_sales": sorted_daily,
            "daily_orders": sorted(
                [(d, daily_orders.get(d, 0)) for d, _ in sorted_daily]
            ),
            "daily_costs": sorted(
                [(d, daily_costs.get(d, 0)) for d, _ in sorted_daily]
            ),
            "daily_profits": sorted(
                [(d, daily_profits.get(d, 0)) for d, _ in sorted_daily]
            ),
            "daily_breakdowns": daily_breakdowns,
            "hourly_orders": sorted_hourly,
            "popular_items": sorted_items,
            "item_costs": sorted(item_costs.items(), key=lambda x: x[1], reverse=True)[
                :10
            ],
            "item_margins": sorted(
                item_margins.items(), key=lambda x: x[1], reverse=True
            )[:10],
            "total_orders": len(finished),
            "total_revenue": total_revenue,
            "total_costs": total_costs,
            "total_profits": total_profits,
            "avg_order_value": avg_order,
            "avg_profit_per_order": avg_profit,
            "profit_margin": round((total_profits / max(total_revenue, 1)) * 100, 1),
        }
    )


if __name__ == "__main__":
    # Disable the automatic reloader on Windows to avoid socket errors
    # Respect environment variable `FLASK_DEBUG` to enable debug mode explicitly.
    _debug_env = os.getenv("FLASK_DEBUG", "0").lower()
    debug_mode = _debug_env in ("1", "true", "yes")
    app.run(debug=debug_mode, port=5000, use_reloader=False)
