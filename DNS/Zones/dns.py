import socket
import threading

# Global variable to store recent queries
recent_queries = []

def handle_client(conn, addr, recent_queries):
    """
    Handles client authentication, processes DNS queries, and sends realistic DNS responses.
    Allows the client to send multiple queries within the same session.

    Args:
        conn (socket.socket): The client connection.
        addr (tuple): The client's address (IP, port).
        recent_queries (list): A shared list to store recent queries.
    """
    print(f"[Server] Connection established with {addr}")
    try:
        # Step 1: Authentication
        conn.sendall(b"Enter username: ")
        username = conn.recv(1024).decode().strip()
        conn.sendall(b"Enter password: ")
        password = conn.recv(1024).decode().strip()

        # Validate credentials (use secure mechanisms in production)
        valid_credentials = {"admin": "password"}  # Replace with a secure store
        if username in valid_credentials and valid_credentials[username] == password:
            conn.sendall(b"Authentication successful. You may send your DNS query.\n")

            # Step 2: Receive and Validate DNS Query in a loop
            while True:
                conn.sendall(b"Enter DNS query: ")
                data = conn.recv(1024).decode().strip()

                if not data or len(data) > 255:  # Basic validation
                    conn.sendall(b"Invalid DNS query. Please try again.\n")
                    continue

                print(f"[Server] Received query: {data} from {addr}")
                recent_queries.append({"client": addr, "query": data})

                # Step 3: Realistic DNS Resolution
                try:
                    response = socket.gethostbyname(data)
                except socket.gaierror:
                    response = "Query could not be resolved."

                conn.sendall(f"Resolved {data} to {response}\n".encode())

                # Ask if the client wants to continue
                conn.sendall(b"Do you want to send another query? (yes/no): ")
                continue_query = conn.recv(1024).decode().strip().lower()
                if continue_query != "yes":
                    conn.sendall(b"Closing connection. Goodbye!\n")
                    break
        else:
            conn.sendall(b"Authentication failed. Invalid username or password.\n")
            print(f"[Server] Authentication failed for {addr}")

    except Exception as e:
        print(f"[Server] Error handling client {addr}: {e}")
    finally:
        conn.close()
        print(f"[Server] Connection with {addr} closed")


def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', 53535))
    server.listen(5)
    print("[Server] Server is listening on 0.0.0.0:53535")
    while True:
        conn, addr = server.accept()  # Accept new connections
        thread = threading.Thread(target=handle_client, args=(conn, addr, recent_queries))  # Pass recent_queries here
        thread.start()
        print(f"[Server] Active connections: {threading.active_count() - 1}")


def cli():
    global recent_queries
    while True:
        print("\nServer CLI:")
        print("1. View Active Connections")
        print("2. View Recent Queries")
        print("3. Stop Server")
        choice = input("Select an option: ")

        if choice == "1":
            print(f"[CLI] Active Connections: {threading.active_count() - 1}")
        elif choice == "2":
            print("[CLI] Recent Queries:")
            for query in recent_queries[-10:]:  # Show the last 10 queries
                print(f"Client {query['client']} queried: {query['query']}")
        elif choice == "3":
            print("[CLI] Shutting down server...")
            break
        else:
            print("[CLI] Invalid option. Try again.")

if __name__ == "__main__":
    # Run server and CLI in separate threads
    server_thread = threading.Thread(target=start_server)
    server_thread.daemon = True  # Ensure server thread stops with the main program
    server_thread.start()

    cli()  # Run CLI in the main thread

