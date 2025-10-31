# calorie_db.py
CALORIE_DB = {
    "apple": {"calories": 95, "protein": 0.5, "fats": 0.3},
    "banana": {"calories": 105, "protein": 1.3, "fats": 0.4},
    "burger_beef": {"calories": 354, "protein": 25, "fats": 20},
    "burger_chicken": {"calories": 300, "protein": 22, "fats": 15},
    "pizza": {"calories": 285, "protein": 12, "fats": 10},
    "cake": {"calories": 235, "protein": 3, "fats": 8},
    "sandwich": {"calories": 250, "protein": 12, "fats": 8},
    "french_fries": {"calories": 365, "protein": 4, "fats": 17},
    "fried_chicken": {"calories": 246, "protein": 19, "fats": 15},
    "chow_mein": {"calories": 281, "protein": 14, "fats": 10},
    "boiled_egg": {"calories": 77, "protein": 6, "fats": 5},
    "donut": {"calories": 195, "protein": 2, "fats": 11},
    "salad": {"calories": 152, "protein": 8, "fats": 12},
    "sushi": {"calories": 200, "protein": 9, "fats": 7},
    "steak": {"calories": 679, "protein": 62, "fats": 45},
    "appam": {"calories": 110, "protein": 2, "fats": 1},
    "beetroot_poriyal": {"calories": 85, "protein": 3, "fats": 4},
    "carrot_poriyal": {"calories": 75, "protein": 2, "fats": 3},
    "chicken_65": {"calories": 280, "protein": 20, "fats": 18},
    "chicken_briyani": {"calories": 320, "protein": 18, "fats": 12},
    "dosa": {"calories": 168, "protein": 4, "fats": 8},
    "idly": {"calories": 58, "protein": 2, "fats": 0.5},
    "kaara_chutney": {"calories": 45, "protein": 1, "fats": 2},
    "kali": {"calories": 180, "protein": 4, "fats": 8},
    "koozh": {"calories": 120, "protein": 3, "fats": 2},
    "lemon_satham": {"calories": 200, "protein": 4, "fats": 6},
    "medu_vadai": {"calories": 150, "protein": 6, "fats": 8},
    "mushroom_briyani": {"calories": 290, "protein": 12, "fats": 10},
    "mutton_briyani": {"calories": 380, "protein": 22, "fats": 15},
    "nandu_masala": {"calories": 220, "protein": 18, "fats": 12},
    "nei_satham": {"calories": 250, "protein": 5, "fats": 12},
    "paal_kolukattai": {"calories": 140, "protein": 4, "fats": 6},
    "paneer_briyani": {"calories": 310, "protein": 15, "fats": 14},
    "paneer_masala": {"calories": 260, "protein": 14, "fats": 18},
    "parupu_vadai": {"calories": 130, "protein": 5, "fats": 6},
    "pidi_kolukattai": {"calories": 125, "protein": 3, "fats": 4},
    "poorna_kolukattai": {"calories": 160, "protein": 4, "fats": 6},
    "prawn_thokku": {"calories": 180, "protein": 16, "fats": 8},
    "puthina_chutney": {"calories": 40, "protein": 1, "fats": 1},
    "sambar": {"calories": 95, "protein": 4, "fats": 3},
    "sambar_satham": {"calories": 220, "protein": 6, "fats": 5},
    "satham": {"calories": 205, "protein": 4, "fats": 0.5},
    "thengai_chutney": {"calories": 65, "protein": 1, "fats": 6},
    "veg_briyani": {"calories": 270, "protein": 8, "fats": 8},
    "ven_pongal": {"calories": 190, "protein": 5, "fats": 7},

}

def canonicalize_class(name: str) -> str:
    if not name:
        return name
    n = name.lower().strip().replace(" ", "_")
    synonyms = {
        "burger": "burger_beef",
        "beef_burger": "burger_beef",
        "chicken_burger": "burger_chicken",
        "fries": "french_fries",
        "chips": "french_fries",
        "fried_chicken": "fried_chicken",
        "chow mein": "chow_mein",
        "boiled egg": "boiled_egg",
        "doughnut": "donut",
        
    }
    return synonyms.get(n, n)
