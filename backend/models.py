from pymongo import MongoClient
from datetime import datetime
from bson.objectid import ObjectId
import os

# MongoDB connection
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://mongo:27017/mydatabase')
client = MongoClient(MONGO_URI)
db = client.mydatabase

# Collections
comments_collection = db.comments

class Comment:
    @staticmethod
    def create_comment(recipe_id, user_id, user_email, content):
        """Create a new comment"""
        comment = {
            'recipe_id': int(recipe_id),
            'user_id': user_id,
            'user_email': user_email,
            'content': content,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        result = comments_collection.insert_one(comment)
        return str(result.inserted_id)
    
    @staticmethod
    def get_comments_by_recipe(recipe_id):
        """Get all comments for a specific recipe"""
        comments = comments_collection.find({
            'recipe_id': int(recipe_id)
        }).sort('created_at', -1)  # Most recent first
        
        # Convert ObjectId to string for JSON serialization
        comment_list = []
        for comment in comments:
            comment['_id'] = str(comment['_id'])
            comment['created_at'] = comment['created_at'].isoformat()
            comment['updated_at'] = comment['updated_at'].isoformat()
            comment_list.append(comment)
        
        return comment_list
    
    @staticmethod
    def update_comment(comment_id, user_id, content):
        """Update a comment (only by the original author)"""
        result = comments_collection.update_one(
            {
                '_id': ObjectId(comment_id),
                'user_id': user_id  # Ensure user owns the comment
            },
            {
                '$set': {
                    'content': content,
                    'updated_at': datetime.utcnow()
                }
            }
        )
        return result.modified_count > 0
    
    @staticmethod
    def delete_comment(comment_id, user_id):
        """Delete a comment (only by the original author)"""
        result = comments_collection.delete_one({
            '_id': ObjectId(comment_id),
            'user_id': user_id  # Ensure user owns the comment
        })
        return result.deleted_count > 0