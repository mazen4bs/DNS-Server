import socket
import threading
import dns.resolver
import time

# Global variables
recent_queries = []
cache = {}  # Cache to store resolved queries
recent_queries_lock = threading.Lock()
# TTL (Time to Live) for cache entries (in seconds)
CACHE_TTL = 300

DNS_RESPONSE_CODES = {
    0: "NOERROR: Query successful.",
    1: "FORMERR: Query format error.",
    2: "SERVFAIL: Server failure.",
    3: "NXDOMAIN: Domain name does not exist.",
    4: "NOTIMP: Operation not implemented.",
    5: "REFUSED: Query refused.",
    8: "NXRRSET: RRSet does not exist.",
    9: "NOTAUTH: Server is not authoritative for the domain.",
}


def resolve_dns(query, record_type, is_recursive=True): # is_recursive=True means that the query is recursive if it is not recursive then it is iterative 
    """
    Resolves a DNS query and returns the response or error code.
    - is_recursive: True for recursive queries, False for iterative queries.
    """
    try:
        if not query or not record_type:
            return None, 1  # FORMERR: Invalid query format

        if is_recursive:
            # Perform recursive resolution by querying upstream servers
            if record_type == "A":
                result = dns.resolver.resolve(query, 'A')
                return [ip.to_text() for ip in result], 0  # NOERROR
            elif record_type == "AAAA":
                result = dns.resolver.resolve(query, 'AAAA')
                return [ip.to_text() for ip in result], 0  # NOERROR
            elif record_type == "MX":
                answers = dns.resolver.resolve(query, 'MX')
                return [str(rdata.exchange) for rdata in answers], 0  # NOERROR
            elif record_type == "CNAME":
                answers = dns.resolver.resolve(query, 'CNAME')
                return [str(rdata.target) for rdata in answers], 0  # NOERROR
            elif record_type == "NS":
                answers = dns.resolver.resolve(query, 'NS')
                return [str(rdata.target) for rdata in answers], 0  # NOERROR
            else:
                return None, 4  # NOTIMP: Query type not supported
        else:
            # Perform iterative resolution by returning referral to another nameserver
            if record_type == "NS":
                # Query NS records to return a referral to another nameserver
                answers = dns.resolver.resolve(query, 'NS')
                return [str(rdata.target) for rdata in answers], 0  # NOERROR
            else:
                return None, 4  # NOTIMP for non-NS iterative queries

    except dns.resolver.NXDOMAIN:
        return None, 3  # NXDOMAIN: Domain does not exist
    except dns.resolver.NoAnswer:
        return None, 8  # NXRRSET: RRSet does not exist
    except dns.resolver.NoNameservers:
        return None, 2  # SERVFAIL: No available name servers
    except Exception:
        return None, 5  # REFUSED: Query refused due to other reasons




def cache_query(query, record_type, response):
    """
    Caches the resolved query result with a TTL.
    """
    expiry = time.time() + CACHE_TTL
    cache[(query, record_type)] = {"response": response, "expiry": expiry}


def get_cached_query(query, record_type):
    """
    Retrieves a cached query result if it exists and is not expired.
    """
    key = (query, record_type)
    if key in cache:
        entry = cache[key]
        if time.time() < entry["expiry"]:  # Check if the cache entry is still valid
            return entry["response"]
        else:
            del cache[key]  # Remove expired entry
    return None


def handle_client(conn, addr, recent_queries):
    print(f"[Server] Connection established with {addr}")
    try:
        while True:  # Loop for authentication until success
            # Authentication Step
            conn.sendall(b"Enter username: ")
            username = conn.recv(1024).decode().strip()
            conn.sendall(b"Enter password: ")
            password = conn.recv(1024).decode().strip()

            valid_credentials = {"a": "p"}
            if username in valid_credentials and valid_credentials[username] == password:
                conn.sendall(b"Authentication successful. You may send your DNS query.\n")
                break  # Exit the loop once authenticated
            else:
                conn.sendall(b"Authentication failed. Invalid username or password. Please try again.\n")
                print(f"[Server] Authentication failed for {addr}")

        # Step 2: Receive and Validate DNS Query in a loop
        while True:
            conn.sendall(b"Enter DNS query (format: domain,record_type): ")
            data = conn.recv(1024).decode().strip()

            if not data or "," not in data:
                conn.sendall(b"Invalid query format. Use: domain,record_type\n")
                continue

            # Extract domain and record type
            query, record_type = map(str.strip, data.split(",", 1))
            if not query or not record_type:
                conn.sendall(b"Invalid query format. Use: domain,record_type\n")
                continue

            print(f"[Server] Received query: {query} ({record_type}) from {addr}")

            # Locking the recent_queries list while adding a new query
            with recent_queries_lock:
                recent_queries.append({"client": addr, "query": data})

            # Check if the query is in the cache first
            cached_response = get_cached_query(query, record_type)
            if cached_response:
                conn.sendall(f"Resolved from cache: {query} ({record_type}) to {cached_response}\n".encode())
            else:
                # Resolve the DNS query if it's not cached
                response, rcode = resolve_dns(query, record_type.upper())
                if rcode == 0:  # NOERROR
                    cache_query(query, record_type.upper(), response)
                    conn.sendall(f"Resolved {query} ({record_type}) to {response}\n".encode())
                else:
                    conn.sendall(f"Error: {DNS_RESPONSE_CODES.get(rcode, 'Unknown error')}\n".encode())

            # Ask if the client wants to continue
            while True:  # Loop until valid input is received
                conn.sendall(b"Do you want to send another query? (yes/no): ")
                continue_query = conn.recv(1024).decode().strip().lower()

                if continue_query in ["yes", "no"]:
                    break  # Exit the loop if input is valid
                else:
                    conn.sendall(b"Invalid input. Please enter 'yes' or 'no'.\n")
            
            if continue_query == "no":
                conn.sendall(b"Closing connection. Goodbye!\n")
                break

    except Exception as e:
        print(f"[Server] Error handling client {addr}: {e}")
    finally:
        conn.close()
        print(f"[Server] Connection with {addr} closed")





def start_tcp_server():
    """
    Starts the TCP server to handle DNS queries over TCP.
    """
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", 53535))
    server.listen(5)
    print("[Server] TCP server listening on 0.0.0.0:53535")
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr, recent_queries))
        thread.start()
        print(f"[Server] Active connections: {threading.active_count() - 1}")


def start_udp_server():
    """
    Starts the UDP server to handle DNS queries over UDP.
    """
    udp_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_server.bind(("0.0.0.0", 53535))
    print("[Server] UDP server listening on 0.0.0.0:53535")
    while True:
        data, addr = udp_server.recvfrom(512)  # DNS responses typically fit within 512 bytes for UDP
        thread = threading.Thread(target=handle_udp_query, args=(data, addr, udp_server))
        thread.start()


def handle_udp_query(data, addr, udp_server):
    """
    Handles DNS queries received over UDP.
    """
    try:
        # Decode and process the query
        query_data = data.decode().strip()
        if "," not in query_data:
            udp_server.sendto(b"Invalid query format. Use: domain,record_type", addr)
            return

        query, record_type = map(str.strip, query_data.split(",", 1))
        print(f"[UDP Server] Received query: {query} ({record_type}) from {addr}")

        # Check the cache
        cached_response = get_cached_query(query, record_type)
        if cached_response:
            udp_server.sendto(f"Resolved from cache: {query} ({record_type}) to {cached_response}\n".encode(), addr)
        else:
            # Resolve the DNS query
            response, rcode = resolve_dns(query, record_type.upper())
            if rcode == 0:  # NOERROR
                cache_query(query, record_type.upper(), response)
                udp_server.sendto(f"Resolved {query} ({record_type}) to {response}\n".encode(), addr)
            else:
                udp_server.sendto(f"Error: {DNS_RESPONSE_CODES.get(rcode, 'Unknown error')}\n".encode(), addr)
    except Exception as e:
        print(f"[UDP Server] Error handling client {addr}: {e}")


def cli():
    global recent_queries
    while True:
        print("\nServer CLI:")
        print("1. View Active Connections")
        print("2. View Recent Queries")
        print("3. View Cache Status")
        print("4. View Protocol Usage")
        print("5. Stop Server")
        choice = input("Select an option: ")

        if choice == "1":
            print(f"[CLI] Active Connections: {threading.active_count() - 1}")
        elif choice == "2":
            print("[CLI] Recent Queries:")
            for query in recent_queries[-10:]:
                print(f"Client {query['client']} queried: {query['query']}")
        elif choice == "3":
            print("[CLI] Cache Status:")
            for key, value in cache.items():
                print(f"Query: {key}, Response: {value['response']}, Expires In: {value['expiry'] - time.time()} seconds")
        elif choice == "4":
            print("[CLI] Protocol Usage: [Placeholder for protocol stats]")
        elif choice == "5":
            print("[CLI] Shutting down server...")
            break
        else:
            print("[CLI] Invalid option. Try again.")


if __name__ == "__main__":
    # Start TCP and UDP servers in separate threads
    tcp_thread = threading.Thread(target=start_tcp_server)
    tcp_thread.daemon = True
    tcp_thread.start()

    udp_thread = threading.Thread(target=start_udp_server)
    udp_thread.daemon = True
    udp_thread.start()

    # Start CLI in the main thread
    cli()
