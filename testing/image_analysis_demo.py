import numpy
import json
import time

product = lambda x,y: numpy.dot(x/numpy.amax(x),y/numpy.amax(y))

displaced = lambda i,j,A: numpy.roll(A,(i,j),(0,1))

def autocorrelation(i,j,A):
    tot = 0
    print('correlating '+str(i)+' '+str(j))
    for k in range(len(A)):
        for l in range(len(A[0])):
            #print(A[k][l].tolist())
            #print(displaced(i,j,A)[k][l].tolist())
            tot += product(A[k][l],displaced(i,j,A)[k][l])
    return tot

if __name__ == "__main__":
    
    with open('C:/Users/Operator/Desktop/Hgridmini.json','r') as infile:
        hgrid = json.load(infile)
    
    d = .1
    dx,dy = (numpy.array(hgrid[-1][0]) - numpy.array(hgrid[0][0]))/d + 1
    dx,dy = int(dx),int(dy)
    hmatrix = numpy.transpose(numpy.reshape(numpy.array([i[1] for i in hgrid]),(dx,dy,3)),(1,0,2))
    t0 = time.time()
    scalegrid = [autocorrelation(i,j,hmatrix) for i in range(dy) for j in range(dx)]
    print('runtime in seconds: '+str(time.time()-t0))
    with open('C:/Users/Operator/Desktop/scalegrid.json','w') as outfile:
        json.dump(scalegrid,outfile)
    



