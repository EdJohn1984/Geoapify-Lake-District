import os
import redis
from rq import Worker, Queue, Connection
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Redis connection without SSL
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
conn = redis.from_url(redis_url, ssl_cert_reqs=None)

# Define the queues
route_queue = Queue('route_generation', connection=conn)

if __name__ == '__main__':
    with Connection(conn):
        worker = Worker([route_queue])
        worker.work() 