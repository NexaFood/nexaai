#!/bin/bash
# Progress monitoring script for synthetic data generation

echo "======================================================================"
echo "📊 CADQUERY DATASET GENERATION PROGRESS"
echo "======================================================================"
echo ""

# Count generated examples
TOTAL=$(ls /home/ubuntu/nexaai/training/data/synthetic/synthetic_*.json 2>/dev/null | wc -l)
TARGET=10000
PROGRESS=$(echo "scale=1; $TOTAL / $TARGET * 100" | bc)

echo "Generated: $TOTAL / $TARGET examples ($PROGRESS%)"
echo ""

# Show progress bar
FILLED=$(echo "$PROGRESS / 2" | bc)
printf "["
for i in $(seq 1 50); do
    if [ $i -le $FILLED ]; then
        printf "="
    else
        printf " "
    fi
done
printf "]\n\n"

# Estimate time remaining
if [ $TOTAL -gt 0 ]; then
    # Assume ~2 seconds per example
    REMAINING=$((($TARGET - $TOTAL) * 2))
    HOURS=$(($REMAINING / 3600))
    MINUTES=$((($REMAINING % 3600) / 60))
    echo "Estimated time remaining: ${HOURS}h ${MINUTES}m"
fi

echo ""
echo "Latest examples:"
ls -lht /home/ubuntu/nexaai/training/data/synthetic/synthetic_*.json | head -5 | awk '{print "  " $9 " (" $5 ") - " $6 " " $7 " " $8}'

echo ""
echo "======================================================================"
