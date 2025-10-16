"""
RQ worker for background job processing.
"""
import os
import redis
from rq import Worker, Queue, Connection
from dotenv import load_dotenv

# Fix macOS fork() issue
os.environ['OBJC_DISABLE_INITIALIZE_FORK_SAFETY'] = 'YES'

# Load environment variables
load_dotenv()

from .config import REDIS_URL

# Configure Redis connection
conn = redis.from_url(REDIS_URL)

# Define the queues
route_queue = Queue('route_generation', connection=conn)

# Create worker instance with an explicit connection to avoid None-type issues
worker = Worker([route_queue], connection=conn)

if __name__ == '__main__':
    with Connection(conn):
        # Use simple worker without multiprocessing to avoid macOS fork issues
        worker.work(with_scheduler=False)