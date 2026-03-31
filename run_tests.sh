#!/bin/bash

set -e  # exit on error

PUBLISH=false

# Parse args
for arg in "$@"
do
    if [ "$arg" == "--publish" ]; then
        PUBLISH=true
    fi
done

# Paths
RESULTS_DIR="tests/allure_results"
REPORTS_BASE_DIR="tests/reports"
DATE=$(date +"%Y-%m-%d")
REPORT_DIR="$REPORTS_BASE_DIR/report_$DATE"

echo "🧪 Running pytest..."
python -m pytest --alluredir=$RESULTS_DIR

echo "📊 Generating Allure report..."
allure generate $RESULTS_DIR -o $REPORT_DIR --clean --single-file

echo "✅ Report generated at: $REPORT_DIR"

if [ "$PUBLISH" = true ]; then
    echo "🚀 Publishing to GitHub..."

    # Add report
    git add $REPORT_DIR

    # Commit
    git commit -m "Add Allure report: $DATE" || echo "No changes to commit"

    # Push
    git push

    echo "✅ Report pushed to GitHub"
fi