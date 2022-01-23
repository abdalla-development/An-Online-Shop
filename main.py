from flask import Flask, render_template, request, redirect, url_for, session, abort, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_gravatar import Gravatar
from functools import wraps
from flask_bootstrap import Bootstrap
import os
import stripe
import json


app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'

# Connect to Database
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", 'sqlite:///store.db')  #
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Login Manger
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


AUTO = "When it's time to refresh your little one's closet, find clothes that express his personality and sense of " \
       "style. Whether you're looking for comfortable, everyday clothing for your little guy or a fun statement piece" \
       ", you'll find a variety of boys' clothes for less on Walmart.com. Where will he be wearing his new outfit? If" \
       " he's headed to gym class, you'll want to find clothes for him that have a good amount of stretch so he can " \
       "easily run, jump and play. Moisture-wicking fabrics are also a great choice to help keep him cool and dry on " \
       "the playground. Looking for something for him to wear to a dressy event? Walmart has suits and sport coats in" \
       " a variety of sizes and styles, perfect for weddings and formal occasions."
ACCESSORIES = "Women's Chain Necklace Y Necklace Coin Bar Star Ladies Bohemian Fashion European Alloy Gold Triangle " \
              "heart Moon Circle 40 cm Necklace Jewelry 1pc For Party / Evening Gift / Layered Necklace"
total = 0
stripe.api_key = "sk_test_51JWH2wCcc2PPngSJaTST7Vj8g1hW1kTQ4NjGjhKDIeUrr2hCnL9zPo0VbBQYS7SkwEvBJXBAbzTP7Ks5FJLuD0AC00e0CDE1Dz"
user_log = False


# Merchandise TABLE Configuration
class Merchandise(UserMixin, db.Model):
    __tablename__ = "MERCHANDISE"
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(250), nullable=False)
    image_path = db.Column(db.String(500), nullable=False)
    price = db.Column(db.String(500), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(100000000), nullable=False)
    item_name = db.Column(db.String(500), unique=True, nullable=False)


# User TABLE Configuration
class User(UserMixin, db.Model):
    __tablename__ = "USER"
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(250), nullable=False)
    last_name = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(500), unique=True, nullable=False)
    password = db.Column(db.String(500), nullable=False)

    # The "Client" refers to the user id that owns the cart.
    my_cart = relationship("Cart", back_populates="user")


# Cart TABLE Configuration
class Cart(UserMixin, db.Model):
    __tablename__ = "CART"
    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(250), unique=True, nullable=False)
    category = db.Column(db.String(250), nullable=False)
    image_path = db.Column(db.String(500), nullable=False)
    price = db.Column(db.String(500), nullable=False)
    quantity = db.Column(db.Integer)
    description = db.Column(db.String(100000000), nullable=False)
    amount = db.Column(db.Integer)
    color = db.Column(db.String(250), nullable=False)
    size = db.Column(db.String(250), nullable=False)

    # Link the cart to the user id
    user = relationship("User", back_populates="my_cart")
    user_id = db.Column(db.Integer, db.ForeignKey("USER.id"))


# db.create_all()


def calculate_order_amount(items):
    # Replace this constant with a calculation of the order's amount
    # Calculate the order total on the server to prevent
    # people from directly manipulating the amount on the client
    return 1400


@app.route("/")
def home():
    cart_item = db.session.query(Cart).all()
    cart_list = len(cart_item)
    return render_template("index.html", number=cart_list, status=user_log)


@app.route("/accessories", methods=["GET"])
def accessories():
    cart_item = db.session.query(Cart).all()
    cart_list = len(cart_item)
    if request.method == "GET":
        girls_accessories = Merchandise.query.filter_by(category="Accessory")
        return render_template("accessories.html", accessory=girls_accessories, number=cart_list, status=user_log)


@app.route("/boys", methods=["GET"])
def boys():
    cart_item = db.session.query(Cart).all()
    cart_list = len(cart_item)
    if request.method == "GET":
        boys_clothes = Merchandise.query.filter_by(category="Boys")
        return render_template("boys.html", boy=boys_clothes, number=cart_list, status=user_log)


@app.route("/girls", methods=["GET"])
def girls():
    cart_item = db.session.query(Cart).all()
    cart_list = len(cart_item)
    if request.method == "GET":
        girls_clothes = Merchandise.query.filter_by(category="Girls")
        return render_template("girls.html", girl=girls_clothes, number=cart_list, status=user_log)


@app.route("/cart", methods=["POST", "GET"])
def cart():
    global total
    total = 0
    cart_item = db.session.query(Cart).all()
    cart_list = len(cart_item)
    for item in cart_item:
        total += int(item.price.replace("SDG", ""))

    if request.method == "GET":
        return render_template("cart.html", shop_list=cart_item, number=cart_list, total=total, status=user_log)


@app.route("/login", methods=["POST", "GET"])
def login():
    global user_log
    cart_item = db.session.query(Cart).all()
    cart_list = len(cart_item)
    if request.method == "GET":
        return render_template("login.html", number=cart_list, status=user_log)
    else:
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if check_password_hash(user.password, password):
            login_user(user)
            user_log = True
            return redirect(url_for("home"))


@app.route("/register", methods=["POST", "GET"])
def register():
    cart_item = db.session.query(Cart).all()
    cart_list = len(cart_item)
    if request.method == "GET":
        return render_template("register.html", number=cart_list, status=user_log)
    else:
        first_name = request.form['f-name']
        last_name = request.form['l-name']
        password = request.form['password']
        email = request.form['email']
        encrypted_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
        new_user = User(first_name=first_name, last_name=last_name, email=email, password=encrypted_password)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("home"))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.route("/add/<int:item_id>", methods=["POST"])
def add(item_id):
    item_to_add = Merchandise.query.filter_by(id=item_id).first()
    size = request.form["size"]
    color = request.form["color"]
    image = item_to_add.image_path
    category = item_to_add.category
    item_name = item_to_add.item_name
    price = int(item_to_add.price.replace("SDG", ""))
    amount = request.form["amount"]
    # quantity total
    cart_to_add = Cart(item_name=item_name, category=category, image_path=image, price=item_to_add.price,
                       description=item_to_add.price, amount=amount, color=color, size=size, user_id=current_user.id)
    db.session.add(cart_to_add)
    db.session.commit()
    flash("item added to the cart")
    if item_to_add.category == "Boys":
        return redirect(url_for("boys"))
    elif item_to_add.category == "Girls":
        return redirect(url_for("girls"))
    else:
        return redirect(url_for("accessories"))


@app.route("/delete/<int:item_id>")
def cart_delete(item_id):
    item_to_delete = Cart.query.get(item_id)
    db.session.delete(item_to_delete)
    db.session.commit()
    # flash("item successfully deleted ")
    return redirect(url_for("cart"))


@app.route("/checkout", methods=["POST", "GET"])
@login_required
def checkout():
    # return render_template("checkout.html")
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': 'T-shirt',
                },
                'unit_amount': 2000,
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url='http://localhost:4242/success.html',
        cancel_url='http://localhost:4242/cancel.html',

    )

    return redirect(session.url, code=303)


@app.route("/product")
def add_item():
    # cart_item = db.session.query(Cart).all()
    # cart_list = len(cart_item)
    # , number=cart_list
    pass


if __name__ == '__main__':
    app.run(port=4242)








