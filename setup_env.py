"""
Setup script to create or update the .env file with Stripe keys
"""
import os

def setup_stripe_env():
    """Setup Stripe environment variables in the .env file"""
    # Check if .env file exists
    env_exists = os.path.exists('.env')
    
    # Read existing content if file exists
    env_content = {}
    if env_exists:
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    env_content[key] = value
    
    # Add or update Stripe keys
    env_content['STRIPE_TEST_SECRET_KEY'] = 'sk_test_51MICMDKoVZIFgcElHdqthAwN7DVyKbRmxDwnrb1lz11ZaS6CaPKLb8ev7UhN5ewSkyhWczVbrNQZP6tKCH62vKRR00WxW8BKbL'
    env_content['STRIPE_TEST_PUBLISHABLE_KEY'] = 'pk_test_51MICMDKoVZIFgcElpXl1LIVKmx4OsNRHtgouIV6HVhKG5uiBKEsw9iuPdC1pDaGgH4vX7ztRP1Tw4Q9LrAHYHaMV00tG1sQRUE'
    
    # Create or update .env file
    with open('.env', 'w') as f:
        for key, value in env_content.items():
            f.write(f"{key}={value}\n")
    
    print("Stripe environment variables have been set up in .env file.")

if __name__ == "__main__":
    setup_stripe_env() 