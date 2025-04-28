# utils/subscription.py
import stripe
import os
from datetime import datetime, timedelta
import time
import streamlit as st
# import webbrowser # No longer needed for opening tab
import streamlit.components.v1 as components
from database.queries import Database
from dotenv import load_dotenv

# Add this at the top of your main.py file temporarily for testing
print("Environment variables loaded:")
print(f"STRIPE_PREMIUM_PRICE_ID: {os.getenv('STRIPE_PREMIUM_PRICE_ID')}")

# Load environment variables
load_dotenv()

# Initialize Stripe with the secret key and better error handling
stripe.api_key = os.getenv('STRIPE_TEST_SECRET_KEY')
PREMIUM_PRICE_ID = os.getenv('STRIPE_PREMIUM_PRICE_ID')
FREE_MONTHLY_LIMIT = 4

# Add debug logging
if not PREMIUM_PRICE_ID:
    print("Warning: STRIPE_PREMIUM_PRICE_ID not found in environment variables")

def check_generation_limits(user_id):
    db = Database()
    
    # Check if user has active subscription
    subscription = db.get_user_subscription(user_id)
    if subscription:
        return True
        
    # Check monthly generation count
    monthly_count = db.get_monthly_generations(user_id)
    return monthly_count < FREE_MONTHLY_LIMIT

def handle_subscription_checkout():
    try:
        if not PREMIUM_PRICE_ID:
            st.error("Stripe price ID not configured. Please contact support.")
            print("Error: STRIPE_PREMIUM_PRICE_ID is not set")
            return
            
        if 'user' not in st.session_state or 'id' not in st.session_state['user']:
            st.error("Please login first to upgrade")
            return

        user_id = st.session_state['user']['id']
        
        # Debug logging
        print(f"Debug: Using Stripe price ID: {PREMIUM_PRICE_ID}")
        
        # Create checkout session with price ID from environment
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': PREMIUM_PRICE_ID,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=f'{os.environ.get("REDIRECT_URI", "https://meals-0b6b.onrender.com/")}?session_id={{CHECKOUT_SESSION_ID}}&subscription=success',
            cancel_url=f'{os.environ.get("REDIRECT_URI", "https://meals-0b6b.onrender.com/")}?subscription=cancelled',
            client_reference_id=str(user_id)
        )
        
        print(f"Debug: Checkout session created with ID: {checkout_session.id}")
        print(f"Debug: Checkout URL: {checkout_session.url}")

        # Use JavaScript to open the checkout URL in a new tab on the client side
        checkout_js = f"""
            <script>
                window.open('{checkout_session.url}', '_blank');
            </script>
        """
        # Add a small delay before executing JS
        time.sleep(0.1)
        components.html(checkout_js, height=0, width=0) # Render the JS to open the tab

        st.info("Opening Stripe checkout in a new tab. Please complete your payment there.")

    except stripe.error.StripeError as e:
        print(f"Stripe error details: {str(e)}")
        st.error(f"Payment processing error: {str(e)}")

def check_subscription_status():
    """Check and handle subscription status from URL parameters"""
    try:
        if 'subscription' in st.query_params:
            subscription_status = st.query_params['subscription']
            session_id = st.query_params.get('session_id')
            
            if subscription_status == 'success' and session_id:
                try:
                    # Verify the payment with Stripe
                    session = stripe.checkout.Session.retrieve(session_id)
                    
                    if session.payment_status == 'paid':
                        # Get user ID from client_reference_id
                        user_id = session.client_reference_id
                        
                        # Update database with new subscription
                        db = Database()
                        db.create_subscription(
                            user_id=user_id,
                            stripe_customer_id=session.customer,
                            stripe_subscription_id=session.subscription,
                            subscription_type='premium',
                            starts_at=datetime.now(),
                            ends_at=datetime.now() + timedelta(days=30)
                        )
                        
                        # Show success message
                        st.success("🎉 Welcome to Premium! You now have unlimited meal plan generations.")
                        st.info("Please log in again to access your premium features.")
                        
                        # Clear any session state
                        for key in ['user', 'checkout_session_id']:
                            if key in st.session_state:
                                del st.session_state[key]
                                
                        time.sleep(2)
                        st.rerun()
                        
                except stripe.error.StripeError as e:
                    print(f"Stripe verification error: {str(e)}")
                    st.error(f"Error verifying subscription: {str(e)}")
                    
            elif subscription_status == 'cancelled':
                st.warning("Subscription cancelled. You can try again anytime!")
                
    except Exception as e:
        print(f"Error in check_subscription_status: {str(e)}")
        st.error("An error occurred while processing your subscription.")

def show_upgrade_modal():
    st.error("You've reached your monthly limit of 4 meal plan generations!")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write("""
        ### Upgrade to Premium! 
        Get unlimited meal plan generations plus exclusive features:
        - Custom recipe modifications
        - Advanced nutrition tracking
        - Priority support
        Only $9.99/month
        """)
    
    with col2:
        # Removed the button from the modal
        # if st.button("Upgrade Now", type="primary", key="upgrade_button"):
        #     # st.info("Redirecting to payment page...") # Removed this line
        #     handle_subscription_checkout()
        st.warning("Please use the 'Upgrade to Premium' button in the sidebar to subscribe.")
