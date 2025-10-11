# minimal calorie DB; extend with your dataset classes
CALORIE_DB = {
    "apple": 95,
    "banana": 105,
    "burger_beef": 354,
    "burger_chicken": 300,
    "pizza": 285,
    "cake": 235,
    "sandwich": 250,
    "french_fries": 365,
    # add more mappings...
}

def canonicalize_class(name: str) -> str:
    """
    Normalize a class name to match CALORIE_DB keys:
      - lower, strip, replace spaces with underscores
      - basic synonyms mapping can be added here
    """
    if not name:
        return name
    n = name.lower().strip().replace(" ", "_")
    # simple synonyms
    synonyms = {
        "burger": "burger_beef",
        "fries": "french_fries",
        "chips": "french_fries",
        "doughnut": "donut",
    }
    return synonyms.get(n, n)
