import uuid
import streamlit as st
from requests_oauthlib import OAuth2Session
from database.queries import Database
import json
from datetime import datetime
import time
import bcrypt
import os
import extra_streamlit_components as stx
from .helpers import create_auth_token

# Load environment variables with fallbacks
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
# Use environment variable for Redirect URI, fallback to production URL
REDIRECT_URI = os.environ.get("REDIRECT_URI", "https://meals-0b6b.onrender.com/")
AUTHORIZATION_BASE_URL = "https://accounts.google.com/o/oauth2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
SCOPE = [
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile"
]
FACEBOOK_CLIENT_ID= os.environ["FACEBOOK_CLIENT_ID"]
FACEBOOK_CLIENT_SECRET= os.environ["FACEBOOK_CLIENT_SECRET"]
FACEBOOK_AUTH_URL = "https://www.facebook.com/v18.0/dialog/oauth"
FACEBOOK_TOKEN_URL = "https://graph.facebook.com/v18.0/oauth/access_token"


def get_cookie_manager():
    return stx.CookieManager()  

cookie_manager = get_cookie_manager()

def login_user():
    # Initialize session state for registration form
    if 'show_register' not in st.session_state:
        st.session_state.show_register = False

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        # Show appropriate header based on current state
        if st.session_state.show_register:
            st.markdown("### Create an Account")
            register_form()
            if st.button("Back to Login", use_container_width=True):
                st.session_state.show_register = False
                st.rerun()
        else:
            st.markdown("### Sign in with:")
            login_form()

        st.markdown("### OR")

        # Social login buttons
        if st.button("Continue with Google", key="google_login", use_container_width=True, type="primary"):
            google = OAuth2Session(GOOGLE_CLIENT_ID, redirect_uri=REDIRECT_URI, scope=SCOPE)
            authorization_url, state = google.authorization_url(
                AUTHORIZATION_BASE_URL,
                access_type="offline",
                prompt="select_account"
            )
            st.session_state['oauth_state'] = state
            st.markdown(f'<meta http-equiv="refresh" content="0;url={authorization_url}">', unsafe_allow_html=True)
            st.stop()

        # if st.button('Continue with Facebook', key='facebook_login', use_container_width=True, type="secondary"):
        #     facebook = OAuth2Session(FACEBOOK_CLIENT_ID, redirect_uri=REDIRECT_URI)
        #     custom_state = f"facebook_{uuid.uuid4()}"
        #     authorization_url, state = facebook.authorization_url(
        #         FACEBOOK_AUTH_URL,
        #         access_type="offline",
        #         state=custom_state
        #     )
        #     st.session_state['oauth_state'] = state
        #     st.session_state['oauth_provider'] = 'facebook'
        #     st.markdown(f'<meta http-equiv="refresh" content="0;url={authorization_url}">', unsafe_allow_html=True)

        # Create Account button - only show when not in registration mode
        if not st.session_state.show_register:
            if st.button("Don't have an account? Create Account", key="create_account", use_container_width=True):
                st.session_state.show_register = True
                st.rerun()

def hash_password(password: str) -> str:
    """Hash a password for storing using bcrypt."""
    try:
        # Ensure password is encoded to bytes
        password_bytes = password.encode('utf-8')
        # Generate salt
        salt = bcrypt.gensalt()
        # Hash the password
        hashed = bcrypt.hashpw(password_bytes, salt)
        # Return the hashed password as a string
        return hashed.decode('utf-8')
    except Exception as e:
        st.error(f"Error hashing password: {str(e)}")
        return None

def verify_password(stored_password: str, provided_password: str) -> bool:
    """Verify a stored password against one provided by user."""
    try:
        # Ensure both passwords are in the correct format
        stored_bytes = stored_password.encode('utf-8')
        provided_bytes = provided_password.encode('utf-8')
        # Verify the password
        return bcrypt.checkpw(provided_bytes, stored_bytes)
    except Exception as e:
        st.error(f"Error verifying password: {str(e)}")
        return False

def login_form():
    st.text_input("Email", key="login_email")
    st.text_input("Password", type="password", key="login_password")
    
    # Create login button
    if st.button("Login", use_container_width=True):
        if password_login():            
            st.rerun()


def register_form():
    st.subheader("Create New Account")
    
    # Form inputs
    username = st.text_input("Username", key="register_username")
    email = st.text_input("Email", type='default', key="register_email")
    password = st.text_input("Password", type="password", key="register_password")
    confirm_password = st.text_input("Confirm Password", type="password", key="register_confirm_password")
    
    # Password requirements
    st.markdown("""
    <style>
    .password-requirements {
        font-size: 0.8em;
        color: #666;
        margin-top: -10px;
    }
    </style>
    <div class="password-requirements">
    Password must be at least 8 characters long and contain at least one number and one special character.
    </div>
    """, unsafe_allow_html=True)
    
    # Create register button
    if st.button("Register", use_container_width=True):
        # Validate inputs
        if not username or not email or not password:
            st.error("All fields are required.")
            return
        
        if len(password) < 8:
            st.error("Password must be at least 8 characters long.")
            return
            
        if not any(char.isdigit() for char in password):
            st.error("Password must contain at least one number.")
            return
            
        if not any(char in "!@#$%^&*()_+-=[]{}|;:,.<>?" for char in password):
            st.error("Password must contain at least one special character.")
            return
        
        if password != confirm_password:
            st.error("Passwords do not match.")
            return
            
        if not '@' in email or not '.' in email:
            st.error("Please enter a valid email address.")
            return
        
        # Connect to database
        db = Database()
        
        try:
            # Check if username already exists
            existing_user = db.get_user(username)
            if existing_user:
                st.error("Username already taken. Please choose another.")
                return
                
            # Check if email already exists
            existing_email = db.get_user_by_email(email)
            if existing_email:
                st.error("An account with this email already exists.")
                return
            
            # Hash password
            password_hash = hash_password(password)
            if not password_hash:
                st.error("Failed to hash password. Please try again.")
                return
            
            # Create user
            user_id = db.create_user(
                username=username,
                password_hash=password_hash,
                email=email,
                preferences=[]
            )
            
            if user_id:
                # Clear form data
                st.session_state.pop('register_username', None)
                st.session_state.pop('register_email', None)
                st.session_state.pop('register_password', None)
                st.session_state.pop('register_confirm_password', None)
                
                # Set session state
                st.session_state['user'] = {
                    'id': user_id,
                    'username': username,
                    'email': email,
                    'password_hash': password_hash  # Store the hash in session for verification
                }
                st.session_state['logged_in'] = True
                st.session_state['user_info'] = {"email": email}
                
                # Create auth token
                create_auth_token(email, user_id, cookie_manager)
                
                st.success("Account created successfully! You can now log in.")
                st.session_state["show_register"] = False
                st.rerun()
            else:
                st.error("Failed to create account. Please try again.")
                
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            return


def password_login():   
    email = st.session_state.get('login_email', '')
    password = st.session_state.get('login_password', '')
    
    if not email or not password:
        st.error("Please enter both email and password.")
        return False
    
    db = Database()
    
    user = db.get_user_by_email(email)
    
    if not user:
        st.error("No account found with this email address.")
        return False
    
    # Debug information
    stored_hash = user.get('password_hash', '')
    if not stored_hash:
        st.error("No password hash found for user.")
        return False
    
    # Verify password
    is_valid = verify_password(stored_hash, password)
    
    if not is_valid:
        st.error("Incorrect password or email. Please try again.")
        return False
    
    # Set session state
    st.session_state['user'] = user
    st.session_state['logged_in'] = True
    st.session_state['user_info'] = {"email": email}     
    
    # Create auth token
    create_auth_token(email, user.get("id"), cookie_manager)
   
    st.success(f"Successfully logged in as {email}!")
    return True

def handle_callback():
    print('-----------------------callback-------------------------')
    if 'code' not in st.query_params:
        st.warning("No authorization code found.")
        return
    
    code = st.query_params.get("code")
    state = st.query_params.get('state')   
    
    try:
        provider = 'google' 
        if state and state.startswith('facebook_'):
            provider = 'facebook'
       
        if provider == 'google':
            oauth_session = OAuth2Session(
                GOOGLE_CLIENT_ID, 
                redirect_uri=REDIRECT_URI,
                state=state
            )
            token_url = TOKEN_URL
            client_secret = GOOGLE_CLIENT_SECRET
            user_info_url = 'https://www.googleapis.com/oauth2/v2/userinfo'
        elif provider == 'facebook':
            oauth_session = OAuth2Session(
                FACEBOOK_CLIENT_ID, 
                redirect_uri=REDIRECT_URI,
                state=state
            )
            token_url = FACEBOOK_TOKEN_URL
            client_secret = FACEBOOK_CLIENT_SECRET
            user_info_url = 'https://graph.facebook.com/me?fields=name,email'
        else:
            st.error("Unknown OAuth provider")
            return
        
        token = oauth_session.fetch_token(
            token_url,
            client_secret=client_secret,
            code=code                
        )       
        user_info_response = oauth_session.get(user_info_url)
        user_info = user_info_response.json()        
        
        st.session_state['token'] = token
        st.session_state['user_info'] = user_info
        
        process_oauth_login(user_info)
        
        st.success(f"Successfully logged in as {user_info.get('email') or user_info.get('name')}!")
        
        st.markdown('''
        <meta http-equiv="refresh" content="2;url=/">
        ''', unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Authentication failed. Try again: {str(e)}")
       
def process_oauth_login(user_info):
    user_id = user_info['id']
    email = user_info.get('email')
    
    name = user_info.get('name', '')
    if name:
            username = name.lower().replace(' ', '_')
    else:        
        username = email.split('@')[0] if email else f"user_{user_id}"
    
    import secrets 
    random_password = secrets.token_hex(16)
    password_hash = hash_password(random_password)
    
    db = Database()
    
    user = db.get_user_by_email(email) if email else db.get_user_by_id(user_id)
   
    if not user:
        try:            
            dietary_preferences = []          
            
            user_id = db.create_user(
                username=username,
                password_hash=password_hash,  
                email=email ,  
                preferences=dietary_preferences,                
            )
            st.success("Account created successfully!")
        except Exception as e:                    
            st.error(f"Account creation failed: {str(e)}")
            return   
    
    
    st.session_state['user'] = user
    st.session_state['logged_in'] = True
    st.session_state['user_info'] = user_info      
    
    create_auth_token(email,  user.get("id") if isinstance(user, dict) else user,cookie_manager)
    

@st.cache_data(ttl=300) 
def get_user_from_db(email):
    db = Database()
    return db.get_user_by_email(email)

def check_authentication():   
    if 'logged_in' in st.session_state and st.session_state['logged_in']:
        return True
        
    if 'cookie_init' not in st.session_state:
        time.sleep(0.5)
        st.session_state['cookie_init'] = True
    
    
    auth_cookie = cookie_manager.get("auth_token")    
   
    if auth_cookie:
        try:
            if isinstance(auth_cookie, dict):
                auth_data = auth_cookie
            else:
                auth_data = json.loads(auth_cookie)
            
            if auth_data.get("exp", 0) < datetime.now().timestamp():
                cookie_manager.delete("auth_token")
                return False            
            
            db = Database()
            user = get_user_from_db(auth_data["email"])
            
            if user:               
                st.session_state['user'] = user                
                st.session_state['logged_in'] = True
                st.session_state['user_info'] = {"email": auth_data["email"]}
                return True
        except Exception as e:            
            return False
    
    return False
def logout_user():
    for key in ['user', 'logged_in', 'user_info', 'token', 'oauth_state']:
        if key in st.session_state:
            del st.session_state[key]     
    
    cookie_manager.delete("auth_token")   
   
    st.rerun()
