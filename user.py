# 用户基本信息

from requests import Session
from urllib import parse
import json
import logging
import datetime
import urllib
import time
import uuid

from logging.handlers import RotatingFileHandler
from auth import headers, get_oauth_authorization

PROXY = "" # 代理地址
ADID = "708dac85-2841-4c3e-b297-e7ccd0d47912" # 可以使用uuid.uuid4()生成，实际上在登录时可能需要通过 https://api.twitter.com/1.1/keyregistry/register 进行注册
CLIENT_UUID = "13f1a89c-eb31-4bef-9db8-451e4c1f0989" # 可以使用uuid.uuid4()生成，实际上在登录时可能需要通过 https://api.twitter.com/1.1/keyregistry/register 进行注册
DEVICE_ID = "bf015943897d8301" # 可以随意生成16位十六进制数，实际上在登录时可能需要通过 https://api.twitter.com/1.1/keyregistry/register 进行注册
OAUTH_TOKEN = "" # 登录时获得
OAUTH_TOKEN_SECERT = "" # 登录时获得


# 日志记录器
logger = logging.getLogger('user_logger')
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
rotating_file_handler = RotatingFileHandler(f'logs/user_{datetime.datetime.now().strftime("%y%m%d%H%M%S")}.log', maxBytes=10*1024*1024, backupCount=5, encoding='utf-8')
rotating_file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
rotating_file_handler.setFormatter(formatter)
logger.addHandler(console_handler)
logger.addHandler(rotating_file_handler)

def get_url(tw_id):
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
        "rest_id": tw_id
    }

    features = {
        # 该特性(verified_phone_label_enabled)在APP的请求中默认是关闭的, 打开后返回值中会多一个verified_phone_status参数, 如果启用该特性对采集频率有影响, 可以尝试关闭
        "verified_phone_label_enabled": True,
        "super_follow_badge_privacy_enabled": True,
        "subscriptions_verification_info_enabled": True,
        "super_follow_user_api_enabled": True,
        "blue_business_profile_image_shape_enabled": True,
        "immersive_video_status_linkable_timestamps": True,
        "super_follow_exclusive_tweet_notifications_enabled": True
    }

    encode_variables = parse.quote(json.dumps(variables, ensure_ascii=False).replace(" ", "")).replace('/', '%2F')
    encode_features = parse.quote(json.dumps(features, ensure_ascii=False).replace(" ", "")).replace('/', '%2F')

    return f"https://api.twitter.com/graphql/cIgulFxDKXxDxIkVedqwzQ/UserResultByIdQuery?variables={encode_variables}&features={encode_features}"

def get_headers(oauth_token, oauth_token_secret, url):
    request_headers = headers.copy()
    
    oauth_sign = get_oauth_authorization(oauth_token=oauth_token, oauth_token_secret=oauth_token_secret, url=url)
    authorization_header = f'OAuth realm="http://api.twitter.com/", oauth_version="1.0", oauth_token="{oauth_sign["oauth_token"]}", oauth_nonce="{oauth_sign["oauth_nonce"]}", oauth_timestamp="{oauth_sign["timestamp"]}", oauth_signature="{urllib.parse.quote(oauth_sign["sign"], safe="")}", oauth_consumer_key="{oauth_sign["oauth_consumer_key"]}", oauth_signature_method="HMAC-SHA1"'
    
    request_headers.update({
        "authorization": authorization_header,
        "x-b3-traceid": uuid.uuid4().hex[:16],
        "x-twitter-client-adid": ADID,
        "x-client-uuid": CLIENT_UUID,
        "x-twitter-client-deviceid": DEVICE_ID,
    })
    
    return request_headers

if __name__ == "__main__":
    # 这里输入用户ID
    # with open("userid.txt", "r", encoding="utf-8") as f:
    #     targets = f.read().split(",")
    targets = ["44196397"]

    logger.info(f"共 {len(targets)} 个目标")

    session = Session()
    counter = 0
    start_time = time.time()
    for target in targets:
        counter += 1
        url = get_url(target)
        target_headers = get_headers(oauth_token=OAUTH_TOKEN, oauth_token_secret=OAUTH_TOKEN_SECERT, url=url)

        logger.debug(f"请求headers: \n{json.dumps(target_headers, ensure_ascii=False)}")
        
        session.headers.update(target_headers)
        logger.info(f"进行第 {counter} 次请求")
        response = session.get(
            url=url,
            proxies={
                "http": PROXY,
                "https": PROXY
            }
        )

        if counter % 100 == 0 and counter >= 100:
            use_time = round(time.time() - start_time, 4)
            logger.info(f"第 {counter - 100} 次到第 {counter} 次请求用时: {use_time}")
            start_time = time.time()

        if response.status_code != 200:
            logger.error(f"状态错误, 请求返回代码({response.status_code})不是200")
            try:
                logger.error(f"请求返回内容: \n{json.dumps(response.json(), ensure_ascii=False)}")
            except Exception as e:
                logger.error(f"请求返回内容: \n{response.content}")
            if response.status_code == 429:
                # 429一般是请求速率限制
                exit()
            break
            
        logger.debug(f"响应headers: \n{json.dumps(dict(response.headers), ensure_ascii=False)}")
            
        try:
            response_json = response.json()
        except Exception as e:
            logger.error(f"将结果进行json转换时出现错误: {e}")
            logger.error(f"返回数据可能不是json格式: \n{response.content}")
            break

        if response_json.get("errors"):
            logger.error(f'返回数据中包含错误信息: {response_json.get("errors")}')
            logger.debug(json.dumps(response_json, ensure_ascii=False))
            break

        logger.debug(json.dumps(response_json, ensure_ascii=False))

        # TODO 具体数据处理的代码

        logger.debug("休眠6秒")
        time.sleep(6)
