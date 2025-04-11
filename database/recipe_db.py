import pandas as pd
import json
from typing import List, Dict, Optional

class RecipeDatabase:
    def __init__(self):
        # Initialize with sample recipes for different meal types
        self.recipes = pd.DataFrame({
            'name': [
                'Overnight Oats',
                'Greek Yogurt Parfait',
                'Avocado Toast',
                'Grilled Chicken Salad',
                'Vegetarian Stir Fry',
                'Keto Beef Bowl',
                'Quinoa Buddha Bowl',
                'Salmon with Roasted Vegetables',
                'Turkey Meatballs with Zucchini Noodles',
                'Breakfast Smoothie Bowl',
                'Egg White Omelette',
                'Protein Pancakes',
                'Chicken Quinoa Bowl',
                'Shrimp Tacos',
                'Baked Cod with Sweet Potato'
            ],
            'meal_type': [
                'breakfast', 'breakfast', 'breakfast',
                'lunch_dinner', 'lunch_dinner', 'lunch_dinner',
                'lunch_dinner', 'lunch_dinner', 'lunch_dinner',
                'breakfast', 'breakfast', 'breakfast',
                'lunch_dinner', 'lunch_dinner', 'lunch_dinner'
            ],
            'ingredients': [
                ['oats', 'almond milk', 'chia seeds', 'berries', 'honey'],
                ['greek yogurt', 'granola', 'berries', 'honey'],
                ['bread', 'avocado', 'eggs', 'tomatoes', 'salt'],
                ['chicken breast', 'lettuce', 'tomatoes', 'olive oil'],
                ['tofu', 'broccoli', 'carrots', 'soy sauce'],
                ['ground beef', 'avocado', 'cauliflower rice', 'cheese'],
                ['quinoa', 'chickpeas', 'sweet potato', 'kale', 'tahini'],
                ['salmon', 'broccoli', 'carrots', 'olive oil', 'lemon'],
                ['ground turkey', 'zucchini', 'marinara sauce', 'parmesan'],
                ['banana', 'berries', 'almond milk', 'protein powder'],
                ['egg whites', 'spinach', 'mushrooms', 'feta cheese'],
                ['oats', 'protein powder', 'banana', 'eggs', 'maple syrup'],
                ['chicken breast', 'quinoa', 'bell peppers', 'black beans'],
                ['shrimp', 'corn tortillas', 'cabbage slaw', 'lime'],
                ['cod', 'sweet potato', 'asparagus', 'olive oil']
            ],
            'nutritional_info': [
                {'calories': 300, 'protein': 12, 'carbs': 45, 'fat': 10},
                {'calories': 250, 'protein': 15, 'carbs': 35, 'fat': 8},
                {'calories': 350, 'protein': 15, 'carbs': 30, 'fat': 20},
                {'calories': 350, 'protein': 40, 'carbs': 10, 'fat': 15},
                {'calories': 300, 'protein': 15, 'carbs': 25, 'fat': 12},
                {'calories': 450, 'protein': 35, 'carbs': 8, 'fat': 35},
                {'calories': 400, 'protein': 20, 'carbs': 50, 'fat': 15},
                {'calories': 380, 'protein': 35, 'carbs': 15, 'fat': 20},
                {'calories': 320, 'protein': 30, 'carbs': 12, 'fat': 18},
                {'calories': 280, 'protein': 20, 'carbs': 40, 'fat': 5},
                {'calories': 200, 'protein': 25, 'carbs': 8, 'fat': 10},
                {'calories': 350, 'protein': 30, 'carbs': 35, 'fat': 12},
                {'calories': 380, 'protein': 35, 'carbs': 40, 'fat': 12},
                {'calories': 320, 'protein': 25, 'carbs': 30, 'fat': 15},
                {'calories': 300, 'protein': 32, 'carbs': 25, 'fat': 10}
            ],
            'difficulty': [
                'easy', 'easy', 'easy',
                'easy', 'medium', 'easy',
                'medium', 'medium', 'medium',
                'easy', 'easy', 'medium',
                'medium', 'medium', 'medium'
            ],
            'prep_time': [
                10, 5, 15,
                20, 30, 25,
                25, 35, 30,
                10, 15, 20,
                25, 30, 35
            ],
            'dietary_tags': [
                ['vegetarian'], 
                ['vegetarian'], 
                ['vegetarian'],
                ['high_protein', 'low_carb'],
                ['vegetarian', 'vegan'],
                ['keto', 'low_carb'],
                ['vegetarian', 'vegan'],
                ['high_protein'],
                ['high_protein', 'low_carb'],
                ['vegetarian'],
                ['high_protein', 'low_carb'],
                ['high_protein'],
                ['high_protein'],
                ['high_protein'],
                ['high_protein', 'low_carb']
            ]
        })

    def get_recipes_by_preferences(
        self,
        dietary_restrictions: List[str],
        max_prep_time: int,
        difficulty_level: str,
        nutritional_goals: Dict[str, int],
        meal_type: str = None,
        num_recipes: int = 1
    ) -> pd.DataFrame:
        """
        Get personalized recipe suggestions based on user preferences
        """
        filtered_recipes = self.recipes.copy()

        # Filter by meal type if specified
        if meal_type:
            filtered_recipes = filtered_recipes[filtered_recipes['meal_type'] == meal_type]

        # Filter by dietary restrictions
        if dietary_restrictions:
            filtered_recipes = filtered_recipes[
                filtered_recipes['dietary_tags'].apply(
                    lambda x: any(tag in x for tag in dietary_restrictions)
                )
            ]

        # Filter by prep time
        filtered_recipes = filtered_recipes[filtered_recipes['prep_time'] <= max_prep_time]

        # Filter by difficulty
        difficulty_mapping = {
            'Beginner': ['easy'],
            'Intermediate': ['easy', 'medium'],
            'Advanced': ['easy', 'medium', 'hard']
        }
        allowed_difficulties = difficulty_mapping.get(difficulty_level, ['easy', 'medium'])
        filtered_recipes = filtered_recipes[
            filtered_recipes['difficulty'].isin(allowed_difficulties)
        ]

        # Score recipes based on nutritional goals
        def calculate_nutrition_score(recipe_nutrition):
            score = 0
            for key in ['protein', 'carbs', 'fat']:
                if key in nutritional_goals and key in recipe_nutrition:
                    # Lower score means better match
                    score += abs(recipe_nutrition[key] - nutritional_goals[key]/3)  # Divide by 3 for per-meal targets
            return score

        filtered_recipes['nutrition_score'] = filtered_recipes['nutritional_info'].apply(
            calculate_nutrition_score
        )

        # Sort by nutrition score (lower is better) and get requested number of recipes
        filtered_recipes = filtered_recipes.sort_values('nutrition_score')
        filtered_recipes = filtered_recipes.head(num_recipes)

        return filtered_recipes.drop('nutrition_score', axis=1)

    def get_weekly_meal_plan(
        self,
        dietary_restrictions: List[str],
        max_prep_time: int,
        difficulty_level: str,
        nutritional_goals: Dict[str, int]
    ) -> Dict[str, pd.DataFrame]:
        """
        Generate a complete weekly meal plan
        """
        # Get 7 breakfast recipes
        breakfasts = self.get_recipes_by_preferences(
            dietary_restrictions=dietary_restrictions,
            max_prep_time=max_prep_time,
            difficulty_level=difficulty_level,
            nutritional_goals=nutritional_goals,
            meal_type='breakfast',
            num_recipes=7
        )

        # Get 1 Monday lunch recipe
        monday_lunch = self.get_recipes_by_preferences(
            dietary_restrictions=dietary_restrictions,
            max_prep_time=max_prep_time,
            difficulty_level=difficulty_level,
            nutritional_goals=nutritional_goals,
            meal_type='lunch_dinner',
            num_recipes=1
        )

        # Get 7 dinner recipes
        dinners = self.get_recipes_by_preferences(
            dietary_restrictions=dietary_restrictions,
            max_prep_time=max_prep_time,
            difficulty_level=difficulty_level,
            nutritional_goals=nutritional_goals,
            meal_type='lunch_dinner',
            num_recipes=7
        )

        return {
            'breakfasts': breakfasts,
            'monday_lunch': monday_lunch,
            'dinners': dinners
        }
