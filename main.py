import os

from pm4py.objects.log.obj import EventLog, EventStream
import  numpy as np
from scipy import stats
from pm4py.algo.discovery.footprints import algorithm as footprints_discovery

from scoreFunction import driftTimeScore_sudden


def transitive_closure(directlyRelations,activitiesName):
    n=len(activitiesName)
    Matrix=np.zeros((n,n))
    for relation in directlyRelations:
        Matrix[activitiesName.index(relation[0])][activitiesName.index(relation[1])]=1
    res=set()
    # print(Matrix)

    # 逻辑加（或运算）
    def logicAdd(a, b):
        if a == 0 and b == 0:
            return 0
        else:
            return 1

    # Walshall算法求传递闭包
    for column in range(n):  # 从第一列到第n列[range（）函数从0到n-1但是不影响算法]
        for row in range(n):  # 从第一行到第n行[range（）函数从0到n-1但是不影响算法]
            # row的for循环在column的for循环的下面，在行数确定时，对相应列的所有元素进行遍历，变化的是row行数
            if int(Matrix[row][column]) == 1:  # 判断第row行第column行的元素是否为1
                for i in range(n):  # 计算n次
                    Matrix[row][i] = logicAdd(int(Matrix[row][i]), int(Matrix[column][i]))
    # 将该行的所有元素与对应行的元素进行逻辑加运算，此处，因为行数与列数是相同的，所以用column固定值表示

    for row in range(n):
        for column in range(n):
            if Matrix[row][column]:
                res.add((activitiesName[row],activitiesName[column]))
    return res



def get_RunRelation(trace,parallel):
    activitiesName=list(set([event['concept:name'] for event in trace]))
    directlyRelations=set([(trace[i]['concept:name'],trace[i+1]['concept:name']) for i in range(len(trace)-1)])
    closure= transitive_closure(directlyRelations,activitiesName)
    run=closure-parallel
    return run

def get_RunRelationfreq(log):
    fp_log = footprints_discovery.apply(log, variant=footprints_discovery.Variants.ENTIRE_EVENT_LOG)
    parallel=fp_log['parallel']
    res={}
    for trace in log:
        run=get_RunRelation(trace, parallel)

        run=list(run)
        run.sort()
        run=tuple(run)
        if run in res :
            res[run]+=1
        else:
            res[run]=1
    return res

def adwin(newref,newdet,windowsize):
    evolution_ratio=len(newdet)/len(newref)
    newwindowsize=windowsize*evolution_ratio
    return newwindowsize


def detect(logpath,windowsize=100):
    from pm4py.objects.log.importer.xes import importer as xes_importer



    log = xes_importer.apply(logpath)
    if len(log)<=2*windowsize:
        return None
    dLen=0
    dTrace=None
    phi=1
    detectTime=[]
    driftTime=[]
    # ref=get_RunRelationfreq(EventLog(log[:windowsize]))
    # det=get_RunRelationfreq(EventLog(log[windowsize:2*windowsize]))
    i=2*windowsize
    while i <len(log):
        if i>=2*windowsize:
            # print("i " + str(i))
            # print("w "+str(windowsize))
            newref=get_RunRelationfreq(EventLog(log[i-2*windowsize:i-windowsize]))
            newdet=get_RunRelationfreq(EventLog(log[i-windowsize:i]))
            # print("ref "+str(len(newref)))
            # print("det "+str(len(newdet)))
            # windowsize=int(adwin(newref,newdet,windowsize))

            keyset=set(newref.keys()).union(set(newdet.keys()))
            matrix= [[],[]]
            for key in keyset:
                if key in newref.keys():
                    matrix[0].append(newref[key])
                else:
                    matrix[0].append(0)
                if key in newdet.keys():
                    matrix[1].append(newdet[key])
                else:
                    matrix[1].append(0)
            p_val=stats.chi2_contingency(observed=matrix)[1]
            # print(p_val)
            if p_val < 0.05:
                dLen+=1
                if dTrace is None:
                    dTrace=i
                    phi=windowsize/3
                if dLen>=phi:
                    # print("drift : "+str(dTrace)  + "now : "+str(i))
                    detectTime.append(i)
                    driftTime.append(dTrace)
                    i = dTrace+2*windowsize
                    dTrace = None
                    dLen = 0
                    phi = 1

            else:
                dTrace=None
                dLen=0
                phi=1
        i+=1
    return (driftTime,detectTime)


if __name__ == '__main__':
    from pm4py.objects.log.importer.xes import importer as xes_importer
    from pm4py.algo.discovery.footprints import algorithm as footprints_discovery

    dir='OIR'
    # logPath = os.path.join(r'C:\Users\75652\PycharmProjects\conceptDriftDetection', 'data', 'Loanlogs', dir,
    #                        'recurring_sudden_noise' + str(0.0) + '_' + str(
    #                            250) + '-10_' + dir + '.xes')
    drift_timeLIST,det=detect('Receipt phase of an environmental permit application process (‘WABO’), CoSeLoG project.xes',125)
    print( drift_timeLIST,det)
    truedriftTimeList = [250 * i for i in range(1, 10)]
    precision, recall, fScore, meanDelay = driftTimeScore_sudden(truedriftTimeList, drift_timeLIST, det, 15)
    print( precision, recall, fScore, meanDelay)

    # runFreq=get_RunRelationfreq(log)
    # for k ,v in runFreq.items():
    #     print(v)