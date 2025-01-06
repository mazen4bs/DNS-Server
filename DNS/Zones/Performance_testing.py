import socket
import time
from threading import Thread

SERVER_IP = "127.0.0.1"  # Replace with your server's IP
SERVER_PORT = 53535
NUM_THREADS = 10  # Number of concurrent clients
NUM_QUERIES = 100  # Number of queries per client

def send_queries(thread_id):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.connect((SERVER_IP, SERVER_PORT))

        # Always respond with "yes" to authentication prompts
        client.recv(1024)  # Skip the "Enter username" prompt
        client.sendall(b"a\n")  # Send username
        client.recv(1024)  # Skip the "Enter password" prompt
        client.sendall(b"p\n")  # Send password
        client.recv(1024)  # Skip the authentication success message
        client.sendall(b"yes\n")  # Always respond with "yes"

        for _ in range(NUM_QUERIES):
            query = "google.com,A"  # Example query
            start_time = time.time()  # Start time for latency measurement
            client.sendall(query.encode())  # Send query to server
            response = client.recv(1024).decode()  # Receive the response
            end_time = time.time()  # End time for latency measurement

            # Print the query, response, and latency
            print(f"[Thread {thread_id}] Query: {query}, Response: {response}, Latency: {end_time - start_time:.4f}s")

# Start multiple threads to simulate concurrent clients
threads = []
for i in range(NUM_THREADS):
    thread = Thread(target=send_queries, args=(i,))
    threads.append(thread)
    thread.start()

# Wait for all threads to complete
for thread in threads:
    thread.join()
