from  tornado.web import RequestHandler,Application
import asyncio
import tailer
import json
import socket
import glob

from access_manager import can_access,gen_token,get_server_token,require_auth
FQDN =socket.getfqdn()

def set_target(target):
    nonlocal self
    return self.request.full_url.replace(FQDN,target)

@require_auth
class FileReader(RequestHandler):
    """
    /tail/filename=filename&server="target"
    """
    def get(self,mode):

        target = self.get_argument("server",None)
        if target not in FQDN:
            #self.request.full_url().replace(FQDN,target)
            self.redirect(set_target(target), permanent=False)
        filepath = self.get_argument("filepath")

        if mode in ["tail","head"]:
            lines=self.get_argument("lines",100)
            with open(filepath,"r") as f :
                lines =getattr(tailer)[type](f,lines)
                self.finish(lines)

        elif mode in ["search"]:
            lines=[]
            substring = self.get_argument("string",None)
            if substring is not None:
                with open(filepath) as f:
                    count =0
                    for line in f:
                        count+=1
                        if substring in line:
                            lines.append([count,line])
            self.finish(lines)

        elif "part" in mode :
            from_lines = self.get_argument("from", None)
            to_lines = self.get_argument("to", None)
            with open(filepath) as f:
                lines=f.readlines()
            lines = lines[from_lines:to_lines]
            if "search" in mode:
                substring=self.get_argument("string")
                lines = [line for line in lines if substring in line]
            return lines



def get_config():
    with open("config.json") as f :
        config= json.load(f)
    return config

def get_file_list():
    config=get_config()
    patterns = config[FQDN]
    file_list = []
    for pattern in patterns:
        file_list+=glob.glob(pattern)
    return file_list



class ServerList(RequestHandler):
    """
    /servers --> to get server list
    /servers/<servername> --> to get list of files available to view
    """
    def initialize(self):
        self.config=get_config()

    async def get(self,mode,server=None):
        if not server:
            config= get_config()
            servers  =list(config['servers'].keys())
            return await self.finish(servers)
        if server:
            target = server
            if target not in FQDN:
                self.redirect(self.request.full_url().replace(FQDN, target), permanent=False)
            else:
                self.finish(get_file_list())






class Auth(RequestHandler):
    """
    /auth
    """
    def post(self):
        username = self.get_argument("username")
        password =self.get_argument("password")
        if can_access(username,password):
            token =gen_token(username)
        return self.finish(token)



def get_app():
    import uuid
    settings = {
        "cookie_secret": "__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__"
    }
    return   Application(
        [
            (r"/auth",Auth),
            (r"/log/(.*)",FileReader),
            (r"/servers/(.*)",ServerList)


         ],**settings
    )









# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    config=get_config()
    from tornado.web import HTTPServer
    import platform
    import uvloop
    from tornado.ioloop import IOLoop
    server= HTTPServer(get_app())
    server.bind(config['SERVER_PORT'])
    server.start(0)
    if platform.system()=="Windows":
        IOLoop.start()
    else:
        from tornado.platform.asyncio import AsyncIOMainLoop
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        AsyncIOMainLoop().install()
        asyncio.get_event_loop().run_forever()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
