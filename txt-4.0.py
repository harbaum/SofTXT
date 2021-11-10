#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# txt-4.0.py
#
# This file implements a simple webserver which handles all the
# device requests of ROBO Pro Coding. By default it listens on port
# 8000 and e-g- when running on the same host as the browser can be
# accessed from within ROBO Pro coding as localhost:8000
#
# This server currently does
# - handle cross-origin requests
# - reply to ping
# - reply to device port stream requests ("Schnittstellentest")
# - process file downloads
# - run external script on "start" request
#   - pipes stdout into stream
#

# curl -X POST http://localhost:8000/api/v1/application/project/start

import argparse
from http.server import HTTPServer, BaseHTTPRequestHandler
import time
import json
import socket
from socketserver import ThreadingMixIn
import email.parser
from pathlib import Path
import os
import subprocess, pty, threading, select, queue
from functools import partial
from urllib.parse import unquote

BASE = os.path.dirname(os.path.realpath(__file__))
WORKSPACES = os.path.join(BASE, "workspaces")
RUNNER = "run.py"

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class MyHandler(BaseHTTPRequestHandler):
    def __init__(self, ctx, *args, **kwargs):
        self.ctx = ctx
        super().__init__(*args, **kwargs)

    def _set_headers(self, stream=False):
        self.send_response(200)
        if stream:  self.send_header("Content-type", "text/event-stream")
        else:       self.send_header("Content-type", "application/json")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "*")
        self.send_header("Access-Control-Allow-Credentials", "true")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def send_error(self, code):
        self.send_response(code)
        self.send_header("Content-type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
            
    def parse_url(self, url):
        # cut off any query. We'll ignore that for now
        parts = url.split("?")
        url = parts[0]
        if len(parts) > 1: query = parts[1]
        else:              query = None

        # split url into seperate parts
        parts = url.split("/")

        # we need at least 4 parts ""/"api"/"vX"/cmd
        if len(parts) < 4:
            print(bcolors.FAIL + "Incomplete url: " + url + bcolors.ENDC);
            return None

        # check for api version 1
        if parts[0] != "" or parts[1].lower() != "api" or parts[2].lower() != "v1":
            print(bcolors.FAIL + "Invalid API request: " + url + bcolors.ENDC);
            return None

        parts = parts[3:]
        
        # catch simple ping and stop
        if len(parts) == 1 and (parts[0] == "ping" or parts[0] == "stop"):
            print(bcolors.OKGREEN + parts[0] + bcolors.ENDC);
            return { "cmd": parts[0] }

        reply = { }

        if len(parts):
            target = parts[0]
            parts = parts[1:]

            if target == "controller":
                # the next may be a controller id
                try:
                    reply["controller"] = int(parts[0])
                    parts = parts[1:]
                except:
                    reply["controller"] = None

                # next may be an interface
                if len(parts):
                    if parts[0] == "message-stream":
                        reply["stream"] = True
                    else:                        
                        interface = parts[0]
                        parts = parts[1:]

                        # interface may also have an subsequent id
                        try:
                            reply["interface"] = ( interface, int(parts[0]) )
                            parts = parts[1:]
                        except:
                            reply["interface"] = interface

                # there now may the stream request be left
                if len(parts):
                    if parts[0] == "message-stream":
                        reply["stream"] = True
                    elif parts[0] == "stop":
                        reply["cmd"] = parts[0]
                    else:
                        print(bcolors.FAIL + "unexpected extra: " + parts[0] + bcolors.ENDC)
                    parts = parts[1:]
                        
            elif target == "workspaces":
                if len(parts):
                    reply["workspaces"] = parts[0]
                    parts = parts[1:]
                else:
                    reply["workspaces"] = None

                if len(parts):
                    if parts[0] == "files":
                        reply["files"] = True
                        parts = parts[1:]
                    else:
                        print(bcolors.FAIL + "workspace" + str(parts) + bcolors.ENDC)
                    
            elif target == "application" or  target == "debugger":
                if len(parts):
                    reply[target] = parts[0]
                    parts = parts[1:]
                else:
                    reply[target] = None
                if len(parts):
                    reply["cmd"] = parts[0]
                    parts = parts[1:]
                    
            elif target == "remote":
                if len(parts) > 1:
                    if parts[0] == "send-command":
                        print(bcolors.OKCYAN + "VoiceCommand: \"{}\"".format(unquote(parts[1])) + bcolors.ENDC)
                        reply["remote"] = unquote(parts[1])
                        parts = parts[2:]
                    else:
                        print(bcolors.FAIL + "unexpected remote command: " + parts[0] + bcolors.ENDC)
                        
            else:
                print(bcolors.FAIL + "unexpected target: " + target + bcolors.ENDC)

            if len(parts):
                print(bcolors.FAIL + "unexpected parts remaining: " + str(parts) + bcolors.ENDC)
                
        print(bcolors.HEADER + "reply:" + str(reply) + bcolors.ENDC)
        return reply
    
        
    def do_GET(self):
        print("GET", self.path);
        info = self.parse_url(self.path)
        
        if not info:
            self.send_error(404);
            return

        # someone is trying to get infos about the workspacxe
        if "workspaces" in info:
            if not "files" in info:
                # try to open the workspace itself

                prjfile = os.path.join(WORKSPACES,info["workspaces"], ".project.json")
                try:
                    f = open(prjfile, "r")
                    prjinfo = json.loads(f.read())                   
 
                    reply = {
                        "name": info["workspaces"],
                        "path": os.path.join(WORKSPACES, info["workspaces"]),
                        "uuid": prjinfo["uuid"]
                    }
                    self._set_headers(False)
                    # This is _not_ what RoboPro expects. And thus it will
                    # always assume that the project doesn't exist yet
                    # self.wfile.write(json.dumps(reply).encode("utf8"))
                    self.wfile.write("[]".encode("utf8"))
                    return
                except:
                    print(bcolors.FAIL + "Project read failed:" + info["workspaces"] + bcolors.ENDC)
            else:
                # request for entire file listing
                dir = os.path.join(WORKSPACES,info["workspaces"])
                try:                    
                    reply = []
                    for f in os.listdir(dir):
                        reply.append( { "name": f,
                                        "path": os.path.join(WORKSPACES,info["workspaces"],f)
                        } ) 
                    self._set_headers(False)
                    self.wfile.write(json.dumps(reply).encode("utf8"))
                    return
                except:
                    print(bcolors.FAIL + "Listing failed: " + info["workspaces"] + bcolors.ENDC)
                
            self.send_error(404);
            return            
        
        self._set_headers("stream" in info)
        
        if "stream" in info:
            # clear console on start
            if not "inputs" in self.path and not "counters" in self.path:
                #  "clear", "started", "finished", "text"
                msg = [ { "type": "clear" } ]
                data = ("data: " + json.dumps(msg) + "\n\n").encode("utf8")
                self.wfile.write(data)
                self.wfile.flush()
                        
            while(True):
                msg = None
                
                if "inputs" in self.path:                
                    # build a fake message with some delay
                    msg = [ { "name":"I1", "value": 12 },
                            { "name":"I2", "value": 34 },
                            { "name":"I3", "value": 0 },
                            { "name":"I4", "value": -100 },
                            { "name":"I5", "value": 0 },
                            { "name":"I6", "value": 0 },
                            { "name":"I7", "value": 0 },
                            { "name":"I8", "value": 0 } ]
                    time.sleep(1);
                elif "counters" in self.path:                    
                    # build a fake message with some delay
                    msg = [ { "name":"C1", "value": 12 },
                            { "name":"C2", "value": 34 },
                            { "name":"C3", "value": 0 },
                            { "name":"C4", "value": 0 } ]
                    time.sleep(1);
                else:
                    try:
                        # check if there's data in the queue
                        data = self.ctx["queue"].get(True, .1)
                        if "text" in data:
                            msg = [ { "type": "text", "data": [ data["text"]  ] } ]
                    except:
                        # send an empty message on timeout to we can detect broken
                        # connections
                        msg = [ ]
                if msg:
                    try:
                        self.wfile.write(("data: " + json.dumps(msg) + "\n\n").encode("utf8"))
                        self.wfile.flush()
                    except Exception as e:
                        print("streaming failed:", str(e));
                        return
                    
        else:
            # dunno what to send. Send empty json message
            self.wfile.write("[]".encode("utf8"))

    # just silently reply to optiojns
    def do_OPTIONS(self):
        self._set_headers()

    def do_DELETE(self):
        print("DELETE", self.path);
        
        info = self.parse_url(self.path)
        if not info:
            self.send_error(404);
            return
        
        self._set_headers()

        if "cmd" in info and info["cmd"] == "stop":
            self.stop()

    def parse_multipart(self, ct, data):
        # assemble message
        data = ("Content-Type: "+ct+"\n\n").encode("utf8") + data;  
        msg = email.parser.BytesParser().parsebytes(data)

        reply = { }
        for part in  msg.get_payload():
            reply[part.get_param('filename', header='content-disposition')] = part.get_payload(decode=True).decode("utf-8");
            
        return reply

    def save_workspace(self, name, data):
        base = os.path.join(WORKSPACES, name)        
        Path(base).mkdir(parents=True, exist_ok=True)
        for i in data:
            if i.startswith("/"): fname = os.path.join(base, i[1:])
            else:                 fname = os.path.join(base, i)
            print(bcolors.OKCYAN + "Writing " + fname + "..." + bcolors.ENDC);
            Path(os.path.dirname(fname)).mkdir(parents=True, exist_ok=True)
            with open(fname,'w') as f:
                f.write(data[i])    

    def console_handle(self, data):
        # add data to buffer an forward complete \n terminated lines only
        self.console_buffer += data.replace("\r", "")
        lines = self.console_buffer.split("\n")
        if len(lines) > 1:
            for line in lines[:len(lines)-1]:
                    self.ctx["queue"].put( { "text": line } )

            self.console_buffer = lines[-1]
                
    # thread to listen for incoming text data from app
    def console_listener(self):
        self.console_buffer = ""

        # do this while no execption has accured and while the
        # process is either starting up or running.
        e = []
        while len(e) == 0 and (self.ctx["proc"] == None or self.ctx["proc"].poll() == None):
            r, w, e = select.select([self.server_fd], [], [self.server_fd], 1)
            
            if self.server_fd in r:
                self.console_handle(os.read(self.server_fd,100).decode())

            # frequently send a ping into the app
            self.send( { "ping": None } )

        print("Console listener done");
        self.ctx["proc"] = None
        os.close(self.server_fd)
        os.close(self.client_fd)
        os.close(self.ctx["cmd_server_fd"])
        os.close(self.cmd_client_fd)
        self.ctx["cmd_server_fd"] = None
          
    def stop(self):
        if "proc" in self.ctx and self.ctx["proc"]:
            print("Stopping running process")
            self.ctx["proc"].terminate()
            self.ctx["proc"] = None
        
    def run(self, app):
        print("Running", app);

        self.ctx["proc"] = None
        self.server_fd, self.client_fd = pty.openpty()
        self.cmd_client_fd, self.ctx["cmd_server_fd"] = pty.openpty()
        threading.Thread(target=self.console_listener, daemon=True).start()
        
        self.ctx["proc"] = subprocess.Popen( [ os.path.join(BASE, RUNNER), app ], stdout=self.client_fd, stdin=self.cmd_client_fd )
        # self.ctx["proc"] = subprocess.Popen( [ os.path.join(BASE, RUNNER), app ], stdin=self.cmd_client_fd )   # without out redirection

    def send(self, data):
        # send data as newline terminated json into the subprocess
        if self.ctx["cmd_server_fd"]:
            os.write(self.ctx["cmd_server_fd"], (json.dumps(data)+"\n").encode("utf8"))
        
    def do_POST(self):
        print("POST", self.path);
        info = self.parse_url(self.path)
        if not info:
            self.send_error(404);
            return

        self._set_headers()
        content_len = self.headers.get('Content-Length')
        content_type = self.headers.get('Content-Type')

        if content_len:
            content_len = int(content_len)        
            post_body = self.rfile.read(content_len)
        else:
            post_body = None
            
        if post_body:
            if content_type == "application/json":
                # run body through a json parser
                try:
                    post_data = json.loads(post_body)                   
                    print(bcolors.OKCYAN + "POST: " + str(post_data) + bcolors.ENDC);
                except:
                    print(bcolors.FAIL + "POST decoding failed" + bcolors.ENDC)

            elif content_type.split(";")[0] == "multipart/form-data":
                post_data = self.parse_multipart(content_type, post_body);

                # check if we know where to save this
                if "workspaces" in info:
                    self.save_workspace(info["workspaces"], post_data);
            else:
                print(bcolors.FAIL + "Unexpected content-type:" + content_type + bcolors.ENDC)

        if "application" in info and "cmd" in info and info["cmd"] == "start":
            self.run(info["application"])
            
        if "remote" in info:
            self.send( { "remote": info["remote"] })

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""
    
def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # just some dummy adress, doesn't even have to be reachable
        s.connect(('8.8.8.8', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

# run main HTTPServer
def run(addr="localhost", port=8000):
    server_address = (addr, port)

    # create queue for console message stream (and perhaps later also
    # device port states for the "Schnittstellentest").
    handler = partial(MyHandler, { "queue": queue.Queue() } )
    httpd = ThreadedHTTPServer(server_address, handler)

    # if no addr was given (which is default behaviour), then
    # try to display the address used with the default route
    if not addr: addr = get_ip()
 
    print(f"Starting TXT-4.0 server on http://{addr}:{port}")
    httpd.serve_forever()
    
if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Run TXT-4.0 server")
    parser.add_argument(
        "-l",
        "--listen",
        default="",
        help="Specify the IP address on which the server listens",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=8000,
        help="Specify the port on which the server listens",
    )
    args = parser.parse_args()
    run(addr=args.listen, port=args.port)
