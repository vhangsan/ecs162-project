# whisk

This is a full-stack recipe application that allows users to search for recipes, save favorites, and post their feedback. The application uses Flask for the backend and Svelte for the frontend.

## GitHub Repository
https://github.com/vhangsan/ecs162-project

## Environment Setup

1. Create a `.env` file in the root directory with the following variables:
```
SPOONACULAR_API_KEY=your_spoonacular_api_key
PORT=8000
```

2. Create a `.env.dev` file for development-specific variables:
```
FRONTEND_URL=http://localhost:5173
```

## Running the Application

### Docker

1. Build and start all services:
```bash
docker-compose -f docker-compose.dev.yml up --build
```

### Manual Setup

#### Backend Setup
1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Run Flask application:
```bash
python -m flask run --host=0.0.0.0 --port=8000 --reload --debug
```

#### Frontend Setup
1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start development server:
```bash
npm run dev -- --host
```

## Features

- Recipe search with multiple filters (ingredients, cuisine, diet, etc.)
- User authentication via Dex
- Favorite recipes
- Add reviews
- Fuzzy string matching

## API Endpoints

- `/api/recipes` - search for recipes
- `/api/cuisines` - get cuisines
- `/api/diets` - get diet types
- `/api/intolerances` - get intolerances
- `/api/meal-types` - get meal types
- `/api/recipes/<recipe_id>/comments` - get and post comments
- `/api/favorites` - manage favorite recipes
- `/api/reviews` - manage recipe reviews