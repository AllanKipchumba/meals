# Meal Planner App Deployment Guide

This guide will help you deploy the Meal Planner application to a production environment like Render.

## Environment Variables

When deploying to Render or any other hosting service, make sure to set the following environment variables in your deployment settings:

```
# Application URL - This is your deployed app URL with trailing slash
REDIRECT_URI=https://your-app-url.onrender.com/

# Google OAuth credentials
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Stripe payment configuration
STRIPE_TEST_SECRET_KEY=your_stripe_secret_key
STRIPE_PREMIUM_PRICE_ID=your_stripe_price_id

# Optional Facebook OAuth credentials
FACEBOOK_CLIENT_ID=your_facebook_client_id
FACEBOOK_CLIENT_SECRET=your_facebook_client_secret

# Google Gemini API key
GEMINI_API_KEY=your_gemini_api_key
```

## OAuth Configuration

After deploying your application, you need to:

1. Update your Google OAuth configuration to add your new app URL to the authorized redirect URIs
2. If you're using Facebook login, update the Facebook app settings with the new redirect URL

## Database Setup

This application uses SQLite by default. For production, you might want to:

1. Use a more robust database solution
2. Configure database connection details in your environment variables

## Render Deployment Instructions

1. Create a new Web Service in your Render dashboard
2. Connect to your GitHub repository
3. Set the environment variables listed above
4. Use the following build command: `pip install -r requirements.txt`
5. Set the start command to: `streamlit run main.py --server.port=$PORT --server.address=0.0.0.0`
6. Select an appropriate instance type (at least 512MB RAM recommended)

## Testing Your Deployment

After deploying, test the following functionality:

1. User login/registration
2. OAuth flows
3. Meal plan generation
4. Payment processing
5. PDF downloading

## Troubleshooting

- If OAuth redirects fail, check that your REDIRECT_URI is correctly set and matches your Google/Facebook app configurations
- If payments fail, verify your Stripe configuration
- For any API errors, check the corresponding API keys

## Local Development vs Production

The application is now configured to automatically detect whether it's running in development or production by using environment variables with appropriate defaults. 