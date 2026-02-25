import subprocess
import os
import sys
import threading
import argparse
import time
import signal
from pathlib import Path

def stream_output(process, prefix):
    """Prefixed output streamer to distinguish between agents in the console."""
    for line in iter(process.stdout.readline, b''):
        try:
            # Try to decode as utf-8 but be resilient to encoding mismatches
            decoded = line.decode('utf-8', errors='replace').strip()
            sys.stdout.write(f"[{prefix}] {decoded}\n")
        except Exception:
            # Fallback for extreme cases
            sys.stdout.write(f"[{prefix}] <output unreadable>\n")
    process.stdout.close()

def main():
    parser = argparse.ArgumentParser(description="AutoYield Multi-Agent Manager")
    parser.add_argument("--count", type=int, default=1, help="Number of agents to run (default: 1)")
    parser.add_argument("command", choices=["status", "run", "fund"], help="Command to execute for each agent")
    parser.add_argument("--strategy", default="random", help="Strategy for 'run' command")
    parser.add_argument("--rounds", type=int, default=1, help="Rounds for 'run' command")
    parser.add_argument("--interval", type=int, default=10, help="Interval for 'run' command")
    
    # Parse known args, everything else (like --vault) goes to the agents
    args, unknown = parser.parse_known_args()

    processes = []
    
    print(f"--- Launching {args.count} autonomous agents ---")

    try:
        for i in range(1, args.count + 1):
            agent_id = f"AGENT_{i}"
            wallet_file = f"agent_{i}.key"
            
            # Setup environment for this specific agent
            env = os.environ.copy()
            env["AUTOYIELD_WALLET_FILE"] = wallet_file
            
            # Build the command
            cmd = [sys.executable, "agent.py", args.command]
            if args.command == "run":
                cmd.extend(["--strategy", args.strategy, "--rounds", str(args.rounds), "--interval", str(args.interval)])
                if unknown:
                    cmd.extend(unknown)

            # Spawn the process
            p = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=env,
                bufsize=1
            )
            processes.append(p)
            
            # Start output thread
            thread = threading.Thread(target=stream_output, args=(p, agent_id), daemon=True)
            thread.start()
            
            # Tiny delay to prevent race conditions on Devnet/OS
            time.sleep(0.5)

        # Wait for all processes to complete
        for p in processes:
            p.wait()

    except KeyboardInterrupt:
        print("\n🛑 Shutdown signal received. Terminating all agents...")
        for p in processes:
            p.terminate()
        print("All agents stopped.")

if __name__ == "__main__":
    main()
