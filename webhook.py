"""
Stripe webhook handler using Flask
Run this separately from the Streamlit app
"""
import os
from flask import Flask, request, jsonify
import stripe
from utils.stripe_webhook import handle_webhook
from utils.stripe_integration import initialize_stripe

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    
    success = handle_webhook(payload, sig_header)
    
    if success:
        return jsonify({'status': 'success'}), 200
    else:
        return jsonify({'status': 'error'}), 400

if __name__ == '__main__':
    # Initialize Stripe
    initialize_stripe()
    
    # Run the Flask app
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port) 