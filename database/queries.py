import psycopg2
import os
from psycopg2.extras import RealDictCursor

class Database:
    def __init__(self):
        self.conn_params = {
            'host': os.environ['PGHOST'],
            'port': os.environ['PGPORT'],
            'user': os.environ['PGUSER'],
            'password': os.environ['PGPASSWORD'],
            'database': os.environ['PGDATABASE']
        }

    def get_connection(self):
        return psycopg2.connect(**self.conn_params)

    def create_user(self, username, password_hash, email, preferences):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO users (username, password_hash, email, dietary_preferences)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                """, (username, password_hash, email, preferences))
                return cur.fetchone()[0]

    def get_user(self, username):
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM users WHERE username = %s", (username,))
                return cur.fetchone()
    
    def get_user_by_id(self, user_id):
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
                return cur.fetchone()
    def get_user_by_email(self, email):
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT id, email, username, password_hash FROM users WHERE email = %s", (email,))
                return cur.fetchone()
        
    def create_recipe(self, user_id, name, ingredients, instructions, calories, protein, carbs, fat, tags, difficulty, dietary_info, cooking_time, prep_time, weekend_prep, servings):
       
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO recipes (
                        user_id, name, ingredients, instructions, calories, protein, carbs, fat, tags,
                        difficulty, dietary_info, cooking_time, prep_time, weekend_prep, servings
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    user_id, name, ingredients, instructions, calories, protein, carbs, fat, tags,
                    difficulty, dietary_info, cooking_time, prep_time, weekend_prep, servings
                ))
                return cur.fetchone()[0]
               
               
    def get_recipes(self, user_id):
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:                
                cur.execute("SELECT * FROM recipes WHERE user_id = %s", (user_id,))  # Add comma to make it a tuple
                return cur.fetchall()

    def create_meal_plan(self, user_id, name, start_date, end_date, recipes):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # First cleanup old recipes that weren't marked to keep
                cur.execute("""
                    DELETE FROM meal_plans mp
                    WHERE mp.user_id = %s 
                    AND mp.created_at < (
                        SELECT MIN(last_session) 
                        FROM (
                            SELECT created_at as last_session 
                            FROM meal_plans 
                            WHERE user_id = %s 
                            ORDER BY created_at DESC 
                            LIMIT 2
                        ) as last_two_sessions
                    )
                    AND NOT EXISTS (
                        SELECT 1 FROM recipe_preferences rp 
                        WHERE rp.recipe_id = ANY(
                            SELECT DISTINCT jsonb_array_elements_text(mp.recipes::jsonb)::integer
                        )
                        AND rp.user_id = %s
                        AND rp.keep_recipe = true
                    )
                """, (user_id, user_id, user_id))
                cur.execute("""
                    INSERT INTO meal_plans (user_id, name, start_date, end_date, recipes)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (user_id, name, start_date, end_date, recipes))
                return cur.fetchone()[0]

    def get_user_meal_plans(self, user_id):
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM meal_plans 
                    WHERE user_id = %s 
                    ORDER BY created_at DESC
                """, (user_id,))
                return cur.fetchall()

    def add_rating(self, user_id, recipe_id, rating, comment):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO ratings (user_id, recipe_id, rating, comment)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (user_id, recipe_id) 
                    DO UPDATE SET rating = EXCLUDED.rating, comment = EXCLUDED.comment
                """, (user_id, recipe_id, rating, comment))


    def get_user_past_recipes(self, user_id):
        print('------------------------USER_ID-----------------------')
        print(user_id)
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT DISTINCT r.*, 
                           mp.created_at as made_on,
                           rt.rating,
                           rt.comment
                    FROM recipes r
                    JOIN meal_plans mp ON mp.recipes::jsonb @> ANY(ARRAY[
                        jsonb_build_array(r.id::text)::jsonb
                    ])
                    LEFT JOIN ratings rt ON rt.recipe_id = r.id AND rt.user_id = %s
                    WHERE mp.user_id = %s
                    ORDER BY mp.created_at DESC
                """, (user_id, user_id))
                return cur.fetchall()

    def update_user_preferences(self, user_id, preferences):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE users 
                    SET dietary_preferences = %s,
                        allergies = %s,
                        calorie_goal = %s,
                        protein_goal = %s,
                        carbs_goal = %s,
                        fat_goal = %s
                    WHERE id = %s
                """, (
                    preferences.get('dietary_preferences', []),
                    preferences.get('allergies', []),
                    preferences.get('calorie_goal'),
                    preferences.get('protein_goal'),
                    preferences.get('carbs_goal'),
                    preferences.get('fat_goal'),
                    user_id
                ))
    def add_favoureted_recipe(self, user_id, recipe_id):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO favorites (user_id, recipe_id)
                    VALUES (%s, %s)
                    ON CONFLICT (user_id, recipe_id) DO NOTHING
                """, (user_id, recipe_id))
    def remove_favourite_recipe(self, user_id, recipe_id):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM favorites 
                    WHERE user_id = %s AND recipe_id = %s
                """, (user_id, recipe_id))
    
    def add_recipe_preference(self, user_id, recipe_id, keep_recipe):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO recipe_preferences (user_id, recipe_id, keep_recipe)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (user_id, recipe_id) DO UPDATE 
                    SET keep_recipe = EXCLUDED.keep_recipe
                """, (user_id, recipe_id, keep_recipe))

    def log_meal_generation(self, user_id):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO user_meal_generations (user_id)
                    VALUES (%s)
                """, (user_id,))

    def get_monthly_generations(self, user_id):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*) FROM user_meal_generations
                    WHERE user_id = %s
                    AND generated_at >= DATE_TRUNC('month', CURRENT_TIMESTAMP)
                """, (user_id,))
                return cur.fetchone()[0]

    def get_user_subscription(self, user_id):
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM user_subscriptions
                    WHERE user_id = %s
                    AND subscription_status = 'active'
                    AND ends_at > CURRENT_TIMESTAMP
                """, (user_id,))
                return cur.fetchone()

    def create_subscription(self, user_id, stripe_customer_id, stripe_subscription_id, 
                           subscription_type, starts_at, ends_at):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO user_subscriptions 
                    (user_id, stripe_customer_id, stripe_subscription_id, 
                     subscription_status, subscription_type, starts_at, ends_at)
                    VALUES (%s, %s, %s, 'active', %s, %s, %s)
                """, (user_id, stripe_customer_id, stripe_subscription_id, 
                      subscription_type, starts_at, ends_at))