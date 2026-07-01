from datetime import date, datetime
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from verify_data import verify_today

def main():
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n{'='*80}")
    print(f"SCHEDULED DATA VERIFICATION - {timestamp}")
    print(f"{'='*80}")
    
    try:
        verify_today()
        
        # Log completion
        print(f"\n✅ VERIFICATION COMPLETED - {timestamp}")
        print(f"📝 Log saved to: /opt/algotrading/logs/daily_verification.log")
        
    except Exception as e:
        print(f"\n❌ VERIFICATION FAILED - {timestamp}")
        print(f"Error: {str(e)}")
        sys.exit(1)
    
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()
