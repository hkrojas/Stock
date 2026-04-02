from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, user_data):
        self.id = user_data.get('id')
        self.username = user_data.get('username')
        self.name = user_data.get('name')
        self.role = user_data.get('role')
        
        # Mocking building objects for templates that use .assigned_buildings
        # In a real scenario, building objects should also be simple wrapper classes
        self.assigned_buildings = user_data.get('assigned_buildings', [])

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'

    def get_id(self):
        return str(self.id)
