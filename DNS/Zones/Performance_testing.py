import socket
import time
from threading import Thread
import random

SERVER_IP = "192.168.1.22"
SERVER_PORT = 53535
NUM_THREADS = 10
NUM_QUERIES = 50

# Performance metrics
response_times = []
errors = 0
queries_sent = 0

# List of websites for generating random queries
websites = [
    "google.com", "yahoo.com", "bing.com", "youtube.com",
    "twitter.com", "linkedin.com", "amazon.com", "wikipedia.org",
    "reddit.com", "netflix.com"
]

def send_queries(thread_id):
    global response_times, errors, queries_sent
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        try:
            client.connect((SERVER_IP, SERVER_PORT))
            client.recv(1024)  # Skip authentication prompt
            client.sendall(b"a\n")
            client.recv(1024)
            client.sendall(b"p\n")
            client.recv(1024)

            for _ in range(NUM_QUERIES):
                # Respond "yes" before sending each query
                client.recv(1024)
                client.sendall(b"yes\n")

                # Generate a random query
                domain = random.choice(websites)
                query = f"{domain},A"
                start_time = time.time()
                client.sendall(query.encode())
                response = client.recv(1024).decode()
                end_time = time.time()

                # Validate response
                if "Invalid" in response:
                    errors += 1
                else:
                    response_times.append(end_time - start_time)
                    queries_sent += 1

                print(f"[Thread {thread_id}] Query: {query}, Response: {response}, Latency: {end_time - start_time:.4f}s")
        except Exception as e:
            print(f"[Thread {thread_id}] Error: {e}")
            errors += NUM_QUERIES  # Assume all queries failed for this thread if there's an exception

# Start multiple threads
threads = []
start_time = time.time()
for i in range(NUM_THREADS):
    thread = Thread(target=send_queries, args=(i,))
    threads.append(thread)
    thread.start()

for thread in threads:
    thread.join()
end_time = time.time()

# Results
total_duration = end_time - start_time
avg_latency = sum(response_times) / len(response_times) if response_times else 0
error_rate = (errors / (NUM_THREADS * NUM_QUERIES)) * 100

print("\n=== Performance Testing Results ===")
print(f"Total Queries Sent: {queries_sent}")
print(f"Total Errors: {errors}")
print(f"Error Rate: {error_rate:.2f}%")
print(f"Average Latency: {avg_latency:.4f}s")
print(f"Total Test Duration: {total_duration:.2f}s")
print(f"Throughput: {queries_sent / total_duration:.2f} queries/second")
