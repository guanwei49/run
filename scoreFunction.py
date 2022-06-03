from pm4py.statistics.variants.log import get as variants_module
from pm4py.algo.simulation.playout.petri_net import algorithm as simulator



def driftTransitionScore(trueDriftInof, predictDriftInfo):
    '''
    评价找到的petrinet中异常位置的准确度
    :param trueDriftInof:
    :param predictDriftInfo:
    :return:
    '''
    trueDriftInof = set(trueDriftInof)
    predictDriftInfo = set(predictDriftInfo)
    intersection = trueDriftInof.intersection(predictDriftInfo)
    recall = len(intersection) / len(trueDriftInof)
    precision = len(intersection) / len(predictDriftInfo)
    fScore = (2 * precision * recall) / (precision + recall)
    return (precision,recall,fScore)



def driftTimeScore_sudden(realDriftTimeList, detectedDriftTimeList, detectTimeList, errorTolerance):
    '''
    评价找到的detection time 的准确性(sudden drift) 和Mean delay
    :param realDriftTime: actual drift time
    :param detectedDriftTime:  detected drift time
    :param detectTime: the moment the drift is alerted
    :param errorTolerance:
    :return:
    '''
    TP=0
    if len(detectTimeList) == 0:
        return (0, 0, 0, 0)
    meanDelay=0
    for realDriftTime in realDriftTimeList:
        start= realDriftTime-errorTolerance
        end= realDriftTime+errorTolerance
        for detectedDriftTime,detectTime in zip(detectedDriftTimeList,detectTimeList):
            if detectedDriftTime>end:
                continue
            elif start<=detectedDriftTime:
                TP+=1
                meanDelay+=detectTime-realDriftTime
                break
    if TP==0:
        return (0, 0, 0, 0)
    else:
        meanDelay = meanDelay / TP
        recall=TP/len(realDriftTimeList)
        precision=TP/len(detectedDriftTimeList)
        fScore= (2 * precision * recall) / (precision + recall)
    return (precision,recall,fScore,meanDelay)


def driftTimeScore_gradual(realDriftTimeList,realDriftLength, detectedDriftTimeList, detectTimeList, errorTolerance):
    '''
    评价找到的detection time 的准确性(gradual drift) 和Mean delay
    :param realDriftTime: actual center of gradual drift time
    :param realDriftLength: gradual drift length
    :param detectedDriftTime:  detected drift time
    :param detectTime: the moment the drift is alerted
    :param errorTolerance:
    :return:
    '''
    TP=0
    if len(detectTimeList) == 0:
        return (0, 0, 0, 0)
    meanDelay=0
    for realDriftTime in realDriftTimeList:
        driftStart= realDriftTime-realDriftLength/2
        driftEnd=realDriftTime + realDriftLength / 2
        start=  driftStart - errorTolerance
        end= driftEnd + errorTolerance
        inrangeList = []
        for detectedDriftTime,detectTime in zip(detectedDriftTimeList,detectTimeList):
            if detectedDriftTime>end:
                continue
            elif start<=detectedDriftTime<=end:
                inrangeList.append((detectedDriftTime,detectTime))
        if len(inrangeList)==0:
            continue
        elif len(inrangeList)==1:
            TP+=1
            if inrangeList[0][0]>realDriftTime:
                meanDelay +=inrangeList[0][1]-driftEnd
            else:
                meanDelay += inrangeList[0][1] - driftStart
        elif len(inrangeList) ==2:
            if inrangeList[0][0]<realDriftTime and inrangeList[1][0]>realDriftTime: #在中心的两边
                TP += 2
                meanDelay += inrangeList[0][1] - driftStart
                meanDelay += inrangeList[1][1] - driftEnd
            elif inrangeList[0][0]<realDriftTime and inrangeList[1][0]<realDriftTime:  #在中心的同一边  ，那算一个，其中一个为误判
                TP += 1
                meanDelay += inrangeList[0][1] - driftStart
            elif inrangeList[0][0]>realDriftTime and inrangeList[1][0]>realDriftTime:  #在中心的同一边  ，那算一个，其中一个为误判
                TP += 1
                meanDelay += inrangeList[1][1] - driftEnd
        else:
            if inrangeList[0][0] < realDriftTime and inrangeList[-1][0] > realDriftTime:  # 在中心的两边
                TP += 2
                meanDelay += inrangeList[0][1] - driftStart
                meanDelay += inrangeList[1][1] - driftEnd
            elif inrangeList[0][0] < realDriftTime and inrangeList[-1][0] < realDriftTime:  # 在中心的同一边  ，那算一个，其中一个为误判
                TP += 1
                meanDelay += inrangeList[0][1] - driftStart
            elif inrangeList[0][0] > realDriftTime and inrangeList[-1][0] > realDriftTime:  # 在中心的同一边  ，那算一个，其中一个为误判
                TP += 1
                meanDelay += inrangeList[1][1] - driftEnd
    if TP==0:
        return (0, 0, 0, 0)
    else:
        meanDelay = meanDelay / TP
        recall=TP/(2*len(realDriftTimeList))
        precision=TP/len(detectedDriftTimeList)
        fScore= (2 * precision * recall) / (precision + recall)
    return (precision,recall,fScore,meanDelay)


if __name__ == '__main__':
    realDriftTimeList=[1000,2000,3000,4000]
    realDriftLength=500
    detectedDriftTimeList=[780,1200,1780,2150,2890,3200]
    detectTimeList=[781,1201,1781,2151,2891,3220]
    errorTolerance=20
    print(driftTimeScore_gradual(realDriftTimeList,realDriftLength, detectedDriftTimeList, detectTimeList, errorTolerance))