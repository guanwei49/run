###固定noise为0.045，生成4个文件分别为长度为250，500，750，1000时检查结果。变化lag period



import multiprocessing
import os
import traceback
from pathlib import Path
import random

import pandas as pd
from pm4py.objects.log.obj import EventLog
from pm4py.objects.petri_net.importer import importer as pnml_importer
import json
from pm4py.objects.log.importer.xes import importer as xes_importer
from sklearn.ensemble import IsolationForest
from concurrent.futures import ProcessPoolExecutor, wait


from main import detect
from scoreFunction import  driftTimeScore_sudden

ROOT_DIR = Path(__file__).parent
noisepercent=0.0
parameter='lag_period'
def helper(dir,basenetPath,scoreDatas,lock):
    for segmentSize in range(250, 1001, 250):
        logPath = os.path.join(r'C:\Users\75652\PycharmProjects\conceptDriftDetection', 'data', 'Loanlogs', dir,
                               'recurring_sudden_noise' + str(noisepercent) + '_' + str(
                                   segmentSize) + '-10_' + dir + '.xes')

        for lag_period in range(5, 56, 5):
            try:
                drift_timeLIST,det=detect(logPath)
                truedriftTimeList = [segmentSize * i for i in range(1, 10)]
                precision, recall, fScore,meanDelay = driftTimeScore_sudden(truedriftTimeList, drift_timeLIST,det,lag_period)
            except Exception as e:
                errorTrace = traceback.format_exc()
                print(errorTrace)
                print("error log "+str(segmentSize)+"_"+dir)
                precision=0
                recall=0
                fScore=0
                meanDelay=0
            print(dir + '_segmentSize_' + str(segmentSize) + "lag_period" + str(lag_period) + " : " + str(precision) + " ; " + str(
                recall) + " ; " + str(fScore) )
            lock.acquire()  # 互斥锁上锁
            scoredict = scoreDatas[segmentSize]
            recalldict = scoredict['recall_' + str(lag_period)]
            precisiondict = scoredict['precision_' + str(lag_period)]
            FScoredict = scoredict['FScore_' + str(lag_period)]
            MeanDelaydict = scoredict['MeanDelay_' + str(lag_period)]
            recalldict[dir] = recall
            precisiondict[dir] = precision
            FScoredict[dir] = fScore
            MeanDelaydict[dir] = meanDelay
            scoreDatas[segmentSize] = scoredict
            lock.release()  # 互斥锁解锁

if __name__ == '__main__':
    mgr = multiprocessing.Manager()
    scoreDatas = mgr.dict()
    lock = mgr.Lock()

    for segmentSize in range(250, 1001, 250):
        newdict= {}
        for lag_period in range(5, 56, 5):

            newdict['recall_' + str(lag_period)]={}
            newdict['precision_' + str(lag_period)] = {}
            newdict['FScore_' + str(lag_period)] = {}
            newdict['MeanDelay_' + str(lag_period)] = {}
        scoreDatas[segmentSize] =newdict
    print(scoreDatas)
    with ProcessPoolExecutor(20) as processPool:
        jobs = []
        basenetPath = os.path.join(r'C:\Users\75652\PycharmProjects\conceptDriftDetection', 'data', 'Loanlogs', 'Loan_baseline_petriNet.pnml')
        logsrootpath = os.path.join(r'C:\Users\75652\PycharmProjects\conceptDriftDetection', 'data','Loanlogs')
        logsdir = os.listdir(logsrootpath)
        for dir in logsdir:
            dirpath = os.path.join(logsrootpath, dir)
            if os.path.isdir(dirpath):
                jobs.append(processPool.submit(helper,dir, basenetPath, scoreDatas,lock))

        wait(jobs)
    scoreDatas=dict(scoreDatas)
    for k , v in scoreDatas.items():
        for type,dir2score in v.items():
            itmes = list(dir2score.items())
            itmes.sort()
            dir2score = dict(itmes)
            v[type]=dir2score
        print(k)
        print(v)
        df = pd.DataFrame(v)
        respath = os.path.join(ROOT_DIR, 'Loan_res','driftTime_noise'+str(noisepercent)+'_segmentSize' + str(k) +'_'+ parameter+'.csv')
        df.to_csv(respath)