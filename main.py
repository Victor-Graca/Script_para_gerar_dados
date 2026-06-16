import subprocess
import time
import sys

def run_script(script_name):
    """Executes a Python script as an isolated subprocess."""
    print(f"\n{'='*55}")
    print(f"STARTING PHASE: {script_name}")
    print(f"{'='*55}")
    
    start_time = time.time()
    
    try:
        # sys.executable ensures it uses your current Python environment
        # (prevents "ModuleNotFoundError" if you are using a virtual environment)
        subprocess.run([sys.executable, script_name], check=True)
        
    except subprocess.CalledProcessError:
        print(f"\nFATAL ERROR: Pipeline halted. {script_name} failed.")
        print("Check the console output above for the specific Python traceback.")
        sys.exit(1) # Stop the entire pipeline
        
    elapsed = time.time() - start_time
    print(f"\nCOMPLETED {script_name} in {elapsed:.2f} seconds.")

def main():
    print("Initializing Eventosbr Data Generation Pipeline...")
    total_start_time = time.time()
    
    # The strict chronological order of your dependency graph
    pipeline = [
        '01_generate_users.py',
        '02_generate_events.py',
        '03_generate_transactions.py',
        '04_generate_operations.py'
    ]
    
    # Execute the pipeline
    for script in pipeline:
        run_script(script)
        
    total_elapsed = time.time() - total_start_time
    
    print(f"\n{'*'*55}")
    print(f"PIPELINE SUCCESS! All CSVs generated in {total_elapsed:.2f} seconds.")
    print(f"{'*'*55}\n")

if __name__ == "__main__":
    main()