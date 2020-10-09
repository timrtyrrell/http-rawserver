#!/usr/bin/env python3

import socket
import select
import sys

from file_reader import FileReader

class Jewel:

    def __init__(self, port, file_path, file_reader):
        self.file_path = file_path
        self.file_reader = file_reader

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.setblocking(0)
        s.bind(('0.0.0.0', port))

        s.listen(5)

        # I read through https://pymotw.com/2/select/ to get a feel for how select works
        inputs = [s]
        address_dict = {}
        stored_data = {}

        while True:
            readable, _, _ = select.select(inputs, [], [])
            for item in readable:
                if item is s:
                    (client, address) = s.accept()
                    print('[CONN] Connection from {} on port {}'.format(address[0], address[1]))
                    client.setblocking(0)

                    inputs.append(client)
                    address_dict[client] = address
                    if client in stored_data:
                        del stored_data[client]
                else:
                    if item in stored_data:
                        data = stored_data[item] + item.recv(1024)
                    else:
                        data = item.recv(1024)

                    if not data:
                        item.close()
                        inputs.remove(item)
                        break

                    header_end = data.find(b'\r\n\r\n')
                    if header_end > -1:
                        if item in stored_data:
                            del stored_data[item]

                        try:
                            header_string = data[:header_end]
                            lines = header_string.split(b'\r\n')

                            request_fields = lines[0].split()
                            headers = lines[1:]

                            # set cookies to pass to file_reader (empty [] by default)
                            cookies = []
                            for header in headers:
                                header_fields = header.split(b':')
                                key = header_fields[0].strip()
                                if key == b'Cookie':
                                    cookies = header_fields[1].split(b';').strip()

                            # log request details, set method and path fields
                            method = request_fields[0].decode()
                            path = request_fields[1].decode()
                            req_address = address_dict[item]
                            print(
                                '[REQU] [{}:{}] {} request for {}'.format(req_address[0], req_address[1], method, path))

                            # set content-type value (empty string by default)
                            mime = ''
                            if path.endswith('.html'):
                                mime = 'text/html'
                            elif path.endswith('.css'):
                                mime = 'text/css'
                            elif path.endswith('.png'):
                                mime = 'image/png'
                            elif path.endswith('.jpeg'):
                                mime = 'image/jpeg'
                            elif path.endswith('.gif'):
                                mime = 'image/gif'

                            # before read attempt, set default values in case of failure
                            response_body = b""
                            content_length_number = '0'
                            response_code = '404 Not Found'
                            not_implemented = ['OPTIONS', 'POST', 'PUT', 'DELETE', 'TRACE', 'CONNECT']

                            # handle various request methods
                            if method == 'GET':
                                get_response = file_reader.get(file_path + path, cookies)
                                if get_response:
                                    response_body = get_response
                                    content_length_number = str(len(response_body))
                                    response_code = '200 OK'
                                else:
                                    print('[ERRO] [{}:{}] {} request returned error {}'.format(req_address[0],
                                                                                               req_address[1], method,
                                                                                               '404'))
                            elif method == 'HEAD':
                                head_response = file_reader.head(file_path + path, cookies)
                                if head_response:
                                    content_length_number = str(head_response)
                                    response_code = '200 OK'
                                else:
                                    print('[ERRO] [{}:{}] {} request returned error {}'.format(req_address[0],
                                                                                               req_address[1], method,
                                                                                               '404'))
                            elif method in not_implemented:
                                response_code = '501 Not Implemented'
                                print('[ERRO] [{}:{}] {} request returned error {}'.format(req_address[0],
                                                                                           req_address[1], method,
                                                                                           '501'))
                            else:
                                response_code = '400 Bad Request'
                                print('[ERRO] [{}:{}] {} request returned error {}'.format(req_address[0],
                                                                                           req_address[1], method,
                                                                                           '400'))

                        except:
                            req_address = address_dict[item]
                            print('[ERRO] [{}:{}] {} request returned error {}'.format(req_address[0],
                                                                                       req_address[1], method,
                                                                                       '400'))
                            response_code = '400 Bad Request'
                            content_length_number = '0'
                            mime = ''
                            response_body = b''


                        # construct response
                        status_line = 'HTTP/1.1 {}\r\n'.format(response_code)
                        content_length = 'Content-length: {}\r\n'.format(content_length_number)
                        content_type = 'Content-type: {}\r\n'.format(mime)

                        decoded_response = status_line + content_length + content_type + '\r\n'

                        # encode response and send to client
                        response = decoded_response.encode()
                        response += response_body
                        item.send(response)


                    else:
                        if item in stored_data:
                            stored_data[item] += data
                        else:
                            stored_data[item] = data



if __name__ == "__main__":
    port = int(sys.argv[1])
    file_path = sys.argv[2]

    FR = FileReader()

    J = Jewel(port, file_path, FR)

