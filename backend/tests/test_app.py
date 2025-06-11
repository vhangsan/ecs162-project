import unittest
from unittest.mock import patch
from app import app

class TestApp(unittest.TestCase):
    """test client to simulate HTTP requests & unittest to mock external API calls.
    """

    def setUp(self):
        self.app = app.test_client()

    @patch('app.requests.get')
    def test_get_recipes(self, mock_get):
        """
        test recipe search endpoint
        
        verifies that:
        1. endpoint returns 200 status code
        2. response contains a list of recipes
        3. recipe data is properly formatted
        4. mock API response is processed correctly
        """
        # Mock the Spoonacular API response
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            'results': [
                {
                    'id': 1,
                    'title': 'Test Recipe',
                    'nutrition': {'nutrients': [{'name': 'Calories', 'amount': 100}]},
                    'image': '',
                    'cuisines': ['Italian'],
                    'readyInMinutes': 15,
                    'servings': 2,
                    'vegetarian': False,
                    'vegan': False,
                    'glutenFree': True,
                    'dairyFree': True,
                    'dishTypes': ['main course'],
                    'extendedIngredients': [],
                    'analyzedInstructions': [],
                    'usedIngredientCount': 1,
                    'missedIngredientCount': 0,
                    'aggregateLikes': 10
                }
            ]
        }

        # Test endpoint with sample ingredient
        response = self.app.get('/recipes?ingredients=chicken')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        self.assertEqual(data[0]['title'], 'Test Recipe')

    def test_get_cuisines(self):
        """
        test cuisines endpoint
        """
        response = self.app.get('/api/cuisines')
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.get_json(), list)
        self.assertIn('Italian', response.get_json())

    def test_get_diets(self):
        """
        test diets endpoint
        """
        response = self.app.get('/api/diets')
        self.assertEqual(response.status_code, 200)
        self.assertIn('vegetarian', response.get_json())

    def test_get_intolerances(self):
        """
        test intolerances endpoint
        """
        response = self.app.get('/api/intolerances')
        self.assertEqual(response.status_code, 200)
        self.assertIn('gluten', response.get_json())

    def test_get_meal_types(self):
        """
        test the meal types endpoint
        """
        response = self.app.get('/api/meal-types')
        self.assertEqual(response.status_code, 200)
        self.assertIn('main course', response.get_json())
    
    def test_get_user_profile_unauthenticated(self):
        """
        test user profile endpoint when user is not logged in
        """
        response = self.app.get('/api/user/profile')
        self.assertEqual(response.status_code, 401)
        self.assertFalse(response.get_json()['success'])

    def test_get_user_profile_authenticated(self):
        """
        test user profile endpoint when user is logged in
        """
        with self.app as client:
            # Set up mock session data
            with client.session_transaction() as sess:
                sess['user'] = {'email': 'test@example.com', 'sub': '123'}
        
            response = client.get('/api/user/profile')
            self.assertEqual(response.status_code, 200)
            json_data = response.get_json()
            self.assertTrue(json_data['success'])
            self.assertEqual(json_data['user']['email'], 'test@example.com')

    def test_get_user_favorites_unauthenticated(self):
        """
        test user favorites endpoint when user is not logged in
        """
        response = self.app.get('/api/user/favorites')
        self.assertEqual(response.status_code, 401)
        self.assertFalse(response.get_json()['success'])
    
    def test_get_user_favorites_authenticated(self):
        """
        test user favorites endpoint when user is logged in
        """
        with self.app.session_transaction() as session:
            # Set up mock session data
            session['user_id'] = 'test_user'
            session['username'] = 'test_user'
            session['email'] = 'test@example.com'

        response = self.app.get('/api/user/favorites') 

    def test_health_check(self):
        """
        check Spoonacular API key is in the response
        """
        response = self.app.get('/health')
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertEqual(json_data['status'], 'healthy')
        self.assertIn('spoonacular_api_key', json_data)

    def test_debug_auth(self):
        """
        test debug authentication endpoint
        """
        response = self.app.get('/debug/auth')
        json_data = response.get_json()
        self.assertIn('current_user', json_data)
        self.assertIn('dex_client_id', json_data)
    
    def test_debug_dex(self):
        """
        test the debug DEX endpoint and check reachability status
        """
        response = self.app.get('/debug/dex')
        json_data = response.get_json()
        self.assertIn('dex_reachable', json_data)
        self.assertIn('status_code', json_data)

if __name__ == '__main__':
    unittest.main()