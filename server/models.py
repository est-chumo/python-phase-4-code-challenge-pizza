# server/models.py
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import validates

db = SQLAlchemy()

class Restaurant(db.Model):
    __tablename__ = "restaurants"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    address = db.Column(db.String, nullable=False)

    # Relationship to restaurant_pizzas
    # cascade so that when a Restaurant is deleted, its RestaurantPizzas are also deleted
    restaurant_pizzas = db.relationship(
        "RestaurantPizza",
        back_populates="restaurant",
        cascade="all, delete-orphan"
    )

    def to_dict(self, include_relationships=True):
        # keep recursion shallow and explicit
        base = {"id": self.id, "name": self.name, "address": self.address}
        if include_relationships:
            base["restaurant_pizzas"] = [rp.to_dict(include_pizza=True, include_restaurant=False) for rp in self.restaurant_pizzas]
        return base


class Pizza(db.Model):
    __tablename__ = "pizzas"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    ingredients = db.Column(db.String, nullable=False)

    restaurant_pizzas = db.relationship(
        "RestaurantPizza",
        back_populates="pizza",
        cascade="all, delete-orphan"
    )

    def to_dict(self, include_relationships=False):
        base = {"id": self.id, "name": self.name, "ingredients": self.ingredients}
        return base


class RestaurantPizza(db.Model):
    __tablename__ = "restaurant_pizzas"

    id = db.Column(db.Integer, primary_key=True)
    price = db.Column(db.Integer, nullable=False)
    pizza_id = db.Column(db.Integer, db.ForeignKey("pizzas.id"), nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurants.id"), nullable=False)

    # relationships
    pizza = db.relationship("Pizza", back_populates="restaurant_pizzas")
    restaurant = db.relationship("Restaurant", back_populates="restaurant_pizzas")

    @validates("price")
    def validate_price(self, key, value):
        if value is None:
            raise ValueError("Price is required")
        if not isinstance(value, int):
            # try to coerce floats/strings that represent ints
            try:
                value = int(value)
            except Exception:
                raise ValueError("Price must be an integer")
        if value < 1 or value > 30:
            raise ValueError("Price must be between 1 and 30")
        return value

    def to_dict(self, include_pizza=True, include_restaurant=True):
        d = {
            "id": self.id,
            "price": self.price,
            "pizza_id": self.pizza_id,
            "restaurant_id": self.restaurant_id
        }
        if include_pizza:
            d["pizza"] = self.pizza.to_dict()
        if include_restaurant:
            d["restaurant"] = {"id": self.restaurant.id, "name": self.restaurant.name, "address": self.restaurant.address}
        return d
