#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'QAQ AutoMaton'
# lang=["C++"]
import yaml,sys,json
from oj import *
acm_mode=len(sys.argv)>2 and sys.argv[2]=="acm"
default_score=-1 if acm_mode else 0
RunCommand=["./{}"]
init()
with open("data/config.yml") as f: 
    config=yaml.load(f,Loader=yaml.SafeLoader)
with open("user/lang") as f: 
    lang=int(f.read())
def compileCode():
    init()
    if lang==0:
        code=moveIntoSandbox("user/code.cpp")
        s=runCommand('g++ {} -E | grep "pragma GCC optimize"'.format(code,code[:-4]),stdout=subprocess.PIPE)
        if s.status==OK:
            report(result="Judgement Failed",judge_info="拒绝评测")
        status=runCommand("g++ {} -o {} -O2".format(code,code[:-4]))
    if(status.status==OK):
        moveOutFromSandbox(code[:-4],"code")
    elif(status.status==TLE):
        report(result="Compiler Time Limit Exceeded")
    else:
        report(result="Compile Error",judge_info=status.message)

def compileSpj():
    global checkerType
    init()
    if(checkerType is None): 
        if not os.path.isfile('data/chk.cpp'):
            report('Data Error',judge_info="Checker Not Found")
        moveIntoSandbox("data/chk.cpp",newName="chk.cpp")
    else:
        if not os.path.isfile("builtin/{}.cpp".format(checkerType)):
            report('Data Error',judge_info="Checker Not Found")
        moveIntoSandbox("builtin/{}.cpp".format(checkerType),newName="chk.cpp")
    moveIntoSandbox("testlib.h",newName="testlib.h")
    status=runCommand("g++ chk.cpp -o chk -O2")
    if(status.status==OK):
        moveOutFromSandbox("chk")
    elif(status.status==TLE):
        report(score=0,result="Special Judge Compiler Time Limit Exceeded")
    else:
        report(score=0,result="Special Judge Compile Error",judge_info=judgeStatus[status.status]+'\n'+status.message)

def runSpecialJudge(Input,Output,Answer,dataid):
    init()
    Input=moveIntoSandbox(Input)
    Output=moveIntoSandbox(Output)
    Answer=moveIntoSandbox(Answer)
    spj=moveIntoSandbox("temp/chk")
    status=runCommand("./{} {} {} {}".format(spj,Input,Output,Answer))
    if status.code==0:
        # AC
        return AC,100,status.message
    elif status.code==1 or status.code==4 or status.code==5:
        # WA
        return WA,0,status.message 
    elif status.code==2 or status.code==8:
        # PE
        return PE,0,status.message 
    elif status.code==3:
        # JF
        return JF,0,status.message
    elif status.code==7:
        # ???
        return JF,0,status.message
    else:
        # PC
        return PC,status.code-16,message

def runProgram(Input,Answer,dataid):
    global inputFile,outputFile,lang,timeLimit,memoryLimit
    init()
    if not os.path.exists(Input) :
        report(result='Data Error',judge_info='file '+Input+' not found')
    if not os.path.exists(Answer):
        report(result='Data Error',judge_info='file '+Answer+' not found')
    if not(inputFile is None):
        moveIntoSandbox(Input,inputFile)
    Output="temp/output"
    code=moveIntoSandbox("temp/code")
    status=runCommand(RunCommand[lang].format(code),
        timeLimit=timeLimit,memoryLimit=memoryLimit,
        stdin=open(Input,"r") if inputFile is None else None,
        stdout=open(Output,"w") if outputFile is None else None,
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
    reportCur(result="Compiling")
    timeLimit=int(config.get("time_limit",1000))
    if timeLimit>20000:
        report(result="Data Error",judge_info="time limit is too huge")
    memoryLimit=config.get("memory_limit",256000)
    if memoryLimit>1024000:
        report(result="Data Error",judge_info="memory limit is too huge")
    subtaskNum=config.get("subtask_num",0)
    inputFile=config.get("input_file",None)
    outputFile=config.get("output_file",None)
    checkerType=config.get('checker',None)
    compileSpj()
    compileCode()
    subScore=[0]*(subtaskNum+1)
    info=[]
    acm_result=""
    for subId in range(1,subtaskNum+1):
        sub=config.get("subtask{}".format(subId),{})
        Full=sub.get("score",0)
        Type=sub.get("type","sum") 
        subScore[subId]=100 if Type=="min" else 0
        if(Type=="min"):
            dependency=sub.get("dependency",[])
            for Id in dependency:
                subScore[subId]=min(subScore[subId],subScore[Id])
        dataNum=sub.get("data_num",0)
        subInfo=[[SKIP,0]]+[[SKIP,0,0,0,"",0]]*dataNum
        for dataId in range(1,dataNum+1):
            if acm_mode:
                reportCur(result="Running",
                score=-1,
            time=totalTime,
            memory=maxMemory)
            else:
                reportCur(result="Running on Test {}.{}".format(subId,dataId),
            score=totalScore+(subScore[subId]*Full//100 if Type=="min" else subScore[subId]*Full//100//dataNum),
            time=totalTime,
            memory=maxMemory)
            if Type=="min" and subScore[subId]==0:
                break
            dataStatus=runProgram("data/{}/data{}.in".format(subId,dataId),"data/{}/data{}.ans".format(subId,dataId),"{}.{}".format(subId,dataId))
            totalTime+=dataStatus.time
            maxMemory=max(maxMemory,dataStatus.memory)
            if dataStatus.status!=AC and acm_mode:
                report(score=-1,result=judgeStatus[dataStatus.status],time=totalTime,memory=maxMemory)

            subScore[subId]=min(subScore[subId],dataStatus.score) if Type=="min" else subScore[subId]+ dataStatus.score
            subInfo[dataId]=toList(dataStatus)
        subtaskScore=Full*subScore[subId]//100
        if Type=="sum":
            subtaskScore//=dataNum
        subInfo[0][0]="Accepted" if subtaskScore==Full else "Unaccepted"
        subInfo[0][1]=subtaskScore
        totalScore+=subtaskScore
        status=[""]*(dataNum+1)
        for i in range(1,dataNum+1):
            status[i]=judgeStatus[subInfo[i][0]]

        for i in range(1,dataNum+1):
            subInfo[i][0]=status[i]
        info.append(subInfo)
    if acm_mode:
        report(result="Accepted",score=-1,time=totalTime,memory=maxMemory)
    else:
        report(result="Accepted" if totalScore==100 else "Unaccepted",
        score=totalScore,
        time=totalTime,
        memory=maxMemory,
        judge_info=json.dumps(info))
except Exception as e: 
    print(e)
    report(score=0,result="Judgement Failed",judge_info=str(e))
