from flask import Flask, redirect, session, request, jsonify, send_from_directory
from authlib.integrations.flask_client import OAuth
from authlib.common.security import generate_token
from dotenv import load_dotenv
from flask_cors import CORS
import requests
import os
from models import Comment

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

print(f"Dex OAuth configured:")
print(f"   Client ID: {DEX_CLIENT_ID}")
print(f"   Internal Host: {DEX_INTERNAL_HOST}")
print(f"   External Host: {DEX_EXTERNAL_HOST}")

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
    print(f"Initiating login, redirect URI: {redirect_uri}")
    return dex.authorize_redirect(redirect_uri, nonce=nonce)

@app.route("/authorize")
def authorize():
    try:
        dex = oauth.create_client(DEX_CLIENT_NAME)
        token = dex.authorize_access_token()
        nonce_val = session.get("nonce")
        user_info = dex.parse_id_token(token, nonce=nonce_val)
        session["user"] = user_info
        print(f"User authorized: {user_info.get('email', 'unknown')}")
        return redirect("http://localhost:5173")
    except Exception as e:
        print(f"Authorization error: {e}")
        return redirect("http://localhost:5173?error=auth_failed")

@app.route("/logout")
def logout():
    user_email = session.get('user', {}).get('email', 'unknown')
    session.clear()
    print(f"User logged out: {user_email}")
    return redirect(os.getenv("FRONTEND_URL", "http://localhost:5173"))

@app.route('/api/user/profile')
def get_user_profile():
    user = session.get('user')
    if user:
        return jsonify({'success': True, 'user': user})
    else:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401

CORS(app, supports_credentials=True, origins=["http://localhost:5173"])

@app.route("/recipes", methods=["GET"])
def get_recipes():
    try:
        if not SPOONACULAR_API_KEY:
            print("No Spoonacular API key found!")
            return jsonify({'error': 'API key not configured'}), 500

        ingredients = request.args.get('ingredients', '')
        cuisine = request.args.get('cuisine', '')
        diet = request.args.get('diet', '')
        intolerances = request.args.get('intolerances', '')
        max_ready_time = request.args.get('maxReadyTime', '')
        recipe_type = request.args.get('type', '')
        number = request.args.get('number', '6')
        
        print(f"Recipe search request:")
        print(f"   Ingredients: {ingredients}")
        print(f"   Cuisine: {cuisine}")
        print(f"   Diet: {diet}")
        print(f"   Type: {recipe_type}")
        print(f"   Max time: {max_ready_time}")
        print(f"   Intolerances: {intolerances}")
        print(f"   Number: {number}")

        if not ingredients:
            return jsonify({'error': 'No ingredients provided'}), 400

        search_url = 'https://api.spoonacular.com/recipes/complexSearch'
        
        params = {
            'apiKey': SPOONACULAR_API_KEY,
            'includeIngredients': ingredients,
            'number': number,
            'addRecipeInformation': 'true',
            'fillIngredients': 'true',
            'addRecipeNutrition': 'true',
            'instructionsRequired': 'true',
            'sort': 'max-used-ingredients',
            'ranking': '2'
        }
        
        if cuisine:
            params['cuisine'] = cuisine
        if diet:
            params['diet'] = diet
        if intolerances:
            params['intolerances'] = intolerances
        if max_ready_time:
            params['maxReadyTime'] = max_ready_time
        if recipe_type:
            params['type'] = recipe_type
        
        print(f"📡 Making request to: {search_url}")
        print(f"📋 Full parameters: {params}")
        
        response = requests.get(search_url, params=params, timeout=30)
        
        print(f"Spoonacular response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            recipes = data.get('results', [])
            
            print(f"📋 Found {len(recipes)} recipes")
            
            if len(recipes) == 0:
                print("No recipes found")
                return jsonify([])
            
            processed_recipes = []
            for i, recipe in enumerate(recipes):
                print(f"🍽️ Processing recipe {i + 1}: {recipe.get('title', 'Unknown')}")
                
                nutrition_data = recipe.get('nutrition', {})
                nutrients = nutrition_data.get('nutrients', [])
                
                calories = 0
                for nutrient in nutrients:
                    if nutrient.get('name') == 'Calories':
                        calories = nutrient.get('amount', 0)
                        break
                
                image_url = recipe.get('image', '')
                if not image_url and recipe.get('id'):
                    image_url = f"https://spoonacular.com/recipeImages/{recipe['id']}-312x231.jpg"
                
                processed_recipe = {
                    'id': recipe.get('id'),
                    'title': recipe.get('title', f'Recipe {recipe.get("id", "")}'),
                    'image': image_url,
                    'calories': int(calories) if calories else recipe.get('calories', 0),
                    'spoonacularScore': recipe.get('spoonacularScore', 60),
                    'cuisines': recipe.get('cuisines', ['International']),
                    'readyInMinutes': recipe.get('readyInMinutes', 30),
                    'servings': recipe.get('servings', 4),
                    'vegetarian': recipe.get('vegetarian', False),
                    'vegan': recipe.get('vegan', False),
                    'glutenFree': recipe.get('glutenFree', False),
                    'dairyFree': recipe.get('dairyFree', False),
                    'dishTypes': recipe.get('dishTypes', ['main course']),
                    'extendedIngredients': recipe.get('extendedIngredients', []),
                    'analyzedInstructions': recipe.get('analyzedInstructions', []),
                    'nutrition': nutrition_data,
                    'usedIngredientCount': recipe.get('usedIngredientCount', 0),
                    'missedIngredientCount': recipe.get('missedIngredientCount', 0),
                    'likes': recipe.get('aggregateLikes', 0)
                }
                
                processed_recipes.append(processed_recipe)
            
            print(f"Returning {len(processed_recipes)} processed recipes")
            return jsonify(processed_recipes)
            
        elif response.status_code == 402:
            print("Spoonacular API quota exceeded")
            return jsonify({'error': 'API quota exceeded. Please try again later.'}), 402
        elif response.status_code == 401:
            print("Spoonacular API authentication failed")
            return jsonify({'error': 'API authentication failed. Check API key.'}), 401
        else:
            print(f"Spoonacular API error: {response.status_code}")
            print(f"Response text: {response.text}")
            return jsonify({'error': f'Spoonacular API error: {response.status_code}'}), 500
            
    except Exception as e:
        print(f"Unexpected error in get_recipes: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/cuisines')
def get_cuisines():
    cuisines = [
        "African", "Asian", "American", "British", "Cajun", "Caribbean", "Chinese", 
        "Eastern European", "European", "French", "German", "Greek", "Indian", 
        "Irish", "Italian", "Japanese", "Jewish", "Korean", "Latin American", 
        "Mediterranean", "Mexican", "Middle Eastern", "Nordic", "Southern", 
        "Spanish", "Thai", "Vietnamese"
    ]
    return jsonify(cuisines)

@app.route('/api/diets')
def get_diets():
    diets = [
        "gluten free", "ketogenic", "vegetarian", "lacto-vegetarian", 
        "ovo-vegetarian", "vegan", "pescetarian", "paleo", "primal", 
        "low fodmap", "whole30"
    ]
    return jsonify(diets)

@app.route('/api/intolerances')
def get_intolerances():
    intolerances = [
        "dairy", "egg", "gluten", "grain", "peanut", "seafood", 
        "sesame", "shellfish", "soy", "sulfite", "tree nut", "wheat"
    ]
    return jsonify(intolerances)

@app.route('/api/meal-types')
def get_meal_types():
    meal_types = [
        "main course", "side dish", "dessert", "appetizer", "salad", 
        "bread", "breakfast", "soup", "beverage", "sauce", "marinade", 
        "fingerfood", "snack", "drink"
    ]
    return jsonify(meal_types)

@app.route('/api/recipes/<int:recipe_id>/comments', methods=['GET'])
def get_comments(recipe_id):
    try:
        comments = Comment.get_comments_by_recipe(recipe_id)
        return jsonify({'success': True, 'comments': comments})
    except Exception as e:
        print(f"Error fetching comments: {e}")
        return jsonify({'success': False, 'error': 'Failed to fetch comments'}), 500

@app.route('/api/recipes/<int:recipe_id>/comments', methods=['POST'])
def create_comment(recipe_id):
    user = session.get('user')
    if not user:
        return jsonify({'success': False, 'error': 'Authentication required'}), 401
    
    try:
        data = request.get_json()
        content = data.get('content', '').strip()
        
        if not content:
            return jsonify({'success': False, 'error': 'Comment content is required'}), 400
        
        if len(content) > 1000:
            return jsonify({'success': False, 'error': 'Comment too long (max 1000 characters)'}), 400
        
        comment_id = Comment.create_comment(
            recipe_id=recipe_id,
            user_id=user['sub'],
            user_email=user['email'],
            content=content
        )
        
        return jsonify({'success': True, 'comment_id': comment_id})
        
    except Exception as e:
        print(f"Error creating comment: {e}")
        return jsonify({'success': False, 'error': 'Failed to create comment'}), 500

@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'dex_configured': True,
        'dex_external_host': DEX_EXTERNAL_HOST,
        'spoonacular_api_key': '✅ Set' if SPOONACULAR_API_KEY else 'Missing',
        'user_logged_in': bool(session.get('user'))
    })

@app.route('/debug/auth')
def debug_auth():
    return jsonify({
        'dex_client_id': DEX_CLIENT_ID,
        'dex_external_host': DEX_EXTERNAL_HOST,
        'dex_internal_host': DEX_INTERNAL_HOST,
        'current_user': session.get('user'),
        'session_keys': list(session.keys())
    })

@app.route('/debug/dex')
def debug_dex():
    """Test Dex connectivity"""
    try:
        response = requests.get(f'{DEX_EXTERNAL_HOST}/.well-known/openid_configuration', timeout=5)
        if response.status_code == 200:
            config = response.json()
            return jsonify({
                'dex_reachable': True,
                'issuer': config.get('issuer'),
                'authorization_endpoint': config.get('authorization_endpoint'),
                'token_endpoint': config.get('token_endpoint')
            })
        else:
            return jsonify({
                'dex_reachable': False,
                'status_code': response.status_code,
                'error': response.text
            })
    except Exception as e:
        return jsonify({
            'dex_reachable': False,
            'error': str(e)
        })

@app.route("/app")
@app.route("/<path:path>")
def serve_frontend(path: str = ""):
    if path and os.path.exists(os.path.join('static', path)):
        return send_from_directory('static', path)
    return send_from_directory('templates', 'index.html')

if __name__ == '__main__':
    print("Starting Flask server...")
    print(f"Spoonacular API Key: {'Set' if SPOONACULAR_API_KEY else 'Missing'}")
    print(f"Dex Configuration:")
    print(f"   Client ID: {DEX_CLIENT_ID}")
    print(f"   External Host: {DEX_EXTERNAL_HOST}")
    print(f"   Internal Host: {DEX_INTERNAL_HOST}")
    app.run(debug=True, host='0.0.0.0', port=8000)