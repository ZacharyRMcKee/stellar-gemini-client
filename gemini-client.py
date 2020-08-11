import socket
import ssl
import sys
from urllib.parse import urlparse
from urllib.parse import urljoin
from typing import List, Set, Dict, Tuple, Optional
import sys
import time
import webbrowser

from pathlib import Path



def get_response(conn, url) -> Tuple[str, str, str]:
  conn.write(url.encode())
  response = ""
  data = conn.recv().decode()
  while data:
    response += data
    data = conn.recv(4096).decode()
  response = response.split("\r\n",maxsplit=1)
  header = response[0]
  body = response[1]
  response_code = header[:2]
  meta = header[3:]
  return response_code, meta, body

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

  scheme, netloc, path, params, query, fragment = urlparse(url, scheme="gemini")

  if scheme != "gemini":
    webbrowser.open_new(url)
    return []
  soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
  context.verify_mode = ssl.CERT_NONE
  context.check_hostname = False
  context.load_default_certs()
  conn = context.wrap_socket(soc, server_hostname=netloc)
  try:
    conn.connect((netloc, 1965))
    response_code, meta, body = get_response(conn, request)
    conn.close()
    print("RESPONSE CODE: " + response_code)
    print("META: " + meta)
    if response_code[0] == '2':
      if meta == "text/gemini":

        links, body = parse_links(body)
        print(body)
    elif response_code[0] == '3':
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

def get_new_link(input_url, current_link):
  new_url = ""

  new_url = urljoin(current_link, input_url)

  if is_absolute(input_url):
    new_url = input_url
  else:
    current_link_parsed = urlparse(current_link)

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













