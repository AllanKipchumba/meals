# Meal Planner App

A comprehensive meal planning application that helps users generate personalized meal plans, manage recipes, and track their nutrition goals.

## Features

- User authentication via Google and Facebook OAuth
- AI-powered meal plan generation using Google Gemini
- Premium features with Stripe integration
- PDF export functionality
- Personalized recipe recommendations
- Nutrition tracking

## Local Development Setup

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up environment variables (see Environment Variables section)
5. Run the application:
   ```bash
   streamlit run main.py
   ```

## Environment Variables

Create a `.env` file in the root directory with the following variables:

```
# Application URL - This is your deployed app URL with trailing slash
REDIRECT_URI=http://localhost:8501/

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

## Deployment

### Render Deployment Instructions

1. Create a new Web Service in your Render dashboard
2. Connect to your GitHub repository
3. Set the environment variables listed above
4. Use the following build command: `pip install -r requirements.txt`
5. Set the start command to: `streamlit run main.py --server.port=$PORT --server.address=0.0.0.0`
6. Select an appropriate instance type (at least 512MB RAM recommended)

### OAuth Configuration

After deploying your application, you need to:

1. Update your Google OAuth configuration to add your new app URL to the authorized redirect URIs
2. If you're using Facebook login, update the Facebook app settings with the new redirect URL

### Database Setup

This application uses SQLite by default. For production, you might want to:

1. Use a more robust database solution
2. Configure database connection details in your environment variables

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

The application is configured to automatically detect whether it's running in development or production by using environment variables with appropriate defaults.

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is licensed under the MIT License - see the LICENSE file for details. 