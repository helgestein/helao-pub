import numpy
import json
import time
import copy
import math

product = lambda x,y: numpy.dot(x/numpy.amax(x),y/numpy.amax(y)) if x.tolist() != numpy.zeros(len(x)).tolist() and y.tolist() != numpy.zeros(len(y)).tolist() else 0

def autocorrelation(i,j,A):
    tot = 0
    print('correlating '+str(i)+' '+str(j))
    B = numpy.roll(A,(i,j),(0,1))
    for k in range(len(A)):
        for l in range(len(A[0])):
            tot += product(A[k][l],B[k][l])
    return tot

def norm(x,y,n,m):
    d0 = abs(x[0]-y[0])
    d0 = min(d0,n-d0)
    d1 = abs(x[1]-y[1])
    d1 = min(d1,m-d1)
    return math.sqrt(d0**2+d1**2)

def find_peaks_wrap(A,r):
    #r is radius around center point to check. i think i will default to 5
    xpeaks = []
    n = len(A)
    m = len(A[0])
    for i in range(n):
        j=0
        while j < m:
            start,end = [m-2*r-1-j,m-j]
            if start < 0 and end >= 0:
                sublist = numpy.append(A[i][start:],A[i][:end])
            else:
                sublist = A[i][start:end]
            peak = numpy.argmax(sublist)
            if peak > r:
                j += 2*r + 1 - peak
            elif peak == r:
                xpeaks.append([i,(m-j-r-1)%m])
                j += r + 1
            else:
                j += r - peak
    B = numpy.transpose(A)
    peaks = []
    for peak in xpeaks:            
        start,end = [peak[0]-r,peak[0]+r+1]
        if end > n:
            start,end = start-n,end-n
        if start < 0 and end >= 0:
            sublist = numpy.append(B[peak[1]][start:],B[peak[1]][:end])
        else:
            sublist = B[peak[1]][start:end]
        if numpy.argmax(sublist) == r:
            peaks.append(peak)
    i = 0
    while i < len(peaks)-1:
        j = i+1
        while j in range(i+1,len(peaks)):
            if norm(peaks[i],peaks[j],n,m) <= r:
                inti,intj = A[peaks[i][0]][peaks[i][1]],A[peaks[j][0]][peaks[j][1]]
                if inti > intj:
                    peaks = numpy.delete(peaks,j,axis=0)
                    j -= 1
                if inti < intj:
                    peaks = numpy.delete(peaks,i,axis=0)
                    i,j = i-1,len(peaks)
            j += 1
        i += 1
    return peaks

def correlation(i,j,A,B):
    tot = 0
    points = len(B)*len(B[0])
    print('correlating '+str(i)+' '+str(j))
    for k in range(len(B)):
        for l in range(len(B[0])):
            if k+i >= 0 and k+i < len(A) and l+j >= 0 and l+j < len(A[0]):
                tot += product(A[k+i][l+j],B[k][l])
            else:
                points -= 1
    print([tot,points])
    return tot/points if points != 0 else 0

def circlematrix(d,h,l,c):
    #d is circle diameter
    #h is square matrix size
    #l is length of color vector
    #c is index of circle color in color vector, so range is 0 to l-1
    if h < d or h-d%2 == 1:
        raise ValueError
    circle = numpy.array([[[1 if k == c and j >= (h-d)/2 and j < (h+d)/2 and i >= (h-d)/2 and i < (h+d)/2 else 0 for k in range(l)] for j in range(h)] for i in range(h)])
    return circle

def find_peaks(A,r):
    xpeaks = []
    n = len(A)
    m = len(A[0])
    for i in range(n):
        j = 0
        while j < m-2*r:
            sublist = A[i][j:j+2*r+1]
            peak = numpy.argmax(sublist)
            if peak + j < r and sublist[peak] >= numpy.amax(A[i][:2*r+1]) or peak == r:
                xpeaks.append([i,peak+j])
                j += peak + 1
            elif peak > r:
                j += peak - r
            else:
                j += peak + 1
    B = numpy.transpose(A)
    peaks = []
    for peak in xpeaks: 
        sublist = B[peak[1]][max(0,peak[0]-r):min(n,peak[0]+r+1)]
        if numpy.argmax(sublist) == r:
            peaks.append(peak)
    i = 0
    while i < len(peaks)-1:
        j = i+1
        inti = A[peaks[i][0]][peaks[i][1]]
        if inti == 0:
            peaks = numpy.delete(peaks,i,axis=0)
            i,j = i-1,len(peaks)
        while j < len(peaks):
            intj = A[peaks[j][0]][peaks[j][1]]
            if intj == 0:
                peaks = numpy.delete(peaks,j,axis=0)
                j -= 1
            if math.sqrt((peaks[i][0]-peaks[j][0])**2+(peaks[i][1]-peaks[j][1])**2) < r:
                if inti > intj:
                    peaks = numpy.delete(peaks,j,axis=0)
                    j -= 1
                if inti < intj:
                    peaks = numpy.delete(peaks,i,axis=0)
                    i,j = i-1,len(peaks)
                if inti == 0 and intj == 0:
                    peaks = numpy.delete(peaks,j,axis=0)
                    peaks = numpy.delete(peaks,i,axis=0)
                    i,j = i-1,len(peaks)
            j += 1
        i += 1
    return peaks


def find_peaks_min(A,r):
    xpeaks = []
    n = len(A)
    m = len(A[0])
    for i in range(n):
        j = 0
        while j < m-2*r:
            sublist = A[i][j:j+2*r+1]
            peak = numpy.argmin(sublist)
            if peak + j < r and sublist[peak] >= numpy.amin(A[i][:2*r+1]) or peak == r:
                xpeaks.append([i,peak+j])
                j += peak + 1
            elif peak > r:
                j += peak - r
            else:
                j += peak + 1
    B = numpy.transpose(A)
    peaks = []
    for peak in xpeaks: 
        sublist = B[peak[1]][max(0,peak[0]-r):min(n,peak[0]+r+1)]
        if numpy.argmin(sublist) == r:
            peaks.append(peak)
    i = 0
    while i < len(peaks)-1:
        j = i+1
        inti = A[peaks[i][0]][peaks[i][1]]
        if inti == 0:
            peaks = numpy.delete(peaks,i,axis=0)
            i,j = i-1,len(peaks)
        while j < len(peaks):
            intj = A[peaks[j][0]][peaks[j][1]]
            if intj == 0:
                peaks = numpy.delete(peaks,j,axis=0)
                j -= 1
            if math.sqrt((peaks[i][0]-peaks[j][0])**2+(peaks[i][1]-peaks[j][1])**2) < r:
                if inti < intj:
                    peaks = numpy.delete(peaks,j,axis=0)
                    j -= 1
                if inti > intj:
                    peaks = numpy.delete(peaks,i,axis=0)
                    i,j = i-1,len(peaks)
                if inti == 0 and intj == 0:
                    peaks = numpy.delete(peaks,j,axis=0)
                    peaks = numpy.delete(peaks,i,axis=0)
                    i,j = i-1,len(peaks)
            j += 1
        i += 1
    return peaks


if __name__ == "__main__":
    
    with open('C:/Users/jkflowers/Downloads/Hgridmini.json','r') as infile:
        hgrid = json.load(infile)
    
    d = .1
    dx,dy = (numpy.array(hgrid[-1][0]) - numpy.array(hgrid[0][0]))/d + 1
    dx,dy = int(dx),int(dy)
    hmatrix = numpy.transpose(numpy.reshape(numpy.array([i[1] for i in hgrid]),(dx,dy,3)),(1,0,2))
    t0 = time.time()
    #scalegrid = [[[i*d,j*d],autocorrelation(i,j,hmatrix)] for i in range(dy) for j in range(dx)]
    #print('runtime in seconds: '+str(time.time()-t0))
    
    #with open('C:/Users/Operator/Desktop/scalegrid.json','w') as outfile:
    #    json.dump(scalegrid,outfile)

    #with open('C:/Users/Operator/Desktop/scalegrid.json','r') as infile:
    #    scalegrid = json.load(infile)
    
    #scalematrix = numpy.array([i[1] for i in scalegrid]).reshape(dy,dx)
    #print(find_peaks_wrap(scalematrix,5))
    
    #circle = circlematrix(11,15,3,2)
    circle = circlematrix(11,11,3,0)
    circleconvgrid = [[[(i+(len(circle)-1)/2)*d,(j+(len(circle)-1)/2)*d],correlation(i,j,hmatrix,circle)] for i in range(dy-len(circle)) for j in range(dx-len(circle))]
    print('runtime in seconds: '+str(time.time()-t0))
    with open('C:/Users/jkflowers/Desktop/circleconvgridd.json','w') as outfile:
        json.dump(circleconvgrid,outfile)

    #with open('C:/Users/jkflowers/Downloads/circleconvgrid.json','r') as infile:
    #    circleconvgrid = json.load(infile)
    circleconvmatrix = numpy.array([i[1] for i in circleconvgrid]).reshape(dy-len(circle),dx-len(circle))
    points = find_peaks_min(circleconvmatrix,3)
    print(points)
    pointsgrid = [[i+(len(circle)-1)/2,j+(len(circle)-1)/2] for i,j in points]
    print(pointsgrid)


