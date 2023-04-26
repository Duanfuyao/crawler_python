import seleniumwire 
from seleniumwire  import webdriver
from selenium.webdriver.common.by import By
import time
import requests
import os
#基本操作，配置浏览器的
driver=webdriver.Chrome(executable_path="./chromedriver.exe")
#窗口是否最大化
driver.maximize_window()
#接下来开始获取真实信息：
toDoHtml=[
{"keyWord":"","page":1,"pageSize":20,"industryChainId":"128","regionCode":"","industryChainNodeId":"128","code":"YQYL0056","clientInfoDTO":{"platform":"pc","system":"window"}}]
payload=toDoHtml[0]
url="https://www.lingxidata.cn/#/graph/index"

#模拟浏览器获取cookies
driver.get(url)
time.sleep(5)

account="18201069118"
password="abcd1234.."

login_button=driver.find_elements(By.CSS_SELECTOR,"h4[class='login-title']>span")[1]
login_button.click()
login_account=driver.find_element(By.CSS_SELECTOR,"input[id='userNameInput']")
login_password=driver.find_element(By.CSS_SELECTOR,"input[id='passWordInput']")
login_account.send_keys(account)
login_password.send_keys(password)
submmit_button=driver.find_elements(By.CSS_SELECTOR,"div[class='login-main']>div>form>div>div>button>span")
for x in submmit_button:
    if x.text.strip()=="登录":
        x.click()
        break

time.sleep(20)
#toCrawl=["电解液溶剂","电解液添加剂","锂盐","锂电池隔膜","锂电池结构件","粘结剂","分散剂","铝塑膜","导电剂","铜箔","铝箔"]
#toCrawl=["磷酸铁锂","磷酸锰铁锂","三元材料","其他正极材料","石墨材料","碳材料","钛酸锂","硅碳负极","其他负极材料"]
#toCrawl=["锂电芯","PVC膜","连接线束","锂电池模组","BMS","线束连接器","模组外包装"]
#toCrawl=["镍钴锰矿","锂矿","石墨矿","消费电子领域","动力电池领域","储能领域","锂电池回收","其他锂电池"]
toCrawl=["镍钴锰矿"]
#toCrawl=["磷酸锰铁锂","三元材料","其他正极材料","石墨材料","碳材料","钛酸锂","硅碳负极","其他负极材料"]
#toCrawl=["正极材料","负极材料","锂电池电解液","其他辅助材料","锂电池生产","锂电池封装","锂电池生产组装","锂电池材料","锂电池","锂电池原材料","锂电池应用"]

tumind=driver.find_element(By.CSS_SELECTOR,"div[id='chanyetupu-mind']")
chanyes=tumind.find_elements(By.CSS_SELECTOR,"g[id^='minder_node']>g[id^='node_text']")
fx=open("fielddata.txt","w",encoding="utf-8")
fa=open("oridata.txt","w",encoding="utf-8")
for companyName in toCrawl:
    for chanye in chanyes:
        if chanye.text.strip()==companyName:
            chanye.click()
            time.sleep(10)
            break
    text_1=driver.find_elements(By.CSS_SELECTOR,"div[class='list-wrap']")
    button=text_1[1].find_element(By.CSS_SELECTOR,"div[class='list-head']>div[class='head-item']>span")
    comps=text_1[1].find_elements(By.CSS_SELECTOR,"div>div>div>div[class='ent-item']>div[class='ent-name']")  
    techs=text_1[1].find_elements(By.CSS_SELECTOR,"div>div>div>div[class='ent-item']>div[class='item-info']")  
    companys=[]
    tech=[]
    for i in comps:
        companys.append(i.text)
    button.click()
    for i in techs:
        tech.append(i.text)
    stringss=""
    for i in companys:
        stringss=stringss+i +" "
    fx.write("$$"+companyName+"\n")
    fx.write(stringss+"\n")
    stringss=""
    for i in tech:
        stringss=stringss+i +" "
    fx.write(stringss+"\n")
    fa.write("$$"+companyName+"\n")
    button=text_1[1].find_element(By.CSS_SELECTOR,"div[class='list-head']>div[class='head-item']>span")
    button.click()
    #continue
    for i in range(100):
        text_1=driver.find_elements(By.CSS_SELECTOR,"div[class='list-wrap']")
        text_2=text_1[0].find_elements(By.CSS_SELECTOR,"div>div>div[class='text-info']")
        #公司名
        for x in text_2:
            outString=""
            companyname=x.find_element(By.CSS_SELECTOR,"div>span[class='ent-name']").text.replace(" ", "-")
            outString=outString+companyname
            #公司情况
            try:
                companyname=x.find_element(By.CSS_SELECTOR,"div>span[class^='ent-status']").text.replace(" ", "-")
                outString=outString+" "+companyname
            except:
                outString=outString+" placeholder"
                pass
            #公司规模
            try:
                companyname=x.find_element(By.CSS_SELECTOR,"div>span[class='tag']").text.replace(" ", "-")
                outString=outString+" "+companyname
            except:
                outString=outString+" placeholder"
                pass
            #公司类型
            try:
                companyname=x.find_element(By.CSS_SELECTOR,"div>span[class$='purple']").text.replace(" ", "-")
                outString=outString+" "+companyname
            except:
                outString=outString+" placeholder"
                pass
            #公司融资情况
            try:
                companyname=x.find_element(By.CSS_SELECTOR,"div>span[class$='green']").text.replace(" ", "-")
                outString=outString+" "+companyname
            except:
                outString=outString+" placeholder"
                pass
            #公司级别
            try:
                companyname=x.find_element(By.CSS_SELECTOR,"div>span[class$='red']").text.replace(" ", "-")
                outString=outString+" "+companyname
            except:
                outString=outString+" placeholder"
                pass
            #公司细节
            companyDel=x.find_elements(By.CSS_SELECTOR,"div>span[class^='text-value']")
            cDel=[]
            for j in companyDel:
                if j.text.strip()!="":
                    cDel.append(j.text.replace(" ", "-"))
            for j in cDel:
                outString=outString+" "+j
            fa.write(outString+"\n")
        try:
            button=driver.find_element(By.CLASS_NAME,"btn-next")
            toJ=button.get_attribute("disabled")
            if button.get_attribute("disabled")=="true":
                break
            button.click()
        except:
            button=driver.find_element(By.CLASS_NAME,"btn-next")
            toJ=button.get_attribute("disabled")
            if button.get_attribute("disabled")=="true":
                break
            button.click()
        time.sleep(5)
fx.close()    
fa.close()
driver.quit()



#账号：18201069118
#密码：abcd1234..




