


cookieList=driver.get_cookies()
coolies_list=[item["name"]+"="+item["value"] for item in cookieList]
cookie=";".join(it for it in coolies_list)
lingxiauth=""
f=open("./lingxi-auth.txt","r")
lingxiauth=f.readlines()[0].strip()
#auth=f.readlines()[1].strip()
print(lingxiauth)
#cookie='lingxi-refresh-token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0ZW5hbnRfaWQiOiIxODY2NzEwMjE4IiwidXNlcl9uYW1lIjoiMTgyMDEwNjkxMTgiLCJyZWFsX25hbWUiOiLlvKDpnZnno4oiLCJhdmF0YXIiOiJodHRwczovL3RoaXJkd3gucWxvZ28uY24vbW1vcGVuL3ZpXzMyL0M4V0c5YmxQMFpCVUhZZWV6SHUxS2lhTFZjdU1pYlJUUDdWam52OUZXbGhTOFJsemlhellNUE13THdZMndiT29wR0laRTlEZjhOVHlDcVVCR0FMaWJHNXJyUS8xMzIiLCJhdXRob3JpdGllcyI6WyIxNTA4MzczMjYzMjQ3MzIzMTM4Il0sImNsaWVudF9pZCI6Imxpbmd4aV9zYWFzIiwicm9sZV9uYW1lIjoiZGVmYXVsdCIsImxpY2Vuc2UiOiJwb3dlcmVkIGJ5IGxpbmd4aSIsInBvc3RfaWQiOiIiLCJ1c2VyX2lkIjoiMTYyODI2OTg3NDEzMjA4MjY4OSIsInJvbGVfaWQiOiIxNTA4MzczMjYzMjQ3MzIzMTM4Iiwic2NvcGUiOlsiYWxsIl0sIm5pY2tfbmFtZSI6IuW8oOmdmeejiiIsImF0aSI6IjNmZDNlOTBiLTBhYjgtNDFlYS1iOWE3LTJmNDJlZDExYjcyYSIsImNsaWVudCI6IndlYiIsIm9hdXRoX2lkIjoiIiwiZGV0YWlsIjp7InR5cGUiOiJ3ZWIifSwiZXhwIjoxNjgwOTQ0MTA1LCJkZXB0X2lkIjoiIiwianRpIjoiNzMwZWYyMTEtYTU3Zi00ZmYzLWFiOTEtOGNjM2IyODMxMzQ3IiwiYWNjb3VudCI6IjE4MjAxMDY5MTE4In0.-Iwl7vKOTQ8xnrsaLC0zJoeVEWFnOKFmk0U7taUryIU;lingxi-access-token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0ZW5hbnRfaWQiOiIxODY2NzEwMjE4IiwidXNlcl9uYW1lIjoiMTgyMDEwNjkxMTgiLCJyZWFsX25hbWUiOiLlvKDpnZnno4oiLCJhdmF0YXIiOiJodHRwczovL3RoaXJkd3gucWxvZ28uY24vbW1vcGVuL3ZpXzMyL0M4V0c5YmxQMFpCVUhZZWV6SHUxS2lhTFZjdU1pYlJUUDdWam52OUZXbGhTOFJsemlhellNUE13THdZMndiT29wR0laRTlEZjhOVHlDcVVCR0FMaWJHNXJyUS8xMzIiLCJhdXRob3JpdGllcyI6WyIxNTA4MzczMjYzMjQ3MzIzMTM4Il0sImNsaWVudF9pZCI6Imxpbmd4aV9zYWFzIiwicm9sZV9uYW1lIjoiZGVmYXVsdCIsImxpY2Vuc2UiOiJwb3dlcmVkIGJ5IGxpbmd4aSIsInBvc3RfaWQiOiIiLCJ1c2VyX2lkIjoiMTYyODI2OTg3NDEzMjA4MjY4OSIsInJvbGVfaWQiOiIxNTA4MzczMjYzMjQ3MzIzMTM4Iiwic2NvcGUiOlsiYWxsIl0sIm5pY2tfbmFtZSI6IuW8oOmdmeejiiIsImNsaWVudCI6IndlYiIsIm9hdXRoX2lkIjoiIiwiZGV0YWlsIjp7InR5cGUiOiJ3ZWIifSwiZXhwIjoxNjgwOTQ0MTA1LCJkZXB0X2lkIjoiIiwianRpIjoiM2ZkM2U5MGItMGFiOC00MWVhLWI5YTctMmY0MmVkMTFiNzJhIiwiYWNjb3VudCI6IjE4MjAxMDY5MTE4In0.ShdoP_cvCb7jHlEvsrKi9jkFpjlbvIshry75OY-ERWc'
print("页面模拟结束，cookie获取结束")
#配置headers
for request in driver.requests:
    headers=request.headers
    break
headers["cookie"]=f'{cookie}'
headers["lingxi-auth"]=f'{lingxiauth}'
del request.headers['accept']
headers["accept"]="application/json, text/plain, */*"
headers["authorization"]="Basic bGluZ3hpX3NhYXM6bGluZ3hpX3NhYXNfc2VjcmV0"
#headers.set_param(param="accept",value="application/json, text/plain, */*")
print("headers")
print(headers)
#for i in range(848):
for i in range(1):
    print("第"+str(i)+"页")
    payload["page"]=i+1
    response=requests.post(url,params=payload,headers=headers)
    print(response.content)
    time.sleep(5)
#element = driver.find_element_by_css_selector(".s-top-login-btn") 
os.system("pause")
#for request in driver.requests:
#    if request.response and "lingxi-auth" in request.response.headers:
#        print(request.response.status_code)
#        print(request.response.headers)












toDoHtml=[
{"keyWord":"","page":1,"pageSize":20,"industryChainId":"128","regionCode":"","industryChainNodeId":"128","code":"YQYL0056","clientInfoDTO":{"platform":"pc","system":"window"}},
{"keyWord":"","page":1,"pageSize":20,"industryChainId":"128","regionCode":"","industryChainNodeId":"12801","code":"YQYL0056","clientInfoDTO":{"platform":"pc","system":"window"}},
{"keyWord":"","page":1,"pageSize":20,"industryChainId":"128","regionCode":"","industryChainNodeId":"12802","code":"YQYL0056","clientInfoDTO":{"platform":"pc","system":"window"}},
{"keyWord":"","page":1,"pageSize":20,"industryChainId":"128","regionCode":"","industryChainNodeId":"12803","code":"YQYL0056","clientInfoDTO":{"platform":"pc","system":"window"}},
{"keyWord":"","page":1,"pageSize":20,"industryChainId":"128","regionCode":"","industryChainNodeId":"12804","code":"YQYL0056","clientInfoDTO":{"platform":"pc","system":"window"}},
{"keyWord":"","page":1,"pageSize":20,"industryChainId":"128","regionCode":"","industryChainNodeId":"12805","code":"YQYL0056","clientInfoDTO":{"platform":"pc","system":"window"}},
{"keyWord":"","page":1,"pageSize":20,"industryChainId":"128","regionCode":"","industryChainNodeId":"12806","code":"YQYL0056","clientInfoDTO":{"platform":"pc","system":"window"}},
{"keyWord":"","page":1,"pageSize":20,"industryChainId":"128","regionCode":"","industryChainNodeId":"1280101","sort":"","code":"YQYL0056","clientInfoDTO":{"platform":"pc","system":"window"}},
{"keyWord":"","page":1,"pageSize":20,"industryChainId":"128","regionCode":"","industryChainNodeId":"1280102","sort":"","code":"YQYL0056","clientInfoDTO":{"platform":"pc","system":"window"}},
{"keyWord":"","page":1,"pageSize":20,"industryChainId":"128","regionCode":"","industryChainNodeId":"1280103","sort":"","code":"YQYL0056","clientInfoDTO":{"platform":"pc","system":"window"}},
{"keyWord":"","page":1,"pageSize":20,"industryChainId":"128","regionCode":"","industryChainNodeId":"1280201","sort":"","code":"YQYL0056","clientInfoDTO":{"platform":"pc","system":"window"}},
{"keyWord":"","page":1,"pageSize":20,"industryChainId":"128","regionCode":"","industryChainNodeId":"1280202","sort":"","code":"YQYL0056","clientInfoDTO":{"platform":"pc","system":"window"}},
{"keyWord":"","page":1,"pageSize":20,"industryChainId":"128","regionCode":"","industryChainNodeId":"1280203","sort":"","code":"YQYL0056","clientInfoDTO":{"platform":"pc","system":"window"}},
{"keyWord":"","page":1,"pageSize":20,"industryChainId":"128","regionCode":"","industryChainNodeId":"1280204","sort":"","code":"YQYL0056","clientInfoDTO":{"platform":"pc","system":"window"}},
{"keyWord":"","page":1,"pageSize":20,"industryChainId":"128","regionCode":"","industryChainNodeId":"1280205","sort":"","code":"YQYL0056","clientInfoDTO":{"platform":"pc","system":"window"}},
{"keyWord":"","page":1,"pageSize":20,"industryChainId":"128","regionCode":"","industryChainNodeId":"1280206","sort":"","code":"YQYL0056","clientInfoDTO":{"platform":"pc","system":"window"}},
{"keyWord":"","page":1,"pageSize":20,"industryChainId":"128","regionCode":"","industryChainNodeId":"128020101","code":"YQYL0056","clientInfoDTO":{"platform":"pc","system":"window"}},
{"keyWord":"","page":1,"pageSize":20,"industryChainId":"128","regionCode":"","industryChainNodeId":"128020102","code":"YQYL0056","clientInfoDTO":{"platform":"pc","system":"window"}},
{"keyWord":"","page":1,"pageSize":20,"industryChainId":"128","regionCode":"","industryChainNodeId":"128020103","code":"YQYL0056","clientInfoDTO":{"platform":"pc","system":"window"}},
{"keyWord":"","page":1,"pageSize":20,"industryChainId":"128","regionCode":"","industryChainNodeId":"128020104","code":"YQYL0056","clientInfoDTO":{"platform":"pc","system":"window"}},
{"keyWord":"","page":1,"pageSize":20,"industryChainId":"128","regionCode":"","industryChainNodeId":"128020201","code":"YQYL0056","clientInfoDTO":{"platform":"pc","system":"window"}},
{"keyWord":"","page":1,"pageSize":20,"industryChainId":"128","regionCode":"","industryChainNodeId":"128020202","code":"YQYL0056","clientInfoDTO":{"platform":"pc","system":"window"}},
{"keyWord":"","page":1,"pageSize":20,"industryChainId":"128","regionCode":"","industryChainNodeId":"128020203","code":"YQYL0056","clientInfoDTO":{"platform":"pc","system":"window"}},
{"keyWord":"","page":1,"pageSize":20,"industryChainId":"128","regionCode":"","industryChainNodeId":"128020204","code":"YQYL0056","clientInfoDTO":{"platform":"pc","system":"window"}},
{"keyWord":"","page":1,"pageSize":20,"industryChainId":"128","regionCode":"","industryChainNodeId":"128020205","code":"YQYL0056","clientInfoDTO":{"platform":"pc","system":"window"}},
{"keyWord":"","page":1,"pageSize":20,"industryChainId":"128","regionCode":"","industryChainNodeId":"128020301","code":"YQYL0056","clientInfoDTO":{"platform":"pc","system":"window"}},
{"keyWord":"","page":1,"pageSize":20,"industryChainId":"128","regionCode":"","industryChainNodeId":"128020302","code":"YQYL0056","clientInfoDTO":{"platform":"pc","system":"window"}},
{"keyWord":"","page":1,"pageSize":20,"industryChainId":"128","regionCode":"","industryChainNodeId":"128020303","code":"YQYL0056","clientInfoDTO":{"platform":"pc","system":"window"}},
{"keyWord":"","page":1,"pageSize":20,"industryChainId":"128","regionCode":"","industryChainNodeId":"128020601","code":"YQYL0056","clientInfoDTO":{"platform":"pc","system":"window"}},
{"keyWord":"","page":1,"pageSize":20,"industryChainId":"128","regionCode":"","industryChainNodeId":"128020602","code":"YQYL0056","clientInfoDTO":{"platform":"pc","system":"window"}},
{"keyWord":"","page":1,"pageSize":20,"industryChainId":"128","regionCode":"","industryChainNodeId":"128020603","code":"YQYL0056","clientInfoDTO":{"platform":"pc","system":"window"}},
{"keyWord":"","page":1,"pageSize":20,"industryChainId":"128","regionCode":"","industryChainNodeId":"128020604","code":"YQYL0056","clientInfoDTO":{"platform":"pc","system":"window"}},
{"keyWord":"","page":1,"pageSize":20,"industryChainId":"128","regionCode":"","industryChainNodeId":"128020605","code":"YQYL0056","clientInfoDTO":{"platform":"pc","system":"window"}},
{"keyWord":"","page":1,"pageSize":20,"industryChainId":"128","regionCode":"","industryChainNodeId":"128020606","code":"YQYL0056","clientInfoDTO":{"platform":"pc","system":"window"}},
{"keyWord":"","page":1,"pageSize":20,"industryChainId":"128","regionCode":"","industryChainNodeId":"1280301","code":"YQYL0056","clientInfoDTO":{"platform":"pc","system":"window"}},
{"keyWord":"","page":1,"pageSize":20,"industryChainId":"128","regionCode":"","industryChainNodeId":"1280302","code":"YQYL0056","clientInfoDTO":{"platform":"pc","system":"window"}},
{"keyWord":"","page":1,"pageSize":20,"industryChainId":"128","regionCode":"","industryChainNodeId":"128030101","code":"YQYL0056","clientInfoDTO":{"platform":"pc","system":"window"}},
{"keyWord":"","page":1,"pageSize":20,"industryChainId":"128","regionCode":"","industryChainNodeId":"128030102","code":"YQYL0056","clientInfoDTO":{"platform":"pc","system":"window"}},
{"keyWord":"","page":1,"pageSize":20,"industryChainId":"128","regionCode":"","industryChainNodeId":"128030103","code":"YQYL0056","clientInfoDTO":{"platform":"pc","system":"window"}},
{"keyWord":"","page":1,"pageSize":20,"industryChainId":"128","regionCode":"","industryChainNodeId":"128030201","code":"YQYL0056","clientInfoDTO":{"platform":"pc","system":"window"}},
{"keyWord":"","page":1,"pageSize":20,"industryChainId":"128","regionCode":"","industryChainNodeId":"128030202","code":"YQYL0056","clientInfoDTO":{"platform":"pc","system":"window"}},
{"keyWord":"","page":1,"pageSize":20,"industryChainId":"128","regionCode":"","industryChainNodeId":"128030203","code":"YQYL0056","clientInfoDTO":{"platform":"pc","system":"window"}},
{"keyWord":"","page":1,"pageSize":20,"industryChainId":"128","regionCode":"","industryChainNodeId":"128030204","code":"YQYL0056","clientInfoDTO":{"platform":"pc","system":"window"}},
{"keyWord":"","page":1,"pageSize":20,"industryChainId":"128","regionCode":"","industryChainNodeId":"1280401","code":"YQYL0056","clientInfoDTO":{"platform":"pc","system":"window"}},
{"keyWord":"","page":1,"pageSize":20,"industryChainId":"128","regionCode":"","industryChainNodeId":"1280402","code":"YQYL0056","clientInfoDTO":{"platform":"pc","system":"window"}},
{"keyWord":"","page":1,"pageSize":20,"industryChainId":"128","regionCode":"","industryChainNodeId":"1280403","code":"YQYL0056","clientInfoDTO":{"platform":"pc","system":"window"}},
]