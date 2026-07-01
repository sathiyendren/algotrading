#!/bin/bash

echo "📊 Data Verification Status Report"
echo "================================="

# Check if today's verification has run
TODAY=$(date +%Y-%m-%d)
LOG_FILE="/opt/algotrading/logs/daily_verification.log"

if [ -f "$LOG_FILE" ]; then
    echo "📅 Today's verification status:"
    if grep -q "$TODAY" "$LOG_FILE"; then
        echo "✅ Verification completed for $TODAY"
        echo "📝 Latest entries:"
        tail -20 "$LOG_FILE" | grep -E "(VERIFICATION|PARTICIPANT|FII/DII|PCR|Snapshots)"
    else
        echo "⏳ Verification not yet run for $TODAY (scheduled for 4:05 PM)"
    fi
    
    echo ""
    echo "📈 Recent verification history:"
    tail -50 "$LOG_FILE" | grep -E "SCHEDULED DATA VERIFICATION|VERIFICATION COMPLETED|VERIFICATION FAILED" | tail -7
else
    echo "❌ No verification log file found"
fi

echo ""
echo "⏰ Next scheduled run: Today at 4:05 PM"
echo "📂 Log location: $LOG_FILE"
