import socket
import ssl
import sys

def get_header(conn, url):
  conn.write(url.encode())
  header = conn.recv(4096).decode()

  status = header[:2]
  space = header[2]
  meta = header[3:-2]

  return (status, meta)
  print(conn.recv().decode())

def do_connection(url):
  request = url + "\r\n"

  if url[:9] == "gemini://":
    pruned_url = url[9:]
  hostname = pruned_url.split("/", 1)[0]
  soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
  context.verify_mode = ssl.CERT_NONE
  context.check_hostname = False
  context.load_default_certs()
  conn = context.wrap_socket(soc, server_hostname=hostname)
  try:
    conn.connect((hostname, 1965))
    (header, meta) = get_header(conn, request)
    print("HEADER: " + header)
    print("META: " + meta)
    if header[0] == '2':
      if meta == "text/gemini":
        body = conn.recv().decode()
        while body:
          print(body)
          body = conn.recv().decode()
  finally:
    conn.close()

def client(url):
  print("Stellar Gemini Client")
  do_connection(url)

if len(sys.argv) > 1:
  url = sys.argv[1]
else:
  url = "gemini://gemini.circumlunar.space/"
client(url)













