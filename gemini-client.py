import socket
import ssl
import sys
from urllib.parse import urlparse, urlunparse
from urllib.parse import urljoin
from typing import List, Set, Dict, Tuple, Optional
import sys
import time
import webbrowser

def parse_mime(meta, response_code) -> Tuple[str, List[Tuple[str, str]]]:
  assert response_code[0] == "2"

  tokenized_meta = [token.strip() for token in meta.split(";")]
  tokenized_meta = [i for i in tokenized_meta if i]
  body_type, parameters = (tokenized_meta[0], tokenized_meta[1:])
  tokenized_params = [tuple(parameter.split("=")) for parameter in parameters]
  return body_type, tokenized_params



def decode_body(body, params) -> str:
  charset = "utf-8"
  for (attribute, value) in params:
    if attribute == "charset":
      charset = value.lower()
  body = body.decode(encoding=charset)
  return body


def get_response(conn, url) -> Tuple[str, str, Tuple[str, str]]:
  conn.write(url.encode())
  response = []
  data = conn.recv()
  while data:
    response.append(data)
    data = conn.recv(4096)

  response = b"".join(response)
  response = response.split(b"\r\n",maxsplit=1)
  header = response[0].decode()
  response_code = header[:2]
  meta = header[3:]
  if response_code[0] == "2":
    body_type, params = parse_mime(meta, response_code)
    body = decode_body(response[1], params)
  else:
    body_type = ""
    body = ("","")
  return response_code, meta, (body_type, body)








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
      try:
        links.append(link_chunks[1])
      except IndexError:
        links.append("about:blank")

  body = "\n".join(lines)
  return (links, body)



def response_code_properly_formatted(response_code) -> bool:
  return len(response_code) == 2 and is_int(response_code[0]) and is_int(response_code[1])

def do_connection(url, retries=0) -> List[str]:
  request = url + "\r\n"
  if retries > 5:
    print("TOO MANY REDIRECTS. ABORTING.")
    retries = 0
    return [], url
  print("CONNECTING TO " + url)

  scheme, netloc, path, params, query, fragment = urlparse(url, scheme="gemini")

  if scheme != "gemini":
    webbrowser.open_new(url)
    return ([], "")
  soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
  context.verify_mode = ssl.CERT_NONE
  context.check_hostname = False
  context.load_default_certs()
  conn = context.wrap_socket(soc, server_hostname=netloc)
  try:
    conn.connect((netloc, 1965))
    response_code, meta, (body_type, body) = get_response(conn, request)
    conn.close()
    print("RESPONSE CODE: " + response_code)
    print("META: " + meta)
    if not response_code_properly_formatted(response_code):
      print("BAD RESPONSE CODE")
      conn.close()
      return [], ""
    if response_code[0] == '1':
      print('HANDLING OF 1X RESPONSES NOT IMPLEMENTED YET')
      conn.close()
      return [], ""
    elif response_code[0] == '2':
      links, body = parse_links(body)
      print(body)
      retries = 0
    elif response_code[0] == '3':
      print("REDIRECTED TO " + meta)
      time.sleep(1)
      conn.close()
      new_url = get_new_link(meta, url)
      links, url = do_connection(new_url, retries=retries+1)
    elif response_code[0] == '4' or response_code[0] == '5':
      conn.close()
      return [], ""
    elif response_code[0] == '6':
      print("CLIENT CERTIFICATE REQUIRED")
      print("NOT YET IMPLEMENTED.")
      return [], ""
    else:
      print("BAD RESPONSE CODE")
      return [], ""



  finally:
    conn.close()
  return links, url

def is_absolute(url) -> bool:
  return bool(urlparse(url).netloc)

def is_int(str) -> bool:
  try:
    int(str)
    return True
  except ValueError:
    return False

def get_new_link(input_url, current_link) -> str:
  new_url = ""
  current_link_parsed = urlparse(current_link)
  input_url_parsed = urlparse(input_url)
  if current_link_parsed.scheme == "gemini":
    current_link_parsed = current_link_parsed._replace(scheme="")
  if input_url_parsed.scheme == "gemini":
    input_url_parsed =  input_url_parsed._replace(scheme="")
  current_link = urlunparse(current_link_parsed)
  input_url = urlunparse(input_url_parsed)

  new_url = urljoin(current_link, input_url)

  if urlparse(new_url).scheme == "":
    new_url = urlparse(new_url, scheme="gemini")
    new_url = urlunparse(new_url)

  return new_url


def print_repl_prompt() -> None:
  print(">>>", end=" ")

def client(url) -> None:
  print("Stellar Gemini Client")
  current_url = url
  while True:
    links, current_url = do_connection(current_url)
    print("List of links on this page:")
    for i in range(len(links)):
      print(f"{[i + 1]} -- ", end="")
      print(links[i])
    print_repl_prompt()
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

      print_repl_prompt()
    current_url = get_new_link(selected_link, current_url)

if len(sys.argv) > 1:
  url = sys.argv[1]
else:
  url = "gemini://gemini.circumlunar.space/"
client(url)













