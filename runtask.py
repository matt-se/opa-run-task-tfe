from urllib.request import Request, urlopen
import subprocess, ssl, json,  shlex, os
import sys



ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE #adding this because of the error: "certificate verify failed"

def tfc_callback(app,url,token,body):
    # need Request to pass headers
    jsondata = json.dumps(body)
    jsondataasbytes = jsondata.encode('utf-8')   # needs to be bytes

    req = Request(url, jsondataasbytes)
    req.add_header('Content-Type', 'application/vnd.api+json')
    req.add_header('Authorization', 'Bearer ' + token)
    req.method = 'PATCH'
    resp = urlopen(req,context=ctx)
    app.logger.info("Response from TFC: %s", resp.read())


# one of the 2 ways to interact with OPA
# this method calls the OPA binary directly
def run_opa_as_shell(app, plan_file_context):
    app.logger.info("Start shell subprocess for OPA request")
    # sample command used to execute OPA from shell
    # opa exec --decision terraform/analysis/authz --bundle terraform/bundle.json 
    cmd = "opa exec --decision terraform/analysis/authz --bundle rego-files/ " + plan_file_context + ".json"
    cmp_shelx = shlex.split(cmd)

    app.logger.info("Executing OPA shell command: %s", cmd)
    output = subprocess.run(cmp_shelx, capture_output=True)
    json_output = json.loads(output.stdout)

    with open(plan_file_context + "-OPA-result.json", "w") as f:
        json.dump(json_output,f, indent=4, sort_keys=True)

    return json_output

# one of the 2 ways to interact with OPA
# this method calls the OPA using the API interface.
# this requires the OPA to be running on the same host as the TFC
def run_opa_as_api():
    app.logger.info("Send OPA request to API")
    # sample command used to execute OPA from an API process. Assumes that 


#saves the plan file to disk for later use. This is required for the OPA Shell integration.
def save_plan_file(app, run_id,workspace_name,workspace_id,data):
    #save plan file to disk
    directory_name = os.getcwd() + "/plan_cache"
    file_name = "plan_" + run_id + "-" + workspace_id + "-" + workspace_name 

    plan_file_context = directory_name + "/" + file_name  #doesn't comtain the .json extension
    app.logger.info("Save plan file to %s/%s", directory_name, file_name)
    

    isExist = os.path.exists(directory_name)
    if not isExist:
        # Create a new directory because it does not exist 
        os.makedirs(directory_name)
        print("The new directory is created!")

    with open(plan_file_context + ".json", "w") as f:
        json.dump(data,f, indent=4, sort_keys=True)
    
    return plan_file_context




def process_opa(app, rq):
    app.logger.info("Processing OPA request")

    opa_shell_integration = True

    #get variables from request
    run_id = rq['run_id']
    workspace_name = rq['workspace_name']
    workspace_id = rq['workspace_id']
    plan_json_url = rq['plan_json_api_url']
    callback_url = rq['task_result_callback_url']
    token = rq['access_token']

    #get plan from TFC
    req = Request(plan_json_url)
    req.add_header('Authorization', 'Bearer ' + token)
    content = urlopen(req, context=ctx).read()
    data = json.loads(content)

    #save plan file to disk
    plan_file_context = save_plan_file(app, run_id,workspace_name,workspace_id,data)

    #send plan to OPA
    result = None
    if opa_shell_integration:
        result = run_opa_as_shell(app, plan_file_context)
    else:
        result = run_opa_as_api() # not implemented yet

    opa_result = result['result'][0]['result']
    app.logger.info("OPA result: %s", opa_result)

    #prepare response for TFC
    response = None
    if opa_result :
        response = {
                        "data": {
                            "type": "task-results",
                            "attributes": {
                                "status": "passed",
                                "message": f"OPA Check Passed - sample message from OPA -->  {str(result)}",
                                "url": "https://example.com"
                            }
                        }
                    }
    else:
        response = {
                        "data": {
                            "type": "task-results",
                            "attributes": {
                                "status": "failed",
                                "message": "OPA Check Failed - sample message from OPA",
                                "url": "https://example.com"
                            }
                        }
                    }
    

    #send response to TFC
    app.logger.info("Sending response to TFC - %s", callback_url)
    tfc_callback(app,callback_url, token, response)