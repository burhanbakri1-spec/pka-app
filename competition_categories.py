KUMITE_CATEGORIES = {
    "6-7": {
        "Male": [
            {"label": "-22kg", "min_weight": None, "max_weight": 22},
            {"label": "-28kg", "min_weight": 22.01, "max_weight": 28},
            {"label": "-32kg", "min_weight": 28.01, "max_weight": 32},
            {"label": "-34kg", "min_weight": 32.01, "max_weight": 34},
            {"label": "+34kg", "min_weight": 34.01, "max_weight": None},
        ],
        "Female": [
            {"label": "-20kg", "min_weight": None, "max_weight": 20},
            {"label": "-24kg", "min_weight": 20.01, "max_weight": 24},
            {"label": "-28kg", "min_weight": 24.01, "max_weight": 28},
            {"label": "-32kg", "min_weight": 28.01, "max_weight": 32},
            {"label": "+32kg", "min_weight": 32.01, "max_weight": None},
        ],
    },
    "8-9": {
        "Male": [
            {"label": "-28kg", "min_weight": None, "max_weight": 28},
            {"label": "-32kg", "min_weight": 28.01, "max_weight": 32},
            {"label": "-36kg", "min_weight": 32.01, "max_weight": 36},
            {"label": "-40kg", "min_weight": 36.01, "max_weight": 40},
            {"label": "-44kg", "min_weight": 40.01, "max_weight": 44},
            {"label": "+44kg", "min_weight": 44.01, "max_weight": None},
        ],
        "Female": [
            {"label": "-26kg", "min_weight": None, "max_weight": 26},
            {"label": "-30kg", "min_weight": 26.01, "max_weight": 30},
            {"label": "-34kg", "min_weight": 30.01, "max_weight": 34},
            {"label": "-38kg", "min_weight": 34.01, "max_weight": 38},
            {"label": "-42kg", "min_weight": 38.01, "max_weight": 42},
            {"label": "+42kg", "min_weight": 42.01, "max_weight": None},
        ],
    },
    "10-11": {
        "Male": [
            {"label": "-37kg", "min_weight": None, "max_weight": 37},
            {"label": "-42kg", "min_weight": 37.01, "max_weight": 42},
            {"label": "-47kg", "min_weight": 42.01, "max_weight": 47},
            {"label": "-52kg", "min_weight": 47.01, "max_weight": 52},
            {"label": "+52kg", "min_weight": 52.01, "max_weight": None},
        ],
        "Female": [
            {"label": "-35kg", "min_weight": None, "max_weight": 35},
            {"label": "-40kg", "min_weight": 35.01, "max_weight": 40},
            {"label": "-45kg", "min_weight": 40.01, "max_weight": 45},
            {"label": "-50kg", "min_weight": 45.01, "max_weight": 50},
            {"label": "+50kg", "min_weight": 50.01, "max_weight": None},
        ],
    },
    "12-13": {
        "Male": [
            {"label": "-40kg", "min_weight": None, "max_weight": 40},
            {"label": "-45kg", "min_weight": 40.01, "max_weight": 45},
            {"label": "-50kg", "min_weight": 45.01, "max_weight": 50},
            {"label": "-55kg", "min_weight": 50.01, "max_weight": 55},
            {"label": "+55kg", "min_weight": 55.01, "max_weight": None},
        ],
        "Female": [
            {"label": "-39kg", "min_weight": None, "max_weight": 39},
            {"label": "-44kg", "min_weight": 39.01, "max_weight": 44},
            {"label": "-49kg", "min_weight": 44.01, "max_weight": 49},
            {"label": "-54kg", "min_weight": 49.01, "max_weight": 54},
            {"label": "+54kg", "min_weight": 54.01, "max_weight": None},
        ],
    },
    "Cadets": { # 14-15 years old (assuming Cadets are 14-15)
        "Male": [
            {"label": "-52kg", "min_weight": None, "max_weight": 52},
            {"label": "-57kg", "min_weight": 52.01, "max_weight": 57},
            {"label": "-63kg", "min_weight": 57.01, "max_weight": 63},
            {"label": "-70kg", "min_weight": 63.01, "max_weight": 70},
            {"label": "+70kg", "min_weight": 70.01, "max_weight": None},
        ],
        "Female": [
            {"label": "-47kg", "min_weight": None, "max_weight": 47},
            {"label": "-54kg", "min_weight": 47.01, "max_weight": 54},
            {"label": "+54kg", "min_weight": 54.01, "max_weight": None},
        ],
    },
    "Juniors": { # 16-17 years old (assuming Juniors are 16-17)
        "Male": [
            {"label": "-55kg", "min_weight": None, "max_weight": 55},
            {"label": "-61kg", "min_weight": 55.01, "max_weight": 61},
            {"label": "-68kg", "min_weight": 61.01, "max_weight": 68},
            {"label": "-76kg", "min_weight": 68.01, "max_weight": 76},
            {"label": "+76kg", "min_weight": 76.01, "max_weight": None},
        ],
        "Female": [
            {"label": "-48kg", "min_weight": None, "max_weight": 48},
            {"label": "-53kg", "min_weight": 48.01, "max_weight": 53},
            {"label": "-59kg", "min_weight": 53.01, "max_weight": 59},
            {"label": "-66kg", "min_weight": 59.01, "max_weight": 66},
            {"label": "+66kg", "min_weight": 66.01, "max_weight": None},
        ],
    },
    "U21": { # 18-20 years old (assuming U21 are 18-20)
        "Male": [
            {"label": "-60kg", "min_weight": None, "max_weight": 60},
            {"label": "-67kg", "min_weight": 60.01, "max_weight": 67},
            {"label": "-75kg", "min_weight": 67.01, "max_weight": 75},
            {"label": "-84kg", "min_weight": 75.01, "max_weight": 84},
            {"label": "+84kg", "min_weight": 84.01, "max_weight": None},
        ],
        "Female": [
            {"label": "-50kg", "min_weight": None, "max_weight": 50},
            {"label": "-55kg", "min_weight": 50.01, "max_weight": 55},
            {"label": "-61kg", "min_weight": 55.01, "max_weight": 61},
            {"label": "-68kg", "min_weight": 61.01, "max_weight": 68},
            {"label": "+68kg", "min_weight": 68.01, "max_weight": None},
        ],
    },
    "Seniors": { # 21+ years old
        "Male": [
            {"label": "-60kg", "min_weight": None, "max_weight": 60},
            {"label": "-67kg", "min_weight": 60.01, "max_weight": 67},
            {"label": "-75kg", "min_weight": 67.01, "max_weight": 75},
            {"label": "-84kg", "min_weight": 75.01, "max_weight": 84},
            {"label": "+84kg", "min_weight": 84.01, "max_weight": None},
        ],
        "Female": [
            {"label": "-50kg", "min_weight": None, "max_weight": 50},
            {"label": "-55kg", "min_weight": 50.01, "max_weight": 55},
            {"label": "-61kg", "min_weight": 55.01, "max_weight": 61},
            {"label": "-68kg", "min_weight": 61.01, "max_weight": 68},
            {"label": "+68kg", "min_weight": 68.01, "max_weight": None},
        ],
    },
}

KATA_CATEGORIES = {
    "6-7": {"Male": ["Kata Individual (6-7 years)"], "Female": ["Kata Individual (6-7 years)"]},
    "8-9": {"Male": ["Kata Individual (8-9 years)"], "Female": ["Kata Individual (8-9 years)"]},
    "10-11": {"Male": ["Kata Individual (10-11 years)"], "Female": ["Kata Individual (10-11 years)"]},
    "12-13": {"Male": ["Kata Individual (12-13 years)"], "Female": ["Kata Individual (12-13 years)"]},
    "Cadets": {"Male": ["Kata Individual (Cadets)"], "Female": ["Kata Individual (Cadets)"]},
    "Juniors": {"Male": ["Kata Individual (Juniors)"], "Female": ["Kata Individual (Juniors)"]},
    "U21": {"Male": ["Kata Individual (U21)"], "Female": ["Kata Individual (U21)"]},
    "Seniors": {"Male": ["Kata Individual (Seniors)"], "Female": ["Kata Individual (Seniors)"]},
}

# Age ranges for mapping
AGE_RANGES = [
    (6, 7, "6-7"),
    (8, 9, "8-9"),
    (10, 11, "10-11"),
    (12, 13, "12-13"),
    (14, 15, "Cadets"), # Assuming Cadets are 14-15
    (16, 17, "Juniors"), # Assuming Juniors are 16-17
    (18, 20, "U21"),     # Assuming U21 are 18-20
    (18, 150, "Seniors"), # Seniors can compete from 18+
]