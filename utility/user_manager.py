import firebase_admin
from firebase_admin import firestore
from flask import session
import datetime

class UserManager:
    def __init__(self):
        self._db = None

    @property
    def db(self):
        if self._db is None:
            try:
                self._db = firestore.client()
            except Exception:
                # Firestore might not be initialized yet
                return None
        return self._db

    def get_user_profile(self, uid):
        """
        Fetches user profile and their associated plan details.
        Caches permissions in session for performance.
        """
        if not self.db:
            return None

        try:
            # 1. Get User Document
            user_ref = self.db.collection('users').document(uid)
            user_doc = user_ref.get()

            if not user_doc.exists:
                return None

            user_data = user_doc.to_dict()
            
            # 2. Get Plan Details (if linked)
            plan_data = {}
            if 'current_plan_id' in user_data:
                plan_ref = self.db.collection('plans').document(user_data['current_plan_id'])
                plan_doc = plan_ref.get()
                if plan_doc.exists:
                    plan_data = plan_doc.to_dict()

            # 3. Merge Data & Cache Permissions
            full_profile = {**user_data, "plan": plan_data}
            
            # Cache relevant permissions in session
            if plan_data and 'permissions' in plan_data:
                session['permissions'] = plan_data['permissions']
                session['user_role'] = plan_data.get('role', 'individual') # Fallback
            
            return full_profile

        except Exception as e:
            print(f"Error getting user profile: {e}")
            return None

    def check_permission(self, permission_key):
        """
        Checks if the current user has a specific permission.
        Uses session cache first.
        """
        # 1. Check Session Cache
        permissions = session.get('permissions', {})
        if permissions and permission_key in permissions:
            return permissions[permission_key]
        
        # 2. Fallback (if critical/session lost): Re-fetch profile
        # This part assumes 'user_id' is in session
        uid = session.get('user_id')
        if not uid:
            return False
            
        profile = self.get_user_profile(uid)
        if profile and 'plan' in profile and 'permissions' in profile['plan']:
             return profile['plan']['permissions'].get(permission_key, False)
             
        return False

    def create_user_if_not_exists(self, uid, email, role='individual'):
        """Creates a default user document if it doesn't exist."""
        if not self.db: return

        user_ref = self.db.collection('users').document(uid)
        if not user_ref.get().exists:
            # Assign default plan based on role
            # Ideally, these plan_ids should exist in 'plans' collection
            default_plan_id = 'basic_individual' if role == 'individual' else 'basic_pro'
            
            user_ref.set({
                'email': email,
                'role': role,
                'current_plan_id': default_plan_id,
                'created_at': datetime.datetime.now(),
                'subscription_status': 'active'
            })
            print(f"Created new user {uid} with role {role}")

    # --- CLIENTS (Professional) ---
    def create_client(self, uid, client_name, client_email="", notes=""):
        if not self.db: return None
        
        # Security check: Ensure user is 'professional' (or check permission)
        if not self.check_permission('can_manage_clients'):
            print("Access Denied: User cannot manage clients")
            return None

        client_data = {
            'name': client_name,
            'email': client_email,
            'notes': notes,
            'created_at': datetime.datetime.now()
        }
        
        # Add to subcollection
        try:
            doc_ref = self.db.collection('users').document(uid).collection('clients').add(client_data)
            return doc_ref[1].id # Returns document ID
        except Exception as e:
            print(f"Error creating client: {e}")
            return None

    def get_clients(self, uid):
        if not self.db: return []
        try:
            clients_ref = self.db.collection('users').document(uid).collection('clients')
            docs = clients_ref.stream()
            return [{'id': doc.id, **doc.to_dict()} for doc in docs]
        except Exception as e:
            print(f"Error fetching clients: {e}")
            return []

    # --- FOLDERS (Individual) ---
    def create_folder(self, uid, folder_name):
        if not self.db: return None
        
        folder_data = {
            'name': folder_name,
            'created_at': datetime.datetime.now()
        }
        try:
            doc_ref = self.db.collection('users').document(uid).collection('folders').add(folder_data)
            return doc_ref[1].id
        except Exception as e:
            print(f"Error creating folder: {e}")
            return None

    def get_folders(self, uid):
        if not self.db: return []
        try:
            folders_ref = self.db.collection('users').document(uid).collection('folders')
            docs = folders_ref.stream()
            return [{'id': doc.id, **doc.to_dict()} for doc in docs]
        except Exception as e:
            print(f"Error fetching folders: {e}")
            return []
    
    # --- STRATEGIES ---
    def save_strategy(self, uid, strategy_data, context_type, context_id=None):
        """
        Saves a strategy linked to a user, and optionally a client or folder.
        context_type: 'client' or 'folder' or 'none'
        """
        if not self.db: return None
        
        # Permission check
        if not self.check_permission('can_create_strategy'):
             return {"status": "error", "message": "Permission denied: Cannot create strategies"}

        data = {
            'owner_id': uid,
            'content': strategy_data,
            'name': strategy_data.get('name', 'Untitled Strategy'),
            'updated_at': datetime.datetime.now(),
            'context_type': context_type, # 'client' or 'folder'
            'context_id': context_id      # ID of the client or folder
        }
        
        try:
            # We store strategies in a top-level 'strategies' collection for easier querying
            # but link them to users/clients via IDs
            if 'id' in strategy_data:
                # Update existing
                self.db.collection('strategies').document(strategy_data['id']).set(data, merge=True)
                return strategy_data['id']
            else:
                # Create new
                doc_ref = self.db.collection('strategies').add(data)
                return doc_ref[1].id
        except Exception as e:
            print(f"Error saving strategy: {e}")
            return None

    def get_strategies(self, uid, context_type=None, context_id=None):
        """Fetches strategies for a user, optionally filtered by client/folder."""
        if not self.db: return []
        
        try:
            query = self.db.collection('strategies').where('owner_id', '==', uid)
            
            if context_type:
                query = query.where('context_type', '==', context_type)
            if context_id:
                query = query.where('context_id', '==', context_id)
                
            docs = query.stream()
            return [{'id': doc.id, **doc.to_dict()} for doc in docs]
        except Exception as e:
            print(f"Error fetching strategies: {e}")
            return []

# Singleton instance
user_manager = UserManager()
