import hmac
import time
import base64
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import NotAuthenticated



def tob(str):
    '''str type convert to bytes'''
    return str.encode('utf-8')

def touni(binary):
    '''bytes convert to str'''
    return binary.decode('utf-8')

def token(msg):
    '''set token,cncrypto'''
    secret = 'wukong'
    hc = hmac.new(tob(secret),tob(msg))
    hc.update(tob(str(time.time())))
    cypto = hc.digest()
    return touni(base64.b64encode(cypto))

class CustomAuthentication(BaseAuthentication):
    def authenticate(self, request):
        """
        Authenticate the request and return a two-tuple of (user, token).
        """
        print('-------------------------')
        token = request._request.COOKIES.get('token_value')
        from monkey import models
        token_obj = models.Token.objects.filter(token_value=token).first()
        if token_obj:
            user_obj = token_obj.user
            return user_obj,token
        else:
            # raise NotAuthenticated
            return None



        raise NotImplementedError(".authenticate() must be overridden.")

    def authenticate_header(self, request):
        """
        Return a string to be used as the value of the `WWW-Authenticate`
        header in a `401 Unauthenticated` response, or `None` if the
        authentication scheme should return `403 Permission Denied` responses.
        """
        pass


if __name__ == '__main__':
    a = token('yuyang')
    print(a)
    print(type(a))