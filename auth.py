import base64
import hashlib
import hmac
import time
import urllib.parse
import random
import json

from urllib import parse

# 这两个值对于安卓客户端来说是固定的
TW_CONSUMER_KEY = '3nVuSoBZnx6U4vzUxf5w'
TW_CONSUMER_SECRET = 'Bcs59EFbbsdF6Sl9Ng71smgStWEGwXXKSjYvPVt7qys'

headers = {
    "timezone": "Asia/Tokyo",
    "os-security-patch-level": "2019-07-05",
    "optimize-body": "true",
    "accept": "application/json",
    "x-twitter-client": "TwitterAndroid",
    "x-attest-token": "no_token",
    "user-agent": "TwitterAndroid/10.48.0-release.0 (310480000-r-0) SM-S908N/9 (samsung;SM-S908N;samsung;SM-S908N;0;;1;2015)", # UA可以根据手机型号更改
    "x-twitter-client-adid": None,  # 该ID每个账号保持一致, 由登录时生成后和账号信息保存到一起
    "x-twitter-client-language": "en-US",
    "x-client-uuid": None,  # 该ID每个账号保持一致, 由登录时生成后和账号信息保存到一起
    "x-twitter-client-deviceid": None,  # 该ID每个账号保持一致, 由登录时生成后和账号信息保存到一起
    "authorization": None,
    "x-twitter-client-version": "10.48.0-release.0",
    "cache-control": "no-store",
    "x-twitter-active-user": "yes",
    "x-twitter-api-version": "5",
    "x-b3-traceid": None,
    "accept-language": "en-US",
}

def generate_oauth_nonce():
    """生成 OAuth 随机数
    """
    return ''.join(random.choices('0123456789', k=33))

# 生成 OAuth 授权头函数
def get_oauth_authorization(oauth_token, oauth_token_secret, method='GET', url='', body='', timestamp=None, oauth_nonce=None):
    if not url:
        return ''

    method = method.upper()
    parsed_url = urllib.parse.urlparse(url)
    link = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
    oauth_nonce = oauth_nonce or generate_oauth_nonce()
    timestamp = str(timestamp or int(time.time()))

    # 处理 URL 参数
    payload = urllib.parse.parse_qsl(parsed_url.query)

    # 处理请求体
    if body:
        try:
            # 尝试解析为 JSON
            is_json = bool(json.loads(body))
        except ValueError:
            # 如果不是 JSON，解析为查询参数
            payload += urllib.parse.parse_qsl(body)

    # 添加 OAuth 参数
    payload += [
        ('oauth_version', '1.0'),
        ('oauth_signature_method', 'HMAC-SHA1'),
        ('oauth_consumer_key', TW_CONSUMER_KEY),
        ('oauth_token', oauth_token),
        ('oauth_nonce', oauth_nonce),
        ('oauth_timestamp', timestamp)
    ]

    # 生成签名基础字符串
    payload.sort(key=lambda x: x[0])
    param_str = urllib.parse.urlencode(payload, quote_via=urllib.parse.quote)
    param_str = param_str.replace('+', '%20').replace('%', '%25').replace('=', '%3D').replace('&', '%26')
    base_string = f"{method}&{urllib.parse.quote(link, safe='')}&{param_str}"

    # 生成签名
    signing_key = f"{TW_CONSUMER_SECRET}&{oauth_token_secret or ''}"
    hashed = hmac.new(signing_key.encode('utf-8'), base_string.encode('utf-8'), hashlib.sha1)
    signature = base64.b64encode(hashed.digest()).decode('utf-8')

    return {
        'method': method,
        'url': url,
        'parse_url': parsed_url,
        'timestamp': timestamp,
        'oauth_nonce': oauth_nonce,
        'oauth_token': oauth_token,
        'oauth_token_secret': oauth_token_secret,
        'oauth_consumer_key': TW_CONSUMER_KEY,
        'oauth_consumer_secret': TW_CONSUMER_SECRET,
        'payload': payload,
        'sign': signature
    }

# 测试get_oauth_authorization方法
if __name__ == "__main__":
    variables = {
        "include_smart_block": True,
        "includeTweetImpression": True,
        "include_profile_info": True,
        "includeTranslatableProfile": True,
        "includeHasBirdwatchNotes": False,
        "include_tipjar": True,
        "includeEditPerspective": False,
        "include_reply_device_follow": True,
        "includeEditControl": True,
        "include_verified_phone_status": False,
        "rest_id": "44196397"
    }

    features = {
        "longform_notetweets_inline_media_enabled": True,
        "super_follow_badge_privacy_enabled": True,
        "longform_notetweets_rich_text_read_enabled": True,
        "super_follow_user_api_enabled": True,
        "unified_cards_ad_metadata_container_dynamic_card_content_query_enabled": True,
        "super_follow_tweet_api_enabled": True,
        "articles_api_enabled": True,
        "android_graphql_skip_api_media_color_palette": True,
        "creator_subscriptions_tweet_preview_api_enabled": True,
        "freedom_of_speech_not_reach_fetch_enabled": True,
        "tweetypie_unmention_optimization_enabled": True,
        "longform_notetweets_consumption_enabled": True,
        "subscriptions_verification_info_enabled": True,
        "blue_business_profile_image_shape_enabled": True,
        "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
        "immersive_video_status_linkable_timestamps": True,
        "super_follow_exclusive_tweet_notifications_enabled": True
    }

    encode_variables = parse.quote(json.dumps(variables, ensure_ascii=False).replace(" ", "")).replace('/', '%2F')
    encode_features = parse.quote(json.dumps(features, ensure_ascii=False).replace(" ", "")).replace('/', '%2F')

    url = f"https://api-3-0-0.twitter.com/graphql/cIgulFxDKXxDxIkVedqwzQ/UserResultByIdQuery?variables={encode_variables}&features={encode_features}"
    
    account = {
        'oauth_token': '',
        'oauth_token_secret': ''
    }
    oauth_sign = get_oauth_authorization(
        account['oauth_token'],
        account['oauth_token_secret'],
        'GET',
        url,
        timestamp="1720688485",
        oauth_nonce="281355687661718672006782385395119",
    )
    authorization_header = f'OAuth realm="http://api.twitter.com/", oauth_version="1.0", oauth_token="{oauth_sign["oauth_token"]}", oauth_nonce="{oauth_sign["oauth_nonce"]}", oauth_timestamp="{oauth_sign["timestamp"]}", oauth_signature="{urllib.parse.quote(oauth_sign["sign"], safe="")}", oauth_consumer_key="{oauth_sign["oauth_consumer_key"]}", oauth_signature_method="HMAC-SHA1"'

    print(authorization_header)
    