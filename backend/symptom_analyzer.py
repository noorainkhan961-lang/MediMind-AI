def analyze_symptoms(symptoms, description=""):
    symptoms = [
        str(item).strip().lower()
        for item in symptoms
        if isinstance(item, str)
    ]
    description = description.strip().lower()
    text = " ".join(symptoms + [description])
    conditions = []

    def has_any(keywords):
        return any(keyword in text for keyword in keywords)

    if has_any(["weight gain", "feeling cold", "hair loss", "fatigue", "tiredness"]):
        conditions.append({
            "name": "Thyroid-related conditions",
            "reason": "Some reported symptoms can occur with thyroid conditions, but they can also have other causes.",
            "tests_to_discuss": ["TSH", "Free T4"]
        })

    if has_any(["frequent urination", "excessive thirst", "increased thirst", "blurred vision"]):
        conditions.append({
            "name": "Diabetes-related concerns",
            "reason": "Increased thirst and frequent urination can occur with diabetes and other health conditions.",
            "tests_to_discuss": ["Fasting blood glucose", "HbA1c"]
        })

    if has_any(["dizziness", "weakness", "pale skin", "fatigue", "tiredness"]):
        conditions.append({
            "name": "Anaemia-related concerns",
            "reason": "Weakness, dizziness and tiredness can sometimes occur with anaemia.",
            "tests_to_discuss": ["Complete blood count (CBC)", "Iron studies"]
        })

    if has_any(["irregular periods", "missed periods", "excess facial hair"]):
        conditions.append({
            "name": "PCOS-related concerns",
            "reason": "Irregular periods and excess facial hair can be associated with PCOS, but do not confirm it.",
            "tests_to_discuss": ["Clinical assessment", "Hormone assessment if advised"]
        })

    if has_any(["cough", "cold", "sore throat", "breathing difficulty"]):
        conditions.append({
            "name": "Respiratory conditions",
            "reason": "These symptoms can occur with respiratory infections and other breathing conditions.",
            "tests_to_discuss": ["Clinical examination", "Further tests if advised by a clinician"]
        })

    if has_any(["stomach pain", "abdominal pain", "acidity", "vomiting", "constipation"]):
        conditions.append({
            "name": "Digestive conditions",
            "reason": "These symptoms can have several digestive and non-digestive causes.",
            "tests_to_discuss": ["Clinical examination", "Further tests if advised"]
        })

    if has_any(["headache", "migraine"]):
        conditions.append({
            "name": "Headache-related conditions",
            "reason": "Headaches have several possible causes, including migraine.",
            "tests_to_discuss": ["Clinical assessment"]
        })

    if not conditions:
        conditions.append({
            "name": "More information needed",
            "reason": "The available information is not enough to identify relevant health possibilities.",
            "tests_to_discuss": ["Discuss your symptoms with a healthcare professional"]
        })

    return {
        "possible_conditions": conditions,
        "general_advice": [
            "Keep track of when symptoms started and how they change.",
            "Maintain regular meals, hydration and adequate rest.",
            "Consult a qualified healthcare professional for assessment."
        ],
        "disclaimer": (
            "This report provides general educational information only. "
            "It is not a diagnosis, and symptoms alone cannot confirm a medical condition. "
            "A qualified healthcare professional must assess your health and interpret any test results."
        )
    }
