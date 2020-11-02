import os
import yaml
import pymysql
import time
import redis
import requests
from oj.env import *
from oj.constant import *

cmd_select = "SELECT * FROM submission WHERE `id` = {}"
r=redis.Redis(host=redishost,port=redisport,password=redispassword)
banlist=[]
try:
    banlist=open("banlist","r").readlines()
except Exception as e: 
    pass
    
for i in range(len(banlist)):
    if banlist[i][-1]=='\n':
        banlist[i]=banlist[i][:-1]
while True:
    try:
        ls=r.blpop('submission')[1].split()
        Type,sid=ls[0],ls[1]
        conn = pymysql.connect(
            host = host,
            user = user,
            password = password,
            database = database,
            charset = 'utf8'
        )
        cursor = conn.cursor(cursor = pymysql.cursors.DictCursor)

        Type=Type.decode()
        sid=int(sid)
        if Type=='test':
            cursor.execute(cmd_select.format(sid))
            sub = cursor.fetchone()
            if sub['user_name'] in banlist:
                print("BANNED!")
                continue
            if('pragma' in sub['source_code']):
                cursor.execute("""
UPDATE submission SET
`result` = {},
`score` = 0,
`judge_info` = '拒绝评测'
WHERE `id` = {}
""".format(JF,sid))
                conn.commit()
                continue
            os.system("rm -rf data user temp 2>/dev/null")
            os.system("cp -rf {}/{} data".format(data_path,sub['problem_id']))
            os.system("mkdir temp user")
            with open("user/code.cpp","w") as f:
                f.write(sub['source_code'])
            with open("user/lang","w") as f:
                f.write("0\n")
            print('start judging submission',sid)
            acm_mode=0
            if not(sub['contest_id'] is None):
                cursor.execute("select * from contest where id={}".format(sub['contest_id']))
                con= cursor.fetchone()
                acm_mode=con['rule']==2
            if acm_mode:
                os.system("python3 judger.py {} acm".format(sid))
            else:
                os.system("python3 judger.py {}".format(sid))
            print("done")
        elif Type=='customtest':
            cursor.execute("select * from custom_tests where id={}".format(sid))
            sub=cursor.fetchone()
            if sub['username'] in banlist:
                print("BANNED!")
                continue
            os.system("rm -rf user temp 2>/dev/null")
            os.system("mkdir user temp")
            with open("user/code.cpp","w") as f:
                f.write(sub['code'])
            with open("user/input","w") as f:
                f.write(str(sub['input']))
            with open("user/lang","w") as f:
                f.write("0\n")
            print('start judging customtest',sid)
            os.system("python3 custom_test.py {}".format(sid))
            print('done')

    except Exception as e:
        print (e)
