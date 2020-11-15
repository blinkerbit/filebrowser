import jwt
import datetime
import secrets

TOKEN_SECRET = None


def get_secret():
    global TOKEN_SECRET
    if not TOKEN_SECRET:
        TOKEN_SECRET = secrets.token_bytes(1024)
    else:
        return TOKEN_SECRET


def get_token(username):
    return jwt.encode(
        {
            "user": username,
            "a": {2: True},
            "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=60 * 60 * 4),
        },
        get_secret(),
        algorithm="HS256",
    )


def can_access(username, password):
    return True


def gen_token(username):
    return "ASDF"


def get_server_token():
    return "server_token"


options = {
    "verify_signature": True,
    "verify_exp": True,
    "verify_nbf": False,
    "verify_iat": True,
    "verify_aud": False,
}


def require_auth(handler_class):
    """ Handle Tornado JWT Auth """

    def wrap_execute(handler_execute):
        def require_auth(handler, kwargs):

            auth = handler.request.headers.get("Authorization")
            if auth:
                parts = auth.split()

                if parts[0].lower() != "bearer":
                    handler._transforms = []
                    handler.set_status(401)
                    handler.write("invalid header authorization")
                    handler.finish()
                elif len(parts) == 1:
                    handler._transforms = []
                    handler.set_status(401)
                    handler.write("invalid header authorization")
                    handler.finish()
                elif len(parts) > 2:
                    handler._transforms = []
                    handler.set_status(401)
                    handler.write("invalid header authorization")
                    handler.finish()

                token = parts[1]
                try:
                    jwt.decode(token, get_secret(), options=options)

                except Exception as e:
                    handler._transforms = []
                    handler.set_status(401)
                    handler.write(e.message)
                    handler.finish()
            else:
                handler._transforms = []
                handler.write("Missing authorization")
                handler.finish()

            return True

        def _execute(self, transforms, *args, **kwargs):

            try:
                require_auth(self, kwargs)
            except Exception:
                return False

            return handler_execute(self, transforms, *args, **kwargs)

        return _execute

    handler_class._execute = wrap_execute(handler_class._execute)
    return handler_class
