import json
from urllib.parse import urlencode, parse_qs
from urllib.request import urlopen
from django.conf import settings
import logging
from .exceptions import QQAPIError
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import BadData
from .constants import SAVE_QQ_USER_TOKEN_EXPIRES

logger = logging.getLogger('django')


class OAuthQQ(object):
    """
    QQ认证辅助工具类
    """

    def __init__(self, client_id=None, redirect_uri=None, state=None, client_secret=None):
        self.client_id = client_id or settings.QQ_CLIENT_ID
        self.redirect_uri = redirect_uri or settings.QQ_REDIRECT_URI
        self.state = state or settings.QQ_STATE
        self.client_secret = client_secret or settings.QQ_CLIENT_SECRET

    def get_qq_login_url(self):
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'state': self.state
        }

        url = 'https://graph.qq.com/oauth2.0/authorize?' + urlencode(params)
        return url

    def get_access_token(self, code):
        params = {
            'grant_type': 'authorization_code',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'redirect_uri': self.redirect_uri
        }

        url = 'https://graph.qq.com/oauth2.0/token?' + urlencode(params)
        response = urlopen(url)
        response_data = response.read().decode()
        data = parse_qs(response_data)
        access_token = data.get('access_token')
        if not access_token:
            logging.error('code=%s msg=%s' % (data.get('code'), data.get('msg')))
            raise QQAPIError

        return access_token[0]

    def get_openid(self, access_token):

        url = 'https://graph.qq.com/oauth2.0/me?access_token=' + access_token
        response = urlopen(url)
        response_data = response.read().decode()
        try:
            data = json.loads(response_data[10: -4])
        except Exception:
            data = parse_qs(response_data)
            logging.error('code=%s msg=%s' % (data.get('code'), data.get('msg')))
            raise QQAPIError

        openid = data.get('openid')
        return openid

    @staticmethod
    def generate_save_user_token(openid):
        serializer = Serializer(settings.SECRET_KEY, expires_in=SAVE_QQ_USER_TOKEN_EXPIRES)
        data = {'openid': openid}
        token = serializer.dumps(data)
        return token.decode()

    @staticmethod
    def check_save_user_token(token):
        serializer = Serializer(settings.SECRET_KEY, expires_in=SAVE_QQ_USER_TOKEN_EXPIRES)
        try:
            data = serializer.loads(token)
        except BadData:
            return None
        else:
            return data.get('openid')
