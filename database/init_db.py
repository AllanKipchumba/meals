import psycopg2
import os
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def init_database():
    conn = psycopg2.connect(
        host=os.environ['PGHOST'],
        port=os.environ['PGPORT'],
        user=os.environ['PGUSER'],
        password=os.environ['PGPASSWORD'],
        database=os.environ['PGDATABASE']
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    
    # Create tables
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) NOT NULL,
            password_hash TEXT NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            dietary_preferences TEXT[],
            allergies TEXT[],
            calorie_goal INTEGER,
            protein_goal INTEGER,
            carbs_goal INTEGER,
            fat_goal INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS subscription_plans (
            id SERIAL PRIMARY KEY,
            name VARCHAR(50) NOT NULL,
            price_id VARCHAR(100) NOT NULL,
            price_amount INTEGER NOT NULL,
            interval VARCHAR(20) NOT NULL,
            description TEXT,
            features TEXT[],
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS subscriptions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            plan_id INTEGER REFERENCES subscription_plans(id),
            stripe_subscription_id VARCHAR(100) UNIQUE NOT NULL,
            stripe_customer_id VARCHAR(100) NOT NULL,
            status VARCHAR(20) NOT NULL,
            current_period_start TIMESTAMP NOT NULL,
            current_period_end TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS recipe_usage (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            recipe_count INTEGER DEFAULT 0,
            last_reset_date DATE DEFAULT CURRENT_DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS recipes (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            name VARCHAR(100) NOT NULL,            
            ingredients TEXT[],
            instructions TEXT[],
            calories INTEGER,
            protein FLOAT,
            carbs FLOAT,
            fat FLOAT,
            tags TEXT[],
            difficulty VARCHAR(50),
            dietary_info TEXT[],
            cooking_time INTEGER,
            prep_time INTEGER,
            weekend_prep TEXT[],            
            servings INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP                        
        );

        CREATE TABLE IF NOT EXISTS meal_plans (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            name VARCHAR(100),
            start_date DATE,
            end_date DATE,
            recipes JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS ratings (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            recipe_id INTEGER REFERENCES recipes(id),
            rating INTEGER CHECK (rating >= 1 AND rating <= 5),
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (user_id, recipe_id)
        );

        CREATE TABLE IF NOT EXISTS favorites (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            recipe_id INTEGER REFERENCES recipes(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, recipe_id)
        );

        CREATE TABLE IF NOT EXISTS user_meal_generations (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS user_subscriptions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            stripe_customer_id TEXT,
            stripe_subscription_id TEXT,
            subscription_status TEXT,
            subscription_type TEXT,
            starts_at TIMESTAMP,
            ends_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    init_database()
