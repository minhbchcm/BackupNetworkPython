import csv
import paramiko
import time

def get_cisco_config(hostname, username, password, enable_password):
    try:
        # Connect to the Cisco device using SSH
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(hostname, username=username, password=password)

        # Create a shell session
        shell = ssh_client.invoke_shell()

        # Send enable command
        shell.send("enable\n")
        time.sleep(1)
        shell.send(enable_password + "\n")

        # Send command to retrieve running configuration
        shell.send("ter len 0\n")  # Setting up terminal length as 0
        shell.send("show running-config\n")

        # Wait for the command to execute
        time.sleep(1)

        # Read the output of the command
        output = ""
        while shell.recv_ready():
            output += shell.recv(1024).decode()

        # Close SSH connection
        ssh_client.close()

        return output

    except Exception as e:
        print(f"Error retrieving configuration from {hostname}: {e}")
        return None

def upload_to_sftp(server, username, password, local_path, remote_path):
    try:
        # Establish an SFTP connection to the server
        transport = paramiko.Transport((server, 22))
        transport.connect(username=username, password=password)
        sftp = paramiko.SFTPClient.from_transport(transport)

        # Upload the file
        sftp.put(local_path, remote_path)

        # Close SFTP connection
        sftp.close()

        print(f"Configuration uploaded to {server} at {remote_path}")

    except Exception as e:
        print(f"Error uploading configuration to {server}: {e}")

if __name__ == "__main__":
    # Read router information from CSV file
    routers = []
    with open('router_info.csv', 'r') as csvfile:
        csv_reader = csv.reader(csvfile)
        next(csv_reader)  # Skip the header row
        for row in csv_reader:
            routers.append({
                "hostname": row[0],
                "username": row[1],
                "password": row[2],
                "enable_password": row[3]
            })

    # SFTP server credentials
    sftp_server = "172.16.0.101"  # IP address of the SFTP server
    sftp_username = "cisco"  # Username for accessing the SFTP server
    sftp_password = "cisco"  # Password for accessing the SFTP server

    for router in routers:
        config = get_cisco_config(router["hostname"], router["username"], router["password"], router["enable_password"])
        if config:
            # Save running configuration to a local file
            local_path = f"running_config_{router['hostname']}.txt"
            with open(local_path, "w") as f:
                f.write(config)

            # Upload the running configuration to SFTP server
            upload_to_sftp(sftp_server, sftp_username, sftp_password, local_path, f"/running_config_{router['hostname']}.txt")