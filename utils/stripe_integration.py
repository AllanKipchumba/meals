import os
import stripe
from urllib.parse import urlencode

def initialize_stripe():
    """Initialize the Stripe client with the secret key from environment variables"""
    try:
        stripe_key = os.environ.get('STRIPE_TEST_SECRET_KEY')
        if not stripe_key:
            print("Warning: STRIPE_TEST_SECRET_KEY not set in environment variables")
            return False
            
        stripe.api_key = stripe_key
        # Test that the API key works by making a simple API call
        stripe.Account.retrieve()
        return True
    except Exception as e:
        print(f"Error initializing Stripe: {str(e)}")
        return False

def create_checkout_session(user_id, success_url, cancel_url, price_in_usd=9.99):
    """
    Create a Stripe checkout session for premium upgrade
    
    Args:
        user_id: The user ID to track who is making the purchase
        success_url: URL to redirect after successful payment
        cancel_url: URL to redirect if payment is cancelled
        price_in_usd: Price in USD (default: 9.99)
        
    Returns:
        The checkout session ID and URL
    """
    # Convert price to cents (Stripe uses smallest currency unit)
    price_in_cents = int(price_in_usd * 100)
    
    try:
        # Create a checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'Meal Planner Premium',
                        'description': 'Lifetime access to all premium features',
                    },
                    'unit_amount': price_in_cents,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=f"{success_url}?session_id={{CHECKOUT_SESSION_ID}}&user_id={user_id}",
            cancel_url=cancel_url,
            metadata={
                'user_id': str(user_id)
            }
        )
        
        return {
            'id': checkout_session.id,
            'url': checkout_session.url
        }
    except Exception as e:
        print(f"Error creating checkout session: {str(e)}")
        return None

def verify_checkout_session(session_id):
    """
    Verify a checkout session was completed successfully
    
    Args:
        session_id: The Stripe checkout session ID
        
    Returns:
        Tuple of (success, user_id, transaction_details)
    """
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        
        # Check if payment was successful
        if session.payment_status == 'paid':
            user_id = session.metadata.get('user_id')
            transaction_details = {
                'amount': session.amount_total / 100,  # Convert cents to dollars
                'currency': session.currency,
                'payment_method': 'card',
                'transaction_id': session.payment_intent,
            }
            return True, user_id, transaction_details
        
        return False, None, None
    except Exception as e:
        print(f"Error verifying checkout session: {str(e)}")
        return False, None, None 