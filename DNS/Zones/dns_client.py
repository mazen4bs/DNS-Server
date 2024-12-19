import socket

def client():
    # Connect to the server
    server_ip = '192.168.1.13i'
    server_port = 53535
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_ip, server_port))
    
    # Receive and send username for authentication
    print(client_socket.recv(1024).decode())  # Prompt for username
    username = input("Username: ")
    client_socket.sendall(username.encode())
    
    # Receive and send password for authentication
    print(client_socket.recv(1024).decode())  # Prompt for password
    password = input("Password: ")
    client_socket.sendall(password.encode())

    # Receive authentication response
    auth_response = client_socket.recv(1024).decode()
    print(auth_response)
    
    if "successful" in auth_response:  # Proceed if authentication is successful
        # Send a DNS query
        query = input("Enter DNS query: ")
        client_socket.sendall(query.encode())

        # Receive and display the resolved DNS response
        response = client_socket.recv(1024).decode()
        print(response)
    
    # Close the connection
    client_socket.close()

if __name__ == "__main__":
    client()
