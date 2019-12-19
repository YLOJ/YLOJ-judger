#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'QAQ AutoMaton'
# lang=["C++"]
import yaml,sys,json
from oj import *
acm_mode=len(sys.argv)>2 and sys.argv[2]=="acm"
default_score=0
RunCommand=["./{}"]
init()
with open("data/config.yml") as f: 
    config=yaml.load(f,Loader=yaml.SafeLoader)
type=config.get("type",0)
has_token=False
if type==1:
    if "token" in config:
        has_token=True
        token=config['token']

with open("user/lang") as f: 
    lang=int(f.read())
def compileCode():
    init()
    global lang
    if lang==0:
        code=moveIntoSandbox("user/code.cpp")
        s=runCommand('g++ {} -E | grep "pragma GCC optimize"'.format(code,code[:-4]),stdout=subprocess.PIPE)
        if s.status==OK:
            report(result=JF,judge_info="拒绝评测")
        global type 
        if type==0:
            status=runCommand("g++ {} -o {} -O2".format(code,code[:-4]))
        elif type==1:
            grader=moveIntoSandbox("data/grader.cpp")
            header=config.get("header")
            moveIntoSandbox("data/{}".format(header),newName=header)
            status=runCommand("g++ {} {} -o {} -O2".format(code,grader,code[:-4]))       
    if(status.status==OK):
        moveOutFromSandbox(code[:-4],"code")
    elif(status.status==TLE):
        report(result=CTLE)
    else:
        report(result=CE,judge_info=status.message)

def compileSpj():
    global checkerType
    init()
    if(checkerType is None): 
        if not os.path.isfile('data/chk.cpp'):
            report(DE,judge_info="Checker Not Found")
        moveIntoSandbox("data/chk.cpp",newName="chk.cpp")
    else:
        if not os.path.isfile("builtin/{}.cpp".format(checkerType)):
            report(DE,judge_info="Checker Not Found")
        moveIntoSandbox("builtin/{}.cpp".format(checkerType),newName="chk.cpp")
    moveIntoSandbox("testlib.h",newName="testlib.h")
    status=runCommand("g++ chk.cpp -o chk -O2")
    if(status.status==OK):
        moveOutFromSandbox("chk")
    else:
        report(score=0,result=SE,judge_info=judgeStatus[status.status]+'\n'+status.message)

def runSpecialJudge(Input,Output,Answer,dataid):
    init()
    global has_token

    if has_token:
        global token
        with open(Output,"r") as f:
            s=f.readlines()
        for i in range(len(s)):
            if(s[i][-1]=='\n'):
                s[i]=s[i][:-1]
        if s[0]!=token:
            return WA,0,"No Response"
        else:
            with open(Output,"w") as f:
                f.write('\n'.join(s[1:]))
    Input=moveIntoSandbox(Input)
    Output=moveIntoSandbox(Output)
    Answer=moveIntoSandbox(Answer)
    spj=moveIntoSandbox("temp/chk")
    result_file=randomString()
    status=runCommand("./{} {} {} {} {}".format(spj,Input,Output,Answer,result_file),noFork=True)
    with open("{}/tmp/{}".format(pathOfSandbox,result_file)) as f:
        message=f.read()
    if status.code==0:
        # AC
        return AC,100,"ok "+message
    elif status.code==1 or status.code==4 or status.code==5:
        # WA
        return WA,0,"wrong answer "+message 
    elif status.code==2 or status.code==8:
        # PE
        return PE,0,"wrong answer "+message 
    elif status.code==3:
        # JF
        return JF,0,message
    elif status.code==7:
        # PC
        score=int(float(message.split(' ')[0])*100+1e-9)
        return PC,score,"points "+message
    else:
        # PC
        return PC,status.code-16,"points "+message

def runProgram(Input,Answer,dataid):
    global inputFile,outputFile,lang,timeLimit,memoryLimit
    init()
    if not os.path.exists(Input) :
        report(result=DE,judge_info='file '+Input+' not found')
    if not os.path.exists(Answer):
        report(result=DE,judge_info='file '+Answer+' not found')
    if not(inputFile is None):
        moveIntoSandbox(Input,inputFile)
    Output="temp/output"
    code=moveIntoSandbox("temp/code")
    status=runCommand(RunCommand[lang].format(code),
        timeLimit=timeLimit,memoryLimit=memoryLimit,
        stdin=open(Input,"r") if inputFile is None else None,
        stdout=open(Output,"w") if outputFile is None else None,
        noFork=True
        )
    if status.status==OK:
        if(not (outputFile is None)):
            moveOutFromSandbox(outputFile,"output")
        status.status,status.score,status.message=runSpecialJudge(Input,Output,Answer,dataid)
    return status 
def toList(status):
    return [status.status,status.time,status.memory,status.code,status.message,status.score]

totalScore=0
totalTime=0
maxMemory=0
try:
    result=AC
    reportCur(result=CP,score="-1")
    sameTL=bool(config.get("time_limit_same",True))
    sameML=bool(config.get("memory_limit_same",True))
    if sameTL :
        timeLimit=int(config.get("time_limit",1000))
        if timeLimit>20000:
            report(result=DE,judge_info="time limit is too huge")
    if sameML :
        memoryLimit=config.get("memory_limit",256000)
        if memoryLimit>1024000:
            report(result=DE,judge_info="memory limit is too huge")
    subtaskNum=config.get("subtask_num",0)
    if type==0:
        inputFile=config.get("input_file",None)
        outputFile=config.get("output_file",None)
    else:
        inputFile=None
        outputFile=None
    checkerType=config.get('checker',None)
    compileSpj()
    compileCode()
    subScore=[0]*(subtaskNum+1)
    info=[]
    acm_result=""
    for subId in range(1,subtaskNum+1):
        sub=config.get("subtask{}".format(subId),{})
        if acm_mode:
            score=0
            sub['score']=100
            sub['type']='pass'
            if subId>1:
                sub['dependency']=[subId-1]
        Full=sub.get("score",0)
        Type=sub.get("type","sum") 
        if not sameTL:
            timeLimit=int(sub.get("time_limit",1000))
            if timeLimit>20000:
                report(result=DE,judge_info="time limit of subtask{} is too huge".format(subId))
        if not sameML:
            memoryLimit=sub.get("memory_limit",256000)
            if memoryLimit>1024000:
                report(result=DE,judge_info="memory limit of subtask {} is too huge".format(subId))
        subScore[subId]=100 if (Type=="min" or Type=="pass") else 0
        if Type=="min" :
            dependency=sub.get("dependency",[])
            for Id in dependency:
                subScore[subId]=min(subScore[subId],subScore[Id])
        elif Type=="pass":
            dependency=sub.get("dependency",[])
            for Id in dependency:
                if subScore[Id]<100:
                    subScore[subId]=0
        dataNum=sub.get("data_num",0)
        subInfo=[]
        if (Type=="min" or Type=="pass") and subScore[subId]==0:
            subInfo.append([SKIP,0])
        else:
            subInfo.append([AC,0])
            if acm_mode:
                reportCur(result=RN)
            for dataId in range(1,dataNum+1):
                if not acm_mode:
                    reportCur(result=RN,data_id="{}.{}".format(subId,dataId),
                    score=totalScore+(subScore[subId]*Full//100 if Type=="min" else subScore[subId]*Full//100//dataNum),
                    time=totalTime,
                    memory=maxMemory)
                if (Type=="min" or Type=="pass") and subScore[subId]==0:
                    break
                dataStatus=runProgram("data/{}/data{}.in".format(subId,dataId),"data/{}/data{}.ans".format(subId,dataId),"{}.{}".format(subId,dataId))
                totalTime+=dataStatus.time
                maxMemory=max(maxMemory,dataStatus.memory)
                if dataStatus.status!=AC:
                    if result==AC:
                        result=dataStatus.status
                    if subInfo[0][0]==AC:
                        subInfo[0][0]=dataStatus.status
                if Type=="pass":
                    if dataStatus.status!=AC:
                        subScore[subId]=0
                elif Type=="min":
                    subScore[subId]=min(subScore[subId],dataStatus.score)
                else:
                    subScore[subId]+dataStatus.score
                subInfo.append(toList(dataStatus))
            subtaskScore=Full*subScore[subId]//100
            if Type=="sum":
                subtaskScore//=dataNum
            totalScore+=subtaskScore
            subInfo[0][1]=subtaskScore

        dataNum=len(subInfo)
        status=[""]*(dataNum)
        info.append(subInfo)
    report(result=result,
    score=totalScore,
    time=totalTime,
    memory=maxMemory,
    judge_info=json.dumps(info))
except Exception as e: 
    print(e)
    report(score=0,result=JF,judge_info=str(e))
