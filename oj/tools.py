#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'QAQ AutoMaton'
import sys,pymysql,signal
from .env import *
from .constant import *
import random,os,subprocess,psutil,time,requests
def init():
    os.system("rm -rf {}/tmp/*".format(pathOfSandbox))
def randomString():
    s="" 
    for i in range(20):
        s+=chr(ord('a')+random.randint(0,25))
    return s

def moveIntoSandbox(oldName,newName=None):
    if newName is None:
        newName=randomString()+os.path.splitext(oldName)[-1]
    os.system("cp {} {}/tmp/{}".format(oldName,pathOfSandbox,newName))
    return newName
class runStatus(object):
    def __init__(self,status,time=None,memory=None,code=0,message="",score=0):
        self.status=status
        self.time=time
        self.memory=memory
        self.code=code
        self.message=str(message)
        self.score=score
    def __str__(self):
        return "runStatus(status:{},time:{},memory:{},code:{},message:{})".format(self.status,self.time,self.memory,self.code,self.message)

def kill(pid):
    for i in os.popen("ps -ef"):
        if(i.split()[2]==str(pid)):
            kill(i.split()[1])
    os.system("kill {}".format(pid))

def runCommand(command,timeLimit=10000,memoryLimit=1024000,stdin=None,stdout=None,noFork=False):
    if not os.path.isdir("/sys/fs/cgroup/memory/{}".format(cgroup_name)):
        os.mkdir("/sys/fs/cgroup/memory/{}".format(cgroup_name))
    if noFork:
        if not os.path.isdir("/sys/fs/cgroup/pids/{}".format(cgroup_name)):
            os.mkdir("/sys/fs/cgroup/pids/{}".format(cgroup_name))
        with open("/sys/fs/cgroup/pids/{}/pids.max".format(cgroup_name),"w") as f:
            f.write('3')
    max_memory = 0
    time_used = 0
    with open(pathOfSandbox+"/a.sh","w") as f:
        f.write('cd tmp\nsudo -u oj '+command)
    begin_time=time.time()
    child = subprocess.Popen("chroot {} sh a.sh".format(pathOfSandbox,command).split(),stdin=stdin,stdout=stdout,stderr=subprocess.PIPE)
    with open("/sys/fs/cgroup/memory/{}/memory.usage_in_bytes".format(cgroup_name),"r") as f:
        before=int(f.read())
    with open("/sys/fs/cgroup/memory/{}/cgroup.procs".format(cgroup_name),"w") as f:
        f.write(str(child.pid)+'\n')
    if noFork:
        with open("/sys/fs/cgroup/pids/{}/cgroup.procs".format(cgroup_name),"w") as f:
            f.write(str(child.pid)+'\n')
    while child.poll() is None:
        try:
            with open("/sys/fs/cgroup/memory/{}/memory.usage_in_bytes".format(cgroup_name),"r") as f:
                memory=(int(f.read())-before)/1024
            curTime=time.time()
            time_used = int((curTime - begin_time)*1000)
            max_memory = max(max_memory, memory)
            if memory > memoryLimit:
                kill(child.pid)
                return runStatus(MLE, time_used, max_memory)
            if time_used > timeLimit:
                kill(child.pid)
                return runStatus(TLE, time_used, max_memory)
        finally:
            pass
    child.poll()
    returncode = child.returncode

    if not (returncode is None or returncode==0):
        return runStatus(RE, time_used, max_memory,returncode,message=child.stderr.read(200).decode())
    else:
        return runStatus(OK, time_used, max_memory,returncode,message=child.stderr.read(200).decode())
def moveOutFromSandbox(oldName,newName=None):
    if(newName is None):
        newName=oldName
    os.system("cp {}/tmp/{} temp/{}".format(pathOfSandbox,oldName,newName))
    return newName
def judgingMessage(message):
    pass
    # TODO
    # print("judging:",message)

def reportCur(result='',score=None,time=-1,memory=-1,judge_info=''):
    if score==None:
        score = -1 if len(sys.argv)>2 and sys.argv[2]=="acm" else 0
    db=pymysql.connect(host,user,password,database)
    cursor=db.cursor()
    sql="update submission set result='{}',score={},time_used={},memory_used={},judge_info='{}' where id={}".format(result,score,time,memory,pymysql.escape_string(judge_info),sys.argv[1])
    cursor.execute(sql)
    db.commit()
    requests.post(update_link+'/api/submission_update',{
    'token':submission_update_token,
    'id': sys.argv[1],
    'result':result,
    'score':score,
    'time':time,
    'memory':memory
        });

def report(result='',score=None,time=-1,memory=-1,judge_info=''):
    reportCur(result,score,time,memory,judge_info)
    sys.exit()
