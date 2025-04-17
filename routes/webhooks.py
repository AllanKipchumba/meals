# routes/webhooks.py
import stripe
import os
from database.queries import Database
from datetime import datetime, timedelta

def handle_stripe_webhook(payload, sig_header):
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.environ['STRIPE_WEBHOOK_SECRET']
        )
        
        if event.type == 'checkout.session.completed':
            session = event.data.object
            
            # Create subscription record
            db = Database()
            db.create_subscription(
                user_id=session.client_reference_id,
                stripe_customer_id=session.customer,
                stripe_subscription_id=session.subscription,
                subscription_type='premium',
                starts_at=datetime.now(),
                ends_at=datetime.now() + timedelta(days=30)
            )
            
    except Exception as e:
        print(f"Webhook error: {str(e)}")
        raise e