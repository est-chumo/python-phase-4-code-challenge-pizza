# server/app.py
from flask import Flask, jsonify, request
from flask_migrate import Migrate
from flask_cors import CORS
from sqlalchemy.exc import IntegrityError
from flask_migrate import Migrate
from .models import db, Restaurant, Pizza, RestaurantPizza


# ---------------- APP CONFIG ----------------
app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
migrate = Migrate(app, db)
CORS(app)

# ---------------- ROUTES ----------------

# GET /restaurants
@app.route("/restaurants", methods=["GET"])
def get_restaurants():
    restaurants = Restaurant.query.all()
    result = [r.to_dict(include_relationships=False) for r in restaurants]
    return jsonify(result), 200


# GET /restaurants/<int:id>
@app.route("/restaurants/<int:id>", methods=["GET"])
def get_restaurant(id):
    restaurant = Restaurant.query.get(id)
    if not restaurant:
        return jsonify({"error": "Restaurant not found"}), 404
    return jsonify(restaurant.to_dict(include_relationships=True)), 200


# DELETE /restaurants/<int:id>
@app.route("/restaurants/<int:id>", methods=["DELETE"])
def delete_restaurant(id):
    restaurant = Restaurant.query.get(id)
    if not restaurant:
        return jsonify({"error": "Restaurant not found"}), 404
    db.session.delete(restaurant)          # cascade removes restaurant_pizzas too
    db.session.commit()
    return "", 204


# GET /pizzas
@app.route("/pizzas", methods=["GET"])
def get_pizzas():
    pizzas = Pizza.query.all()
    result = [p.to_dict() for p in pizzas]
    return jsonify(result), 200


# POST /restaurant_pizzas
@app.route("/restaurant_pizzas", methods=["POST"])
def create_restaurant_pizza():
    data = request.get_json()
    if not data:
        return jsonify({"errors": ["Invalid JSON"]}), 400

    pizza_id = data.get("pizza_id")
    restaurant_id = data.get("restaurant_id")
    price = data.get("price")

    # Check required fields
    errors = []
    if pizza_id is None:
        errors.append("pizza_id is required")
    if restaurant_id is None:
        errors.append("restaurant_id is required")
    if price is None:
        errors.append("price is required")
    if errors:
        return jsonify({"errors": errors}), 400

    # Ensure referenced records exist
    pizza = Pizza.query.get(pizza_id)
    if not pizza:
        return jsonify({"errors": [f"Pizza with id {pizza_id} not found"]}), 404

    restaurant = Restaurant.query.get(restaurant_id)
    if not restaurant:
        return jsonify({"errors": [f"Restaurant with id {restaurant_id} not found"]}), 404

    # Try to create RestaurantPizza
    try:
        rp = RestaurantPizza(price=price, pizza=pizza, restaurant=restaurant)
        db.session.add(rp)
        db.session.commit()
    except ValueError as ve:
        db.session.rollback()
        return jsonify({"errors": [str(ve)]}), 400
    except IntegrityError:
        db.session.rollback()
        return jsonify({"errors": ["Integrity error creating RestaurantPizza"]}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"errors": [str(e)]}), 400

    return jsonify(rp.to_dict(include_pizza=True, include_restaurant=True)), 201


# ---------------- RUN SERVER ----------------
if __name__ == "__main__":
    app.run(port=5555, debug=True)
