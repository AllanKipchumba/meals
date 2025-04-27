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
            is_premium BOOLEAN DEFAULT FALSE,
            meal_gen_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
        
        CREATE TABLE IF NOT EXISTS payments (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            amount DECIMAL(10, 2) NOT NULL,
            currency VARCHAR(3) DEFAULT 'USD',
            payment_method VARCHAR(50),
            status VARCHAR(20) NOT NULL,
            transaction_id VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # Check if columns exist, add them if they don't
    cur.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'is_premium') THEN
            ALTER TABLE users ADD COLUMN is_premium BOOLEAN DEFAULT FALSE;
        END IF;
        
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'meal_gen_count') THEN
            ALTER TABLE users ADD COLUMN meal_gen_count INTEGER DEFAULT 0;
        END IF;
        
        -- Remove premium_until column if exists (since premium is now permanent)
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'premium_until') THEN
            ALTER TABLE users DROP COLUMN premium_until;
        END IF;

        -- Update payments table to remove subscription fields if they exist
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'payments' AND column_name = 'plan_name') THEN
            ALTER TABLE payments DROP COLUMN plan_name;
        END IF;
        
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'payments' AND column_name = 'plan_duration_months') THEN
            ALTER TABLE payments DROP COLUMN plan_duration_months;
        END IF;
    END
    $$;
    """)
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    init_database()
