import socket
import ssl
import sys
from urllib.parse import urlparse
from typing import List, Set, Dict, Tuple, Optional
import sys
import time

def get_header(conn, url) -> Tuple[str, str]:
  conn.write(url.encode())
  header = conn.recv(4096).decode()

  status = header[:2]
  space = header[2]
  meta = header[3:-2]

  return (status, meta)
  print(conn.recv().decode())

def parse_links(body) -> Tuple[List[str], str]:
  lines = body.split("\n")
  link_count = 0
  links = []
  for i in range(len(lines)):
    if lines[i][:2] == "=>":
      link_count += 1
      link_chunks = lines[i].replace("=>", f'[{link_count}]', 1)
      link_chunks = link_chunks.split(maxsplit=2)
      if len(link_chunks) == 3:
        lines[i] = link_chunks[0] + " " + link_chunks[2]
      else:
        lines[i] = " ".join(link_chunks)
      links.append(link_chunks[1])

  body = "\n".join(lines)
  return (links, body)

def do_connection(url) -> List[str]:
  request = url + "\r\n"
  print("CONNECTING TO " + url)

  if url[:9] == "gemini://":
    pruned_url = url[9:]
  else:
    pruned_url = url
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
    body = ""
    if header[0] == '2':
      if meta == "text/gemini":
        new_block = conn.recv().decode()
        while new_block:
          body += new_block
          new_block = conn.recv(4096).decode()
        links, body = parse_links(body)
        print(body)
    elif header[0] == '3':
      print("REDIRECTED TO " + meta)
      time.sleep(1)
      conn.close()
      links = do_connection(meta)
  finally:
    conn.close()
  return links

def is_absolute(url):
  return bool(urlparse(url).netloc)

def is_int(str):
  try:
    int(str)
    return True
  except ValueError:
    return False

def get_new_link(input_url, link):
  new_url = ""
  if link[:9] == "gemini://":
    link = link[9:]
  if is_absolute(input_url):
    new_url = input_url
  elif input_url == "..":
    new_url = link.rsplit('/', 1)[0]
  else:
    new_url = link + input_url
  if new_url[:9] != "gemini://":
    new_url = "gemini://" + new_url
  return new_url


def client(url):
  print("Stellar Gemini Client")
  current_url = url
  while True:
    links = do_connection(current_url)
    print("List of links on this page:")
    for i in range(len(links)):
      print(f"{[i + 1]} -- ", end="")
      print(links[i])
    print(">>>", end=" ")
    while True:
      user_input = input()
      if is_int(user_input):
        user_num = int(user_input)
        try:
          selected_link = links[user_num-1]
          break
        except IndexError:
          print("Bad link, please select a link in the list.")
      else:
        selected_link = user_input
        break

      print(">>>", end=" ")
    current_url = get_new_link(selected_link, current_url)
if len(sys.argv) > 1:
  url = sys.argv[1]
else:
  url = "gemini://gemini.circumlunar.space/"
client(url)













