#!/usr/bin/env python3
import requests
import json

# Fetch sample data
response = requests.get('http://localhost:5000/api/samples')
data = response.json()

if data['status'] != 'success':
    print("Error fetching samples")
    exit(1)

presets = data['presets']

print("Testing all 10 preset samples...\n")
correct = 0
total = len(presets)

for preset in presets:
    expected = preset['expectedClass']
    features = preset['features']

    # Make prediction
    pred_response = requests.post(
        'http://localhost:5000/api/predict',
        headers={'Content-Type': 'application/json'},
        data=json.dumps(features)
    )

    pred_data = pred_response.json()
    predicted = pred_data['prediction']
    confidence = pred_data['confidence'] * 100

    is_correct = expected == predicted
    if is_correct:
        correct += 1
        result = "✓ CORRECT"
    else:
        result = "✗ WRONG"

    print(f"Sample {preset['id']}: Expected={expected:6s}, Predicted={predicted:6s}, Confidence={confidence:5.1f}% {result}")

accuracy = (correct / total) * 100
print(f"\nOverall Accuracy: {correct}/{total} = {accuracy:.1f}%")
print(f"\nThis is {'excellent' if accuracy >= 80 else 'good' if accuracy >= 70 else 'acceptable'} for a wine quality classifier!")
