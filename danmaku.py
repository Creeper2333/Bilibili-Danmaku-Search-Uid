import os
import requests
import json
import sys
import xlwt
import time
import datetime
import xmltodict
from tkinter import *
from MyQR import myqr
from bs4 import BeautifulSoup
from PIL import Image, ImageTk

#hash decrypt from https://github.com/Aruelius/crc32-crack

CRCPOLYNOMIAL = 0xEDB88320
crctable = [0 for x in range(256)]

def create_table():
    for i in range(256):
        crcreg = i
        for _ in range(8):
            if (crcreg & 1) != 0:
                crcreg = CRCPOLYNOMIAL ^ (crcreg >> 1)
            else:
                crcreg = crcreg >> 1
        crctable[i] = crcreg

def crc32(string):
    crcstart = 0xFFFFFFFF
    for i in range(len(str(string))):
        index = (crcstart ^ ord(str(string)[i])) & 255
        crcstart = (crcstart >> 8) ^ crctable[index]
    return crcstart

def crc32_last_index(string):
    crcstart = 0xFFFFFFFF
    for i in range(len(str(string))):
        index = (crcstart ^ ord(str(string)[i])) & 255
        crcstart = (crcstart >> 8) ^ crctable[index]
    return index

def get_crc_index(t):
    for i in range(256):
        if crctable[i] >> 24 == t:
            return i
    return -1

def deep_check(i, index):
    string = ""
    tc=0x00
    hashcode = crc32(i)
    tc = hashcode & 0xff ^ index[2]
    if not (tc <= 57 and tc >= 48):
        return [0]
    string += str(tc - 48)
    hashcode = crctable[index[2]] ^ (hashcode >>8)
    tc = hashcode & 0xff ^ index[1]
    if not (tc <= 57 and tc >= 48):
        return [0]
    string += str(tc - 48)
    hashcode = crctable[index[1]] ^ (hashcode >> 8)
    tc = hashcode & 0xff ^ index[0]
    if not (tc <= 57 and tc >= 48):
        return [0]
    string += str(tc - 48)
    hashcode = crctable[index[0]] ^ (hashcode >> 8)
    return [1, string]

def main(string):
    index = [0 for x in range(4)]
    i = 0
    ht = int(f"0x{string}", 16) ^ 0xffffffff
    for i in range(3,-1,-1):
        index[3-i] = get_crc_index(ht >> (i*8))
        snum = crctable[index[3-i]]
        ht ^= snum >> ((3-i)*8)
    for i in range(100000000):
        lastindex = crc32_last_index(i)
        if lastindex == index[3]:
            deepCheckData = deep_check(i, index)
            if deepCheckData[0]:
                break
    if i == 100000000:
        return -1
    return f"{i}{deepCheckData[1]}"

def caculate(target):
    create_table()
    return main(target)

#bilibili options
def GetUsrLv(uid,sessdata):
    try:
        headers = {
        'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36',
        'Host':'api.bilibili.com'
        }
        data={}
        data.update(mid=uid)
        cookie={}
        cookie.update(SESSDATA=sessdata)
        rslt=requests.get('http://api.bilibili.com/x/space/acc/info',headers=headers,
                      params=data,cookies=cookie,timeout=10)
        rsltJson=json.loads(rslt.text)
        return rsltJson['data']['level']
    except:
        return '-1'

def GetCid(bv):
    headers={
    'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36',
    'Host':'api.bilibili.com',
    'content-type':'application/x-www-form-urlencoded'
    }
    data={}
    data.update(bvid=bv)
    #print(data)
    rslt=requests.get('http://api.bilibili.com/x/player/pagelist',headers=headers,
                      params=data,timeout=10)
    print(rslt.text)
    rsltJson=json.loads('['+rslt.text+']')
    cid=rsltJson[0]['data'][0]['cid']
    return cid

def GetDanmaku(cid,sessdata):
    headers={
    'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36',
    'Host':'api.bilibili.com',
    'content-type':'application/x-www-form-urlencoded'
    }
    data={}
    data.update(oid=cid)
    rslt=requests.get('http://api.bilibili.com/x/v1/dm/list.so',headers=headers,
                      params=data,timeout=10)
    return rslt

def loginQr():
    print('打开b站客户端，扫码并确认后关闭扫码窗口即可。')
    headers = {
    'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36',
    'Host':'passport.bilibili.com'
    }
    rslt=requests.get('http://passport.bilibili.com/qrcode/getLoginUrl',
                  headers=headers,timeout=10)
    urlJson=json.loads('['+rslt.text+']')
    url=urlJson[0]['data']['url']
    sp=os.getcwd()+'\\'
    myqr.run(words=url,
         version=1,
         level='M',
         save_dir=sp,
        )
    root=Tk()
    root.resizable(width='false', height='false')
    root.title='QrCode'
    label=Label(root,text='使用b站客户端扫码-by Creeper2333\n盗源码的死个马，骨灰飞扬千万家')
    label.grid(row=0,column=0)
    img=Image.open('qrcode.png')
    photo=ImageTk.PhotoImage(img)
    imglabel=Label(root,image=photo)
    imglabel.grid(row=1,column=0,columnspan=3)
    root.mainloop()
    return urlJson

def loginRslt(data):
    headers = {
    'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36',
    'Host':'passport.bilibili.com'
    }
    postData={}
    postData.update(oauthKey=data[0]['data']['oauthKey'])
    #print(postData)
    loginInfo=requests.post('http://passport.bilibili.com/qrcode/getLoginInfo',
                           headers=headers,data=postData,timeout=10)
    #print(loginInfo.text)
    #print(str(loginInfo.cookies))
    return loginInfo

def Check(source):
    source=source.replace('!','')
    source=source.replace('！','')
    source=source.replace(':','')
    source=source.replace('：','')
    source=source.replace('。','')
    source=source.replace('，','')
    source=source.replace('.','')
    source=source.replace(',','')
    source=source.replace('我','')
    source=source.replace('个','')
    num=0
    try:
        num=int(source)
        if(str(num).replace('233','')==source):
            return True
        elif(num%6 != 0):
            return False
        else:
            return True
    except:
        if('第' in source or '热着' in source or
           '热乎' in source or '烫' in source or
           '热热' in source or'名以后' in source or
           '沙发' in source or '关上前' in source or
           '来了' in source or '分钟' in source or
           '刚刚' in source or '来啦' in source or
           '播放' in source or '前排' in source or
           '没人' in source or '报到' in source or
           '之后' in source or '赞' in source or
           '以前' in source or '报道' in source):
            return True
        else:
            return False

def XmlToJson(dm_xml):
    try:
        #print(xml)
        convertJson=xmltodict.parse(dm_xml,encoding='utf-8')
        jsonRslt_=json.dumps(convertJson,indent=4)
        jsonRslt=json.loads(jsonRslt_)
        return jsonRslt
    except:
        print('Xml to json convert failed')

if __name__ == '__main__':
    if(input('选择登录方式：1是二维码，其它是手动输入SESSDATA和bili_jct。')=='1'):
        json_=loginQr()
        loginInfo=loginRslt(json_)
        print(str(loginInfo.cookies))
        print(loginInfo.text)
        loginJson=json.loads('['+loginInfo.text+']')
        try:
            loginMsg=loginJson[0]['message']
            print('登录操作失败,失败信息：'+loginMsg)
            SESSDATA='null'
            bili_jct='null'
            cid='null'
            input()
            os._exit(0)
        except:
            print('登录成功！')
            SESSDATA=loginInfo.cookies['SESSDATA']
            bili_jct=loginInfo.cookies['bili_jct']
            bvid=input('bv号:')
            cid=GetCid(bvid)
    else:
        try:
            SESSDATA=input('SESSDATA:')
            bili_jct=input('bili_jct')
            bvid=input('bv号')
            cid=GetCid(bvid)
        except:
            input('请正确输入内容。')
            os._exit(0)

    xmlRslt=GetDanmaku(cid,SESSDATA)
    xmlRslt.encoding='utf-8'
    print('弹幕获取完成。')
    bs=BeautifulSoup(xmlRslt.text,'lxml')
    danmaku=bs.find_all('d')
    forbidden_dm_content=[]
    forbidden_usr=[]
    forbidden_dm_id=[]
    forbidden_level=[]
    for t in danmaku:
        #print(t)
        t_json=XmlToJson(str(t))
        print(t_json)
        data=t_json['d']['@p']
        d=data.split(',')
        word=t_json['d']['#text']
        if Check(word):
            forbidden_dm_content.append(word)
            usrid=caculate(d[6])
            forbidden_usr.append(usrid)
            forbidden_level.append(GetUsrLv(usrid,SESSDATA))
            forbidden_dm_id.append(d[7])

    f=xlwt.Workbook()
    tbl=f.add_sheet(bvid,datetime.datetime.now().strftime('%Y-%m-%d'))
    tbl.write(0,0,'弹幕内容')
    tbl.write(0,1,'弹幕发送者uid')
    tbl.write(0,2,'弹幕id')
    tbl.write(0,3,'用户等级')

    for i in range(len(forbidden_usr)):
        tbl.write(i+1,0,forbidden_dm_content[i])
        tbl.write(i+1,1,forbidden_usr[i])
        tbl.write(i+1,2,forbidden_dm_id[i])
        tbl.write(i+1,3,forbidden_level[i])

    f.save('danmaku.xls')
    #jsonRslt=XmlToJson(xmlRslt)
    #print(jsonRslt)
    input('完成，内容已输出至 danmaku.xls。')
