#!/bin/bash
# Author: sathiyendren
# Email: sathiyendren@gmail.com
# Created: 2026-07-01
# Description: Create new files with automatic author attribution
# Project: Algo Trading System

if [ $# -eq 0 ]; then
    echo "Usage: ./create_file.sh <filename> [description]"
    echo "Example: ./create_file.sh new_strategy.py 'RSI trading strategy'"
    exit 1
fi

FILENAME=$1
DESCRIPTION=${2:-"Algo Trading System File"}
CURRENT_DATE=$(date '+%Y-%m-%d %H:%M:%S')

# Check if file already exists
if [ -f "$FILENAME" ]; then
    echo "Error: File '$FILENAME' already exists"
    exit 1
fi

# Create file with author header
cat > $FILENAME << FILEEOF
# Author: sathiyendren
# Email: sathiyendren@gmail.com
# Created: $CURRENT_DATE
# Description: $DESCRIPTION
# Project: Algo Trading System

FILEEOF

# Add file-specific content based on extension
case "${FILENAME##*.}" in
    "py")
        echo "import logging" >> $FILENAME
        echo "" >> $FILENAME
        echo "logger = logging.getLogger(__name__)" >> $FILENAME
        echo "" >> $FILENAME
        echo "# TODO: Add your implementation here" >> $FILENAME
        ;;
    "sh")
        echo "#!/bin/bash" >> $FILENAME
        echo "set -euo pipefail" >> $FILENAME
        echo "" >> $FILENAME
        echo "# TODO: Add your script logic here" >> $FILENAME
        chmod +x $FILENAME
        ;;
    "js")
        echo "// TODO: Add your JavaScript code here" >> $FILENAME
        ;;
esac

echo "Created file: $FILENAME"
echo "Contents:"
cat $FILENAME

# Add to git if in a git repository
if [ -d .git ]; then
    git add $FILENAME
    echo "File added to git: $FILENAME"
fi
