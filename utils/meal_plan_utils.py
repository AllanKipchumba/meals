from datetime import datetime, timedelta
import json
from database.queries import Database

def create_weekly_plan(user_id, recipes, start_date):
    """Create a weekly meal plan"""
    db = Database()
    
    # Structure the meal plan
    meal_plan = {
        'breakfast': [],
        'lunch': [],
        'dinner': []
    }
    
    # Distribute recipes across the week
    for i in range(7):
        day = start_date + timedelta(days=i)
        day_plan = {
            'date': day.strftime('%Y-%m-%d'),
            'meals': {
                'breakfast': recipes[i % len(recipes)]['id'],
                'lunch': recipes[(i + 1) % len(recipes)]['id'],
                'dinner': recipes[(i + 2) % len(recipes)]['id']
            }
        }
        for meal_type in meal_plan:
            meal_plan[meal_type].append(day_plan['meals'][meal_type])
    
    # Save meal plan to database
    plan_id = db.create_meal_plan(
        user_id=user_id,
        name=f"Meal Plan {start_date.strftime('%Y-%m-%d')}",
        start_date=start_date,
        end_date=start_date + timedelta(days=6),
        recipes=json.dumps(meal_plan)
    )
    
    return plan_id

def get_meal_plan_nutrition(meal_plan):
    """Calculate nutritional totals for a meal plan"""
    db = Database()
    total_nutrition = {
        'calories': 0,
        'protein': 0,
        'carbs': 0,
        'fat': 0
    }
    
    recipes = json.loads(meal_plan['recipes'])
    for meal_type in recipes:
        for recipe_id in recipes[meal_type]:
            recipe = db.get_recipe_by_id(recipe_id)
            total_nutrition['calories'] += recipe['calories']
            total_nutrition['protein'] += recipe['protein']
            total_nutrition['carbs'] += recipe['carbs']
            total_nutrition['fat'] += recipe['fat']
    
    return total_nutrition
