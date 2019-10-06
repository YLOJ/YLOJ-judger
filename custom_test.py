#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'QAQ AutoMaton'

import yaml,sys,json
from oj import *
import time
import pymysql
def report(message):
    if len(sys.argv)==1:
        print(message)
    else:
        db=pymysql.connect(host,user,password,database)
        cursor=db.cursor()
        #message=pymysql.escape_string(message)
        cursor.execute("update custom_tests set output=%s where id=%s",(message,sys.argv[1]))
        db.commit()
        time.sleep(1)
        req=requests.post(update_link+'/api/custom_test_update',{
        'token':submission_update_token,
        'id':sys.argv[1],
        'output':message
        })
with open("user/lang","r") as f:
    lang=int(f.read())
if lang==0:
    code=moveIntoSandbox("user/code.cpp")
    status=runCommand("g++ {} -o {} -O2".format(code,code[:-4]))
    if status.status!=OK:
        report("Compile Error:\n"+status.message)
    else:
        code=code[:-4]
        moveOutFromSandbox(code,"code")
        init()
        code=moveIntoSandbox("temp/code")
        status=runCommand(
                "./{}".format(code),
                stdin=open("user/input","r"),
                stdout=open("user/output","w"))
        out=open("user/output","r").read(10245)
        if(len(out)>10240):
            out=out[:10240]+'...'
        report(
                "{}\nTime: {} ms Memory: {} KB\n=================\n{}".format(judgeStatus[status.status],status.time,status.memory,out)
                )

