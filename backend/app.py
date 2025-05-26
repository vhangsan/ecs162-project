from flask import Flask, redirect, session, request, jsonify, send_from_directory
from authlib.integrations.flask_client import OAuth
from authlib.common.security import generate_token
from dotenv import load_dotenv
from flask_cors import CORS
import requests
import os

load_dotenv()

secret_key = os.getenv("FLASK_SECRET_KEY") or os.urandom(24)

app = Flask(__name__)
app.config["SECRET_KEY"] = secret_key

SPOONACULAR_API_KEY = os.getenv("SPOONACULAR_API_KEY")

oauth = OAuth(app)

nonce = generate_token()

DEX_CLIENT_ID: str = os.getenv("OIDC_CLIENT_ID", "flask-app")
DEX_CLIENT_NAME: str = os.getenv("OIDC_CLIENT_NAME", DEX_CLIENT_ID)
DEX_CLIENT_SECRET: str = os.getenv("OIDC_CLIENT_SECRET", "flask-secret")


DEX_INTERNAL_HOST = os.getenv("DEX_INTERNAL_HOST", "http://dex:5556")
DEX_EXTERNAL_HOST = os.getenv("DEX_EXTERNAL_HOST", "http://localhost:5556")

AUTHORIZATION_ENDPOINT = f"{DEX_EXTERNAL_HOST}/auth"
TOKEN_ENDPOINT = f"{DEX_INTERNAL_HOST}/token"
JWKS_URI = f"{DEX_INTERNAL_HOST}/keys"
USERINFO_ENDPOINT = f"{DEX_INTERNAL_HOST}/userinfo"
DEVICE_ENDPOINT = f"{DEX_INTERNAL_HOST}/device/code"

oauth.register(
    name=DEX_CLIENT_NAME,
    client_id=DEX_CLIENT_ID,
    client_secret=DEX_CLIENT_SECRET,
    authorization_endpoint=AUTHORIZATION_ENDPOINT,
    token_endpoint=TOKEN_ENDPOINT,
    jwks_uri=JWKS_URI,
    userinfo_endpoint=USERINFO_ENDPOINT,
    device_authorization_endpoint=DEVICE_ENDPOINT,
    client_kwargs={"scope": "openid email profile"},
)

@app.route('/')
def home():
    user = session.get('user')
    if user:
        return f"<h2>Logged in as {user['email']}</h2><a href='/logout'>Logout</a>"
    return '<a href="/login">Login with Dex</a>'

@app.route("/login")
def login():
    session["nonce"] = nonce
    redirect_uri = "http://localhost:8000/authorize"
    dex = oauth.create_client(DEX_CLIENT_NAME)
    return dex.authorize_redirect(redirect_uri, nonce=nonce)


@app.route("/authorize")
def authorize():
    dex = oauth.create_client(DEX_CLIENT_NAME)
    token = dex.authorize_access_token()
    nonce_val = session.get("nonce")
    user_info = dex.parse_id_token(token, nonce=nonce_val)
    session["user"] = user_info
    return redirect("http://localhost:5173")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(os.getenv("FRONTEND_URL", "http://localhost:5173"))

CORS(app, supports_credentials=True, origins=["http://localhost:5173"])

@app.route("/recipes", methods=["GET"])
def get_recipes():
    ingredients = request.args.get("ingredients")
    response = requests.get(
        "https://api.spoonacular.com/recipes/findByIngredients",
        params={
            "ingredients": ingredients,
            "number": 6,
            "apiKey": SPOONACULAR_API_KEY
        }
    )
    return jsonify(response.json())

@app.route("/app")
@app.route("/<path:path>")
def serve_frontend(path: str = ""):
    if path and os.path.exists(os.path.join('static', path)):
        return send_from_directory('static', path)
    return send_from_directory('templates', 'index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)