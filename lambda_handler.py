import json
import urllib3
import os

#import base64
#import hashlib
#import hmac
#import boto3
#from botocore.exceptions import ClientError

HMAC_KEY = os.getenv("HMAC_KEY", None)
REGION = os.getenv("REGION", None)
EST_RUN_HOURS = os.getenv("EST_RUN_HOURS", 0)


try:
    print(HMAC_KEY)
    print(REGION)
    print(EST_RUN_HOURS)
except:
    print(f'problem with printing the environmental variables -  {Exception}')
       
       

def lambda_handler(event, context):
    cost = calc_cost()
    parse_event_result = parse_event(event)
    url = parse_event_result['callback_url']
    token = parse_event_result['access_token']
    tfc_callback(url,token,"this is my message")
    
    return {
        "statusCode": 200,
        "body": json.dumps(f"the cost is {calc_cost()}")
    }
    
    
    
    

def calc_cost():
    cost = 200
    return cost
    
    
def parse_event(event):
    print(f"parse event - {event}")
    try:
        payload = json.loads(event['body'])
        print(f" The body from the Run task is:----  {payload}")
        callback_url = payload['task_result_callback_url']
        access_token = payload['access_token']
        print(f"url and code:  {callback_url} --- {access_token}")
    except:
        print(Exception)
        return 0
    return {'callback_url':callback_url,'access_token':access_token}
        
        
        
def tfc_callback(url,token,message):
    print(f"tfc_callback - {url} - {token} - {message}")
    try:
        http = urllib3.PoolManager()
        #headers = urllib3.util.make_headers(basic_auth=token,'Content-Type'='Content-Type')
        encoded_data = json.dumps({"data": {"type": "task-results", "attributes": {"status":"passed", "message": message}}})
        r = http.request('PATCH', 
            url, 
            headers = {'Content-Type': 'application/vnd.api+json', 'Authorization': f'Bearer {token}'},
            body = encoded_data)
        print(f"The status of the result:   {r.data.decode('utf-8')}")
        return 1
    except:
        print(Exception)
        return 0
    
    
        
