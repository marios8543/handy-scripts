import socket
from os import getenv
from datetime import datetime
import pymysql


class LogItem:
    def __init__(self, line):
        self.ip = line.split(" ")[0]
        self.timestamp = datetime.strptime(line.split("[")[1].split("]")[
                                           0].split("+")[0].strip(), "%d/%b/%Y:%H:%M:%S")
        req = line.split('"')[1].split(' ')
        self.method = req[0]
        self.path = req[1]
        self.http = req[2]
        self.status = int(line.split('"')[2].split(' ')[1])


print("Starting log server")
db_conn = pymysql.connect(host=getenv("db_host"), user=getenv(
    "db_user"), password=getenv("db_pass"), db=getenv("db_db"), autocommit=True)
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((getenv("tcp_ip"), int(getenv("tcp_port"))))
s.listen(True)

with db_conn.cursor() as db:
    db.execute("""
        CREATE TABLE IF NOT EXISTS `caddy_logs` (
            `ip` varchar(255) DEFAULT NULL,
            `timestamp` datetime DEFAULT NULL,
            `path` varchar(255) DEFAULT NULL,
            `method` varchar(255) DEFAULT NULL,
            `http` varchar(255) DEFAULT NULL,
            `status` int(11) DEFAULT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

while True:
    conn, addr = s.accept()
    print("Caddy connected from {}".format(addr))
    while True:
        data = conn.recv(4096)
        if not data:
            break
        data = data.decode("utf-8").split("]:")[1].strip()
        itm = LogItem(data)
        while True:
            try:
                with db_conn.cursor() as db:
                    db.execute("INSERT INTO `caddy_logs` (`ip`, `timestamp`, `path`, `method`, `http`, `status`) VALUES (%s, %s, %s, %s, %s, %s)",
                               (itm.ip, itm.timestamp, itm.path, itm.method, itm.http, itm.status,))
                    break
            except Exception:
                db_conn = pymysql.connect(host=getenv("db_host"), user=getenv(
                    "db_user"), password=getenv("db_pass"), db=getenv("db_db"), autocommit=True)
                continue

    conn.close()
