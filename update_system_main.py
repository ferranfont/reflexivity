"""
MAIN UPDATE SCRIPT
1. Update Stock Prices (Downloads fresh data for all symbols)
2. Regenerate Company Profiles (Refreshes HTML for all profiles in cache)
3. Regenerate Themes (Refreshes HTML for all theme pages)
"""
import subprocess
import sys
import time
from pathlib import Path

def run_script(script_relative_path):
    # Base dir is the script directory (project root)
    # Target scripts are in data_update/
    script_path = Path(__file__).parent / "data_update" / script_relative_path
    
    print(f"\n{'='*50}")
    print(f"🚀 STARTING: {script_relative_path}")
    print(f"{'='*50}")
    
    if not script_path.exists():
        print(f"❌ Error: Script not found at {script_path}")
        return False
        
    try:
        # Run script and wait for it to finish
        result = subprocess.run([sys.executable, str(script_path)], check=True)
        print(f"\n✅ FINISHED: {script_relative_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ FAILED: {script_relative_path} (Exit Code: {e.returncode})")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False

def main():
    start_time = time.time()
    
    print(f"\n{'='*60}")
    print("🔄 SYSTEM UPDATE STARTED")
    print(f"{'='*60}")
    print("This process will update market data and regenerate the website.")
    print("It may take several hours depending on the number of stocks.")
    
    # 1. Update Market Data
    print("\n[STEP 1/3] Updating Market Data...")
    if not run_script("download_and_update_data_all_stocks.py"):
        print("⚠️ Market data update failed. Continuing to regeneration might show old data.")
        # We continue anyway because maybe we just want to regenerate HTMLs using existing DB data
    
    # 2. Regenerate Profiles
    print("\n[STEP 2/3] Regenerating Company Profiles...")
    run_script("regenerate_all_profiles.py")
    
    # 3. Regenerate Themes
    print("\n[STEP 3/3] Regenerating Theme Pages...")
    run_script("regenerate_all_themes.py")
    
    elapsed = time.time() - start_time
    hours = int(elapsed // 3600)
    minutes = int((elapsed % 3600) // 60)
    
    print(f"\n{'='*60}")
    print(f"✨ UPDATE COMPLETE")
    print(f"⏱️ Total Time: {hours}h {minutes}m")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
