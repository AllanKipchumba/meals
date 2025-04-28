import os
import json
import requests
from typing import Dict, List, Optional
import streamlit as st

class USDANutrientCalculator:
    def __init__(self):
        self.api_key = os.environ.get("USDA_API_KEY")
        self.base_url = "https://api.nal.usda.gov/fdc/v1"
        self.cache = {}
        
        # USDA nutrient IDs
        self.NUTRIENT_IDS = {
            'protein': 1003,      # Protein
            'total_fat': 1004,    # Total Fat
            'carbs': 1005,        # Carbohydrates
            'calories': 1008,     # Energy (kcal)
            'saturated_fat': 1258 # Saturated Fat
        }
    
    def search_food(self, query: str) -> Optional[Dict]:
        """
        Search for a food item in the USDA database
        """
        if query in self.cache:
            return self.cache[query]
            
        try:
            params = {
                'api_key': self.api_key,
                'query': query,
                'dataType': ["Foundation", "SR Legacy"],
                'pageSize': 1
            }
            
            response = requests.get(
                f"{self.base_url}/foods/search",
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            if data['foods']:
                food = data['foods'][0]
                self.cache[query] = food
                return food
            return None
            
        except Exception as e:
            st.error(f"Error searching USDA database: {str(e)}")
            return None
    
    def get_nutrient_value(self, nutrients: List[Dict], nutrient_id: int) -> float:
        """
        Extract specific nutrient value from nutrients list
        """
        for nutrient in nutrients:
            if nutrient.get('nutrientId') == nutrient_id:
                return float(nutrient.get('value', 0))
        return 0.0
    
    def get_nutrients_for_ingredient(self, ingredient: str, quantity: float, unit: str) -> Dict[str, float]:
        """
        Get nutritional information for an ingredient
        """
        # Extract the main ingredient name (remove quantities and units)
        ingredient_name = ' '.join(word for word in ingredient.split() 
                                 if not any(char.isdigit() for char in word)
                                 and word.lower() not in ['g', 'grams', 'oz', 'ounces', 'lbs', 'pounds'])
        
        food = self.search_food(ingredient_name)
        if not food:
            return {nutrient: 0.0 for nutrient in self.NUTRIENT_IDS.keys()}
        
        # Convert quantity to grams for calculation
        grams = self.convert_to_grams(quantity, unit)
        if grams is None:
            return {nutrient: 0.0 for nutrient in self.NUTRIENT_IDS.keys()}
        
        # Calculate nutrients based on portion size
        nutrients = food.get('foodNutrients', [])
        serving_size = float(food.get('servingSize', 100))
        serving_unit = food.get('servingSizeUnit', 'g')
        
        if serving_unit != 'g':
            serving_size = self.convert_to_grams(serving_size, serving_unit) or 100
            
        multiplier = grams / serving_size
        
        return {
            nutrient: round(self.get_nutrient_value(nutrients, nutrient_id) * multiplier, 1)
            for nutrient, nutrient_id in self.NUTRIENT_IDS.items()
        }
    
    def convert_to_grams(self, quantity: float, unit: str) -> Optional[float]:
        """
        Convert various units to grams
        """
        unit = unit.lower().strip()
        
        # Handle common descriptive measurements
        if unit in ['large', 'small', 'medium']:
            conversions = {
                'onion': {'large': 150, 'medium': 110, 'small': 70},
                'carrot': {'large': 72, 'medium': 61, 'small': 50},
                'potato': {'large': 213, 'medium': 156, 'small': 99},
                # Add more common vegetables as needed
            }
            # Default to medium if specific conversion not found
            return quantity * 100
            
        elif unit in ['bunch', 'head']:
            conversions = {
                'asparagus': 500,  # 1 bunch ≈ 500g
                'broccoli': 608,   # 1 head ≈ 608g
                'lettuce': 539,    # 1 head ≈ 539g
                # Add more items as needed
            }
            return quantity * 500  # Default to 500g if specific conversion not found
            
        # Standard weight conversions
        conversions = {
            'g': 1,
            'gram': 1,
            'grams': 1,
            'kg': 1000,
            'kilogram': 1000,
            'kilograms': 1000,
            'oz': 28.3495,
            'ounce': 28.3495,
            'ounces': 28.3495,
            'lb': 453.592,
            'pound': 453.592,
            'pounds': 453.592,
            # Volume to weight approximations for common ingredients
            'cup': 236.588,
            'cups': 236.588,
            'tbsp': 14.787,
            'tablespoon': 14.787,
            'tablespoons': 14.787,
            'tsp': 4.929,
            'teaspoon': 4.929,
            'teaspoons': 4.929,
        }
        
        return quantity * conversions.get(unit, 0) if unit in conversions else None

    def calculate_recipe_nutrients(self, ingredients: List[str]) -> Dict[str, float]:
        """
        Calculate total nutrients for a recipe
        """
        from utils.shopping_list import parse_ingredient
        
        total_nutrients = {nutrient: 0.0 for nutrient in self.NUTRIENT_IDS.keys()}
        
        for ingredient in ingredients:
            quantity, unit, descriptor, item = parse_ingredient(ingredient)
            
            # If descriptor exists, combine it with the item for better USDA search
            search_item = f"{descriptor} {item}" if descriptor else item
            nutrients = self.get_nutrients_for_ingredient(search_item, quantity, unit)
            
            for nutrient in total_nutrients:
                total_nutrients[nutrient] += nutrients[nutrient]
        
        return {k: round(v, 1) for k, v in total_nutrients.items()}
