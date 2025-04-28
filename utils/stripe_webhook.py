import os
import stripe
import json
from database.queries import Database

def handle_webhook(request_data, signature):
    """
    Handle incoming webhook events from Stripe
    
    Args:
        request_data: Raw request body data
        signature: Stripe signature header
        
    Returns:
        True if successfully processed, False otherwise
    """
    # Get the webhook secret from environment variables
    webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    if not webhook_secret:
        print("Warning: STRIPE_WEBHOOK_SECRET not set")
        return False
    
    if not stripe.api_key:
        stripe_key = os.environ.get('STRIPE_TEST_SECRET_KEY')
        if not stripe_key:
            print("Error: STRIPE_TEST_SECRET_KEY not set")
            return False
        stripe.api_key = stripe_key
    
    try:
        # Verify the webhook signature
        event = stripe.Webhook.construct_event(
            request_data, signature, webhook_secret
        )
        
        # Handle different event types
        if event['type'] == 'checkout.session.completed':
            return handle_checkout_completed(event['data']['object'])
        
        return True  # Successfully processed but not relevant
    except stripe.error.SignatureVerificationError:
        print("Invalid signature")
        return False
    except Exception as e:
        print(f"Error processing webhook: {str(e)}")
        return False

def handle_checkout_completed(session):
    """
    Handle a successful checkout session completion
    
    Args:
        session: The Stripe session object
        
    Returns:
        True if successfully processed, False otherwise
    """
    try:
        # Get the user ID from the session metadata
        user_id = session.get('metadata', {}).get('user_id')
        
        if not user_id:
            print("No user_id found in session metadata")
            return False
        
        # Check if payment was successful
        if session.get('payment_status') != 'paid':
            print(f"Payment not completed: {session.get('payment_status')}")
            return False
        
        # Record the payment and set premium status
        db = Database()
        
        # Record payment details
        db.record_payment(
            user_id=int(user_id),
            amount=session.get('amount_total') / 100,  # Convert from cents to dollars
            currency=session.get('currency', 'usd'),
            payment_method='stripe',
            status='completed',
            transaction_id=session.get('payment_intent')
        )
        
        # Set user premium status
        db.set_premium_status(int(user_id))
        
        print(f"Successfully processed premium upgrade for user {user_id}")
        return True
    except Exception as e:
        print(f"Error processing checkout completion: {str(e)}")
        return False 