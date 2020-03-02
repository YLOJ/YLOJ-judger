#!/usr/bin/env python3 # -*- coding: utf-8 -*-
__author__ = 'QAQ AutoMaton'
import sys,pymysql,signal
from .env import *
from .constant import *
import random,os,subprocess,psutil,time,requests
def init():
    os.system("rm -rf {}/tmp/*".format(pathOfSandbox))
def init2():
    os.system("rm -rf {}/tmp/*".format(pathOfSandbox2))
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
def moveIntoSandbox2(oldName,newName=None):
    if newName is None:
        newName=randomString()+os.path.splitext(oldName)[-1]
    os.system("cp {} {}/tmp/{}".format(oldName,pathOfSandbox2,newName))
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

def testlib_status(code,result_file):
    with open(result_file,"rb") as f:
        message=f.read().decode()
    if code==0:
        # AC
        return AC,100,"ok "+message
    elif code==1 or code==4 or code==5:
        # WA
        return WA,0,"wrong answer "+message 
    elif code==2 or code==8:
        # PE
        return PE,0,"wrong answer "+message 
    elif code==3:
        # WA 
        return WA,0,message
    elif code==7:
        # PC
        score=int(float(message.split(' ')[0])*100+1e-9)
        if score<=0:
            score=0
            return WA,score,"points "+message
        if score>=100:
            score=100
            return AC,score,"points "+message
        return PC,score,"points "+message
    else:
        # PC
        return PC,code-16,"points "+message


def kill(pid):
    for i in os.popen("ps -aef").readlines():
        if(i.split()[2]==str(pid)):
            kill(i.split()[1])
    os.system("kill -9 {}".format(pid))

def runCommand(command,timeLimit=10000,memoryLimit=1024000,stdin=None,stdout=None,noFork=False):
    if not os.path.isdir("/sys/fs/cgroup/memory/{}".format(cgroup_name)):
        os.mkdir("/sys/fs/cgroup/memory/{}".format(cgroup_name))
    if noFork:
        if not os.path.isdir("/sys/fs/cgroup/pids/{}".format(cgroup_name)):
            os.mkdir("/sys/fs/cgroup/pids/{}".format(cgroup_name))
        with open("/sys/fs/cgroup/pids/{}/pids.max".format(cgroup_name),"w") as f:
            f.write('4')
    max_memory = 0
    time_used = 0
    with open(pathOfSandbox+"/a.sh","w") as f:
        f.write('cd tmp\nsudo -u oj '+command)
    begin_time=time.time()
    child = subprocess.Popen("chroot {} sh a.sh".format(pathOfSandbox).split(),stdin=stdin,stdout=stdout,stderr=subprocess.PIPE)
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

def run2Command(command1,command2,timeLimit=10000,memoryLimit=1024000,noFork=False):
    if not os.path.isdir("/sys/fs/cgroup/memory/{}".format(cgroup_name)):
        os.mkdir("/sys/fs/cgroup/memory/{}".format(cgroup_name))
    if not os.path.isdir("/sys/fs/cgroup/memory/{}".format(cgroup_name2)):
        os.mkdir("/sys/fs/cgroup/memory/{}".format(cgroup_name2))
    if noFork:
        if not os.path.isdir("/sys/fs/cgroup/pids/{}".format(cgroup_name)):
            os.mkdir("/sys/fs/cgroup/pids/{}".format(cgroup_name))
        with open("/sys/fs/cgroup/pids/{}/pids.max".format(cgroup_name),"w") as f:
            f.write('4')
        if not os.path.isdir("/sys/fs/cgroup/pids/{}".format(cgroup_name2)):
            os.mkdir("/sys/fs/cgroup/pids/{}".format(cgroup_name2))
        with open("/sys/fs/cgroup/pids/{}/pids.max".format(cgroup_name2),"w") as f:
            f.write('4')
    max_memory1 = 0
    max_memory2 = 0
    time_used = 0
    with open(pathOfSandbox+"/a.sh","w") as f:
        f.write('cd tmp\nsudo -u oj '+command1)
    with open(pathOfSandbox2+"/a.sh","w") as f:
        f.write('cd tmp\nsudo -u oj '+command2)
    begin_time=time.time()
    child1 = subprocess.Popen("chroot {} sh a.sh".format(pathOfSandbox).split(),stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    child2 = subprocess.Popen("chroot {} sh a.sh".format(pathOfSandbox2).split(),stdin=child1.stdout,stdout=child1.stdin,stderr=subprocess.PIPE)
    with open("/sys/fs/cgroup/memory/{}/memory.usage_in_bytes".format(cgroup_name),"r") as f:
        before1=int(f.read())
    with open("/sys/fs/cgroup/memory/{}/memory.usage_in_bytes".format(cgroup_name2),"r") as f:
        before2=int(f.read())
    with open("/sys/fs/cgroup/memory/{}/cgroup.procs".format(cgroup_name),"w") as f:
        f.write(str(child1.pid)+'\n')
    with open("/sys/fs/cgroup/memory/{}/cgroup.procs".format(cgroup_name2),"w") as f:
        f.write(str(child2.pid)+'\n')
    if noFork:
        with open("/sys/fs/cgroup/pids/{}/cgroup.procs".format(cgroup_name),"w") as f:
            f.write(str(child1.pid)+'\n')
        with open("/sys/fs/cgroup/pids/{}/cgroup.procs".format(cgroup_name2),"w") as f:
            f.write(str(child2.pid)+'\n')

    while child1.poll() is None or child2.poll() is None:
        try:
            curTime=time.time()
            time_used = int((curTime - begin_time)*1000)
            if time_used > timeLimit:
                kill(child1.pid)
                kill(child2.pid)
                return runStatus(TLE, time_used, max_memory2)
            if child1.poll() is None:
                with open("/sys/fs/cgroup/memory/{}/memory.usage_in_bytes".format(cgroup_name),"r") as f:
                    memory1=(int(f.read())-before1)/1024
                if memory1 > 10240000:
                    kill(child1.pid)
                    kill(child2.pid)
                    return runStatus(RE, time_used, max_memory2, message="Interactor MLE")
            if child2.poll() is None:
                with open("/sys/fs/cgroup/memory/{}/memory.usage_in_bytes".format(cgroup_name2),"r") as f:
                    memory2=(int(f.read())-before2)/1024
                max_memory2 = max(max_memory2, memory2)
                if memory2 > memoryLimit:
                    kill(child1.pid)
                    kill(child2.pid)
                    return runStatus(MLE, time_used, max_memory2)
            else:
                if not (child2.returncode is None or child2.returncode==0):
                    return runStatus(RE, time_used, max_memory2,child2.returncode,message=child2.stderr.read(200).decode())
        finally:
            pass
    child1.poll()
    child2.poll()

    if not (child2.returncode is None or child2.returncode==0):
        return runStatus(RE, time_used, max_memory2,child2.returncode,message=child2.stderr.read(200).decode())
    else:
        return runStatus(OK, time_used, max_memory2, child1.returncode)


def moveOutFromSandbox(oldName,newName=None):
    if(newName is None):
        newName=oldName
    if os.path.exists("{}/tmp/{}".format(pathOfSandbox,oldName)):
        os.system("cp {}/tmp/{} temp/{}".format(pathOfSandbox,oldName,newName))
    else:
        with open("temp/{}".format(newName),"w") as f:
            pass
    return newName

def moveOutFromSandbox2(oldName,newName=None):
    if(newName is None):
        newName=oldName
    if os.path.exists("{}/tmp/{}".format(pathOfSandbox2,oldName)):
        os.system("cp {}/tmp/{} temp/{}".format(pathOfSandbox2,oldName,newName))
    else:
        with open("temp/{}".format(newName),"w") as f:
            pass
    return newName

def reportCur(result=0,score=0,time=-1,memory=-1,judge_info='',data_id=""):
    db=pymysql.connect(host,user,password,database)
    cursor=db.cursor()
    sql="update submission set data_id='{}',result={},score={},time_used={},memory_used={},judge_info='{}' where id={}".format(data_id,result,score,time,memory,pymysql.escape_string(judge_info),sys.argv[1])
    cursor.execute(sql)
    db.commit()
    requests.post(update_link+'/api/submission_update',{
    'token':submission_update_token,
    'id': sys.argv[1],
    'result':result,
    'data_id':data_id,
    'score':score,
    'time':time,
    'memory':memory
        });

def report(result=0,score=0,time=-1,memory=-1,judge_info='',data_id=""):
    reportCur(result,score,time,memory,judge_info,data_id)
    sys.exit()
