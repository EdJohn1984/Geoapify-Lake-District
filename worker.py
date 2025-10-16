"""
Main worker entry point.
"""
import sys
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

# Import and run the worker
from backend.worker import worker, route_queue

if __name__ == '__main__':
    with route_queue.connection:
        worker.work(with_scheduler=False)
