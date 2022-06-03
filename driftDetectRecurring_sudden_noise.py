###固定noise为0，生成4个文件分别为长度为250，500，750，1000时检查结果。变化数据集的noise



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
from scoreFunction import driftTimeScore_sudden

ROOT_DIR = Path(__file__).parent
errorTolerance=15
parameter='noise'
def helper(dir,basenetPath,scoreDatas,lock):
    for segmentSize in range(250, 1001, 250):
        for tempnoisepercent in range(0, 101, 15):
            noise = tempnoisepercent / 1000
            logPath = os.path.join(r'C:\Users\75652\PycharmProjects\conceptDriftDetection', 'data', 'Loanlogs', dir,
                                   'recurring_sudden_noise' + str(noise) + '_' + str(
                                       segmentSize) + '-10_' + dir + '.xes')
            try:
                drift_timeLIST ,det= detect(logPath)
                truedriftTimeList = [segmentSize * i for i in range(1, 10)]
                # print(truedriftTimeList)
                # print(drift_timeLIST)
                # print(detection_timeLIST)
                # print(errorTolerance)
                precision, recall, fScore, meanDelay = driftTimeScore_sudden(truedriftTimeList, drift_timeLIST, det,
                                                                             errorTolerance)
            except Exception as e:
                errorTrace = traceback.format_exc()
                print(errorTrace)
                print("error log "+str(segmentSize)+"_"+dir)
                precision, recall, fScore, meanDelay = 0, 0, 0, 0
            print(dir + '_segmentSize_' + str(segmentSize) + "noise" + str(noise) + " : " + str(
                precision) + " ; " + str(recall) + " ; " + str(fScore) )
            lock.acquire()  # 互斥锁上锁
            scoredict = scoreDatas[segmentSize]
            recalldict = scoredict['recall_' + str(noise)]
            precisiondict = scoredict['precision_' + str(noise)]
            FScoredict = scoredict['FScore_' + str(noise)]
            MeanDelaydict = scoredict['MeanDelay_' + str(noise)]
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
        for tempnoisepercent in range(0, 101, 15):
            noise = tempnoisepercent / 1000
            newdict['recall_' + str(noise)]={}
            newdict['precision_' + str(noise)] = {}
            newdict['FScore_' + str(noise)] = {}
            newdict['MeanDelay_' + str(noise)] = {}
        scoreDatas[segmentSize] =newdict
    print(scoreDatas)
    with ProcessPoolExecutor(14) as processPool:
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
        respath = os.path.join(ROOT_DIR, 'Loan_res','driftTime_segmentSize' + str(k) +'_'+ parameter+'.csv')
        df.to_csv(respath)