import socket
import threading
import dns.resolver

# Global variable to store recent queries
recent_queries = []

def resolve_dns(query, record_type):
    try:
        if record_type == "A":
            # Resolving A record (IPv4 address)
            result = dns.resolver.resolve(query, 'A')
            return [ip.to_text() for ip in result]
        elif record_type == "AAAA":
            # Resolving AAAA record (IPv6 address)
            result = dns.resolver.resolve(query, 'AAAA')
            return [ip.to_text() for ip in result]
        elif record_type == "MX":
            # Resolving MX record (Mail Exchange)
            answers = dns.resolver.resolve(query, 'MX')
            return [str(rdata.exchange) for rdata in answers]
        elif record_type == "CNAME":
            # Resolving CNAME record (Canonical Name)
            answers = dns.resolver.resolve(query, 'CNAME')
            return [str(rdata.target) for rdata in answers]
        elif record_type == "NS":
            # Resolving NS record (Name Server)
            answers = dns.resolver.resolve(query, 'NS')
            return [str(rdata.target) for rdata in answers]
        else:
            return None  
    except Exception as e:
        return None  


def handle_client(conn, addr, recent_queries):
    print(f"[Server] Connection established with {addr}")
    try:
        # Step 1: Authentication
        conn.sendall(b"Enter username: ")
        username = conn.recv(1024).decode().strip()
        conn.sendall(b"Enter password: ")
        password = conn.recv(1024).decode().strip()

        valid_credentials = {"a": "p"}
        if username in valid_credentials and valid_credentials[username] == password:
            conn.sendall(b"Authentication successful. You may send your DNS query.\n")

            # Step 2: Receive and Validate DNS Query in a loop
            while True:
                conn.sendall(b"Enter DNS query (format: domain,record_type): ")
                data = conn.recv(1024).decode().strip()

                # Validate input format
                if not data or "," not in data:
                    conn.sendall(b"Invalid query format. Use: domain,record_type\n")
                    continue

                # Extract domain and record type
                query, record_type = map(str.strip, data.split(",", 1))
                if not query or not record_type:
                    conn.sendall(b"Invalid query format. Use: domain,record_type\n")
                    continue

                print(f"[Server] Received query: {query} ({record_type}) from {addr}")
                recent_queries.append({"client": addr, "query": data})

                # Resolve the DNS query
                response = resolve_dns(query, record_type.upper())
                if response:
                    conn.sendall(f"Resolved {query} ({record_type}) to {response}\n".encode())
                else:
                    conn.sendall(b"Query could not be resolved or unsupported record type.\n")

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
    server.bind(("0.0.0.0", 53535))
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
    server_thread.daemon = True  
    server_thread.start()

    cli()  