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
if ( not "config" in config.keys() ) or ( not "testdata" in config.keys() ):
    report(DE,judge_info="Invalid Config File")
testdata=config['testdata']
config=config['config']
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
        if type==0 or type==2:
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
    global checkerType,type
    if type==2:
        if not os.path.isfile('data/interactor.cpp'):
            report(DE,judge_info="Interactor Not Found")
        code=moveIntoSandbox("data/interactor.cpp")
        moveIntoSandbox("testlib.h",newName="testlib.h")
        status=runCommand("g++ {} -o {} -O2".format(code,code[:-4]))
        if(status.status==OK):
            moveOutFromSandbox(code[:-4],"interactor")
        else:
            report(score=0,result=SE,judge_info=status.message)
        return
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
        report(score=0,result=SE,judge_info=status.message)

def runSpecialJudge(Input,Output,Answer):
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
    moveOutFromSandbox(result_file,"result")
    return testlib_status(status.code,"temp/result")

def runProgram(Input,Answer):
    global inputFile,outputFile,lang,timeLimit,memoryLimit,type
    init()
    if type==2:
        init2()
        code=moveIntoSandbox2("temp/code")
        interactor=moveIntoSandbox("temp/interactor")
        input=moveIntoSandbox(Input)
        answer=moveIntoSandbox(Answer)
        status=run2Command("./{} {} output {} result".format(interactor,input,answer),"./{}".format(code),timeLimit=timeLimit,memoryLimit=memoryLimit,noFork=True)
        if status.status==OK:
            moveOutFromSandbox("result")
            status.status,status.score,status.message=testlib_status(status.code,"temp/result")
        return status
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
        status.status,status.score,status.message=runSpecialJudge(Input,Output,Answer)
    return status 
def toList(status):
    return [status.status,status.time,status.memory,status.code,status.message,status.score]

totalScore=0
totalTime=0
maxMemory=0
#try:
if True:
    result=AC
    reportCur(result=CP,score="-1")
    tl=config.get("time_limit",1000)
    if tl>20000:
        report(result=DE,judge_info="time limit is too huge")
    ml=config.get("memory_limit",256000)
    if ml>1024000:
        report(result=DE,judge_info="memory limit is too huge")

    subtaskNum=config.get("subtask_num",0)
    if subtaskNum<=0:
        report(result=DE,judge_info="invalid subtask_num")
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
        timeLimit=int(sub.get("time_limit",tl))
        if timeLimit>20000:
            report(result=DE,judge_info="time limit of subtask{} is too huge".format(subId))
        memoryLimit=sub.get("memory_limit",ml)
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
        if not "subtask{}".format(subId) in testdata.keys():
            report(result=DE,judge_info="no testdata in subtask {}".format(subId))
        datas=testdata['subtask{}'.format(subId)]
        if datas is None or len(datas)==0:
            report(result=DE,judge_info="no testdata in subtask {}".format(subId))
        dataNum=len(datas)
        subInfo=[]
        if (Type=="min" or Type=="pass") and subScore[subId]==0:
            subInfo.append([SKIP,0])
        else:
            subInfo.append([AC,0])
            if acm_mode:
                reportCur(result=RN)

            for dataId in range(dataNum):
                data=datas[dataId] 
                if len(data)!=2:
                    report(result=DE,judge_info="Invalid test {}.{}".format(subId,dataId+1))
                if not acm_mode:
                    reportCur(result=RN,data_id="{}.{}".format(subId,dataId+1),
                            score=totalScore+(subScore[subId]*Full//100//dataNum if Type=="sum" else subScore[subId]*Full//100),
                            time=totalTime,
                            memory=maxMemory)

                if (Type=="min" or Type=="pass") and subScore[subId]==0:
                    break
                dataStatus=runProgram('data/'+data[0],'data/'+data[1])
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
                    subScore[subId]+=dataStatus.score
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
#except Exception as e: 
#    print(e)
#    report(score=0,result=JF,judge_info=str(e))
