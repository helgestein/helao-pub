import numpy
import json
import time

product = lambda x,y: numpy.dot(x/numpy.amax(x),y/numpy.amax(y))

def autocorrelation(i,j,A):
    tot = 0
    print('correlating '+str(i)+' '+str(j))
    B = numpy.roll(A,(i,j),(0,1))
    for k in range(len(A)):
        for l in range(len(A[0])):
            tot += product(A[k][l],B[k][l])
    return tot

def find_peaks(A,r):
    #r is radius around center point to check. i think i will default to 5
    xpeaks = []
    n = len(A)
    m = len(A[0])
    for i in range(n):
        while j < m:
            j=0
            sublist[A[i][m-2*r-1-j:m-j]]
            peak = numpy.argmax(sublist)
            if peak > r:
                j += 2*r + 1 - peak
            elif peak == r:
                xpeaks.append([i,m-j-r-1%m])
                j += r + 1
            else:
                j += r - peak


if __name__ == "__main__":
    
    with open('C:/Users/Operator/Desktop/Hgridmini.json','r') as infile:
        hgrid = json.load(infile)
    
    d = .1
    dx,dy = (numpy.array(hgrid[-1][0]) - numpy.array(hgrid[0][0]))/d + 1
    dx,dy = int(dx),int(dy)
    hmatrix = numpy.transpose(numpy.reshape(numpy.array([i[1] for i in hgrid]),(dx,dy,3)),(1,0,2))
    t0 = time.time()
    scalegrid = [[[i*d,j*d],autocorrelation(i,j,hmatrix)] for i in range(dy) for j in range(dx)]
    print('runtime in seconds: '+str(time.time()-t0))

    with open('C:/Users/Operator/Desktop/scalegrid.json','w') as outfile:
        json.dump(scalegrid,outfile)
    



