from pymongo import MongoClient
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from bson import ObjectId
import os

# Load environment variables
load_dotenv()

class Database:
    def __init__(self):
        self.client = None
        self.db = None
        self.connect()

    def connect(self):
        try:
            mongodb_uri = os.getenv('MONGODB_URI')
            self.client = MongoClient(mongodb_uri)
            self.db = self.client.clustersearchimge
            self.db.users.create_index('email', unique=True)
            print("Connected to MongoDB Atlas")
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            raise

    # User Management Methods
    def register_user(self, username, email, password, is_admin=False):
        try:
            if self.db.users.find_one({'email': email}):
                return False, "Email already registered"

            user = {
                'username': username,
                'email': email,
                'password': generate_password_hash(password),
                'created_at': datetime.utcnow(),
                'last_login': None,
                'is_admin': is_admin,
                'is_active': True,
                'search_history': [],
                'avatar': 'default.png'
            }

            result = self.db.users.insert_one(user)
            return True, str(result.inserted_id)
        except Exception as e:
            print(f"Error registering user: {e}")
            return False, str(e)

    def login_user(self, email, password):
        try:
            user = self.db.users.find_one({'email': email})
            
            if not user:
                return False, "Invalid email or password"
                
            if not user.get('is_active', True):
                return False, "Account is deactivated"
                
            if user and check_password_hash(user['password'], password):
                self.db.users.update_one(
                    {'_id': user['_id']},
                    {'$set': {'last_login': datetime.utcnow()}}
                )
                return True, user
            
            return False, "Invalid email or password"
        except Exception as e:
            print(f"Error during login: {e}")
            return False, str(e)

    def get_user_by_id(self, user_id):
        try:
            return self.db.users.find_one({'_id': ObjectId(user_id)})
        except:
            return None

    def get_user_by_email(self, email):
        try:
            return self.db.users.find_one({'email': email})
        except:
            return None

    def update_avatar(self, user_id, avatar_filename):
        try:
            self.db.users.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': {'avatar': avatar_filename}}
            )
            return True, "Avatar updated successfully"
        except Exception as e:
            return False, str(e)

    def change_password(self, user_id, current_password, new_password):
        try:
            user = self.get_user_by_id(ObjectId(user_id))
            if not user:
                return False, "User not found"
            
            if not check_password_hash(user['password'], current_password):
                return False, "Current password is incorrect"
            
            self.db.users.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': {'password': generate_password_hash(new_password)}}
            )
            return True, "Password changed successfully"
        except Exception as e:
            return False, str(e)

    def reset_password(self, email, new_password):
        try:
            self.db.users.update_one(
                {'email': email},
                {'$set': {'password': generate_password_hash(new_password)}}
            )
            return True
        except Exception as e:
            print(f"Error resetting password: {e}")
            return False

    # Admin Methods
    def get_all_users(self):
        try:
            users = self.db.users.find({}, {'password': 0})
            return list(users)
        except Exception as e:
            print(f"Error fetching users: {e}")
            return []

    def toggle_user_status(self, user_id):
        try:
            user = self.db.users.find_one({'_id': ObjectId(user_id)})
            if user:
                new_status = not user.get('is_active', True)
                self.db.users.update_one(
                    {'_id': ObjectId(user_id)},
                    {'$set': {'is_active': new_status}}
                )
                return True, f"User status changed to {'active' if new_status else 'inactive'}"
            return False, "User not found"
        except Exception as e:
            return False, str(e)

    def delete_user(self, user_id):
        try:
            if not ObjectId.is_valid(user_id):
                return False, "Invalid user ID"
                
            result = self.db.users.delete_one({'_id': ObjectId(user_id)})
            if result.deleted_count:
                return True, "User deleted successfully"
            return False, "User not found"
        except Exception as e:
            return False, str(e)

    def make_admin(self, user_id):
        try:
            result = self.db.users.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': {'is_admin': True}}
            )
            if result.modified_count:
                return True, "User promoted to admin"
            return False, "User not found"
        except Exception as e:
            return False, str(e)

    def revoke_admin(self, user_id):
        try:
            result = self.db.users.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': {'is_admin': False}}
            )
            if result.modified_count:
                return True, "Admin privileges revoked"
            return False, "User not found"
        except Exception as e:
            return False, str(e)

    # Search History Methods
    def update_search_history(self, user_id, search_data):
        try:
            self.db.users.update_one(
                {'_id': ObjectId(user_id)},
                {
                    '$push': {
                        'search_history': {
                            'query_image': search_data['query_image'],
                            'timestamp': datetime.utcnow(),
                            'results': search_data['results'][:5]
                        }
                    }
                }
            )
            return True
        except Exception as e:
            print(f"Error updating search history: {e}")
            return False

    # Post Management Methods
    def create_post(self, user_id, image_filename, caption):
        try:
            post = {
                'user_id': ObjectId(user_id),
                'image': image_filename,
                'caption': caption,
                'created_at': datetime.utcnow(),
                'likes': 0,
                'comments': []
            }
            self.db.posts.insert_one(post)
            return True, "Post created successfully"
        except Exception as e:
            return False, str(e)

    def get_all_posts(self):
        try:
            posts = list(self.db.posts.find().sort('created_at', -1))
            for post in posts:
                user = self.get_user_by_id(post['user_id'])
                if user:
                    post['username'] = user['username']
                    post['user_avatar'] = user.get('avatar', 'default.png')
                else:
                    post['username'] = 'Unknown User'
                    post['user_avatar'] = 'default.png'
                post['_id'] = str(post['_id'])
                post['user_id'] = str(post['user_id'])
            return posts
        except Exception as e:
            print(f"Error getting posts: {e}")
            return []

    def get_user_posts(self, user_id):
        try:
            posts = list(self.db.posts.find(
                {'user_id': ObjectId(user_id)}
            ).sort('created_at', -1))
            for post in posts:
                post['_id'] = str(post['_id'])
                post['user_id'] = str(post['user_id'])
            return posts
        except Exception as e:
            print(f"Error getting user posts: {e}")
            return []

    def delete_post(self, post_id, user_id):
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return False, "User not found"

            post = self.db.posts.find_one({'_id': ObjectId(post_id)})
            if not post:
                return False, "Post not found"

            # Admin có thể xóa bất kỳ bài viết nào
            if user.get('is_admin', False):
                self.db.posts.delete_one({'_id': ObjectId(post_id)})
                return True, "Post deleted successfully by admin"

        # Người dùng thường chỉ có thể xóa bài viết của họ
            if str(post['user_id']) != str(user_id):
                return False, "Not authorized to delete this post"

            self.db.posts.delete_one({'_id': ObjectId(post_id)})
            return True, "Post deleted successfully"
        except Exception as e:
            return False, str(e)

    def update_post(self, post_id, user_id, caption):
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return False, "User not found"

            post = self.db.posts.find_one({'_id': ObjectId(post_id)})
            if not post:
                return False, "Post not found"

            if str(post['user_id']) != user_id and not user.get('is_admin', False):
                return False, "Not authorized to edit this post"

            self.db.posts.update_one(
                {'_id': ObjectId(post_id)},
                {'$set': {'caption': caption}}
            )
            return True, "Post updated successfully"
        except Exception as e:
            return False, str(e)

    def close(self):
        if self.client:
            self.client.close()
            print("MongoDB connection closed")
    def add_animal_info(self, class_name, info):
        """Add or update animal information"""
        try:
            self.db.animal_info.update_one(
                {'class_name': class_name},
                {'$set': {
                    'description': info.get('description', ''),
                    'scientific_name': info.get('scientific_name', ''),
                    'habitat': info.get('habitat', ''),
                    'diet': info.get('diet', ''),
                    'lifespan': info.get('lifespan', ''),
                    'updated_at': datetime.utcnow()
                }},
                upsert=True
            )
            return True, "Animal information updated successfully"
        except Exception as e:
            return False, str(e)
    def get_animal_info(self, class_name):
        return self.db.animal_info.find_one({
            "class_name": {
                "$regex": f"^{class_name}$",
                "$options": "i"
            }
        })


       
# Create database instance
db = Database()