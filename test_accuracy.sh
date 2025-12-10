#!/bin/bash

echo "Testing all 10 preset samples..."
echo ""

correct=0
total=10

# Get all samples
samples=$(curl -s http://localhost:5000/api/samples)

for i in $(seq 0 9); do
  # Extract expected class and features for this sample
  expected=$(echo "$samples" | jq -r ".presets[$i].expectedClass")
  features=$(echo "$samples" | jq -c ".presets[$i].features")
  sample_id=$(echo "$samples" | jq -r ".presets[$i].id")

  # Make prediction
  prediction=$(curl -s -X POST http://localhost:5000/api/predict \
    -H "Content-Type: application/json" \
    -d "$features")

  predicted=$(echo "$prediction" | jq -r '.prediction')
  confidence=$(echo "$prediction" | jq -r '.confidence')
  confidence_pct=$(echo "$confidence * 100" | bc -l | xargs printf "%.1f")

  # Check if correct
  if [ "$expected" = "$predicted" ]; then
    result="✓ CORRECT"
    ((correct++))
  else
    result="✗ WRONG"
  fi

  printf "Sample %d: Expected=%-6s Predicted=%-6s Confidence=%5.1f%% %s\n" \
    $sample_id "$expected" "$predicted" $confidence_pct "$result"
done

echo ""
accuracy=$(echo "scale=1; $correct * 100 / $total" | bc)
echo "Overall Accuracy: $correct/$total = ${accuracy}%"
echo ""

if (( $(echo "$accuracy >= 80" | bc -l) )); then
  echo "This is EXCELLENT for a wine quality classifier!"
elif (( $(echo "$accuracy >= 70" | bc -l) )); then
  echo "This is GOOD for a wine quality classifier!"
else
  echo "This is acceptable for a wine quality classifier."
fi
