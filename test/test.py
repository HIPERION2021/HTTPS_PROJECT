import subprocess
import time
import json
import csv

SERVER_URL = "https://192.16.14.1:5000"
PAYLOAD_FILE = "payloads_modified_keys.txt"
RESULTS_CSV = "results.csv"

# Load payloads
with open(PAYLOAD_FILE, "r") as f:
    payloads = [json.loads(line.strip()) for line in f if line.strip()]

# Prepare CSV
with open(RESULTS_CSV, mode="w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Run", "ElapsedTime(s)", "ModifiedKey"])

    for i, payload in enumerate(payloads, start=1):
        # Write temp payload file
        with open("temp_payload.json", "w") as temp:
            json.dump(payload, temp)

        start = time.time()
        try:
            subprocess.run(
                ["python3", "client.py", "--server", SERVER_URL, "temp_payload.json"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except subprocess.CalledProcessError:
            print(f"Run {i} failed.")

        elapsed = time.time() - start

        # Find which key is modified (compared to original)
        original_keys = {"FirstName", "LastName", "Age", "hight", "Address", "Comments"}
        modified_key = list(set(payload.keys()) - original_keys)
        writer.writerow([i, round(elapsed, 4), modified_key[0] if modified_key else "none"])

print("Done! Results saved to", RESULTS_CSV)
