import numpy
from scipy.ndimage import correlate
from math import sin,cos
from scipy.optimize import minimize
from julia import BackgroundSubtraction

def kernel(d):
    #returns a dxd matrix with value 1 for all values i,j within radius d/2 of matrix center, 0 otherwise
    return numpy.array([[1 if (i-(d+1)/2)**2+(j-(d+1)/2)**2 <= d**2/4 else 0 for i in range(d)] for j in range(d)])

def list_to_matrix(l):
    #list contains a length 3 list for each spectrum
    #index 0 is list containing x-position and y-position
    #index 2 is grayscale value or color vector, should typically be non-background share of spectrum intensity

    #matrix format stores position in indices i and j in matrix
    #currently, a rectangular grid of samples is assumed
    #i = (x-x0)/dx, j = (y-y0)/dy
    #value at i,j is grayscale value or color vector, should typically be non-background share of spectrum intensity
    xs = [i[0][0] for i in l]
    ys = [i[0][1] for i in l]
    minx = min(xs)
    miny = min(ys)
    maxx = max(xs)
    maxy = max(ys)
    dx = (maxx-minx)/len(xs)
    dy = (maxy-miny)/len(ys)
    mat = numpy.empty((round((maxx-minx)/dx),round((maxy-miny)/dy)))
    for i in l:
        mat[round((i[1]-minx)/dx)][round((i[2]-miny)/dy)] = i[1]
    return [mat,minx,miny,dx,dy]
    
def matrix_to_list(mat,x0,y0,dx,dy):
    pass

def contrast():
    pass

#take a spectral image in list format, and return local intensity maxima in that image
#currently only works for grayscale images
def peaks(l,k):
    mat = list_to_matrix(l)[0]
    return MaxDetect(correlate(mat,k))

#porting Mathematica's MaxDetect function to python, as no equivalent appears to exist in scipy or numpy
def MaxDetect(mat,r=1):
    maxes = []
    shape = numpy.shape(mat)
    for i in range(shape[0]):
        for j in range(shape[1]):
            if numpy.argmax(mat[min(i-r,0):max(i+r,shape[0]),min(0,j-r):max(j+r,shape[1])]) == numpy.array([i,j]):
                maxes.append([i,j])
    return maxes

#number that is minimized to evaluate goodness of fit for proposed sample grid
#peaks: list of peaks found experimentally
#x: displacement of grid starting point from (0,0) in image coordinate system
#theta: angle at which grid is rotated relative to image coordinate system
#a1,a2: basis vectors of grid. list_to_matrix currently doesn't work with non-rectangular basis choices
#each peak is paired with its nearest grid point if it is also the nearest peak to that grid point.
#square of distances between these pairs is summed, and divided by number of pairs
def fitness(peaks,x,theta,a1,a2):
    pairings = {}
    peaks,x,a1,a2 = map(numpy.array,[peaks,x,a1,a2])
    rot = numpy.dot(numpy.array([[cos(theta),-sin(theta)],[sin(theta),cos(theta)]]),numpy.array([[a1[0],a2[0]],[a1[1],a2[1]]]))
    for peak in peaks:
        index = numpy.round(numpy.dot(numpy.linalg.inv(rot),peak-x))
        d2 = numpy.linalg.norm(peak - x - numpy.dot(rot,index))**2
        index = tuple(index)
        if index not in pairings or d2 < pairings[index][1]:
            pairings[index] = [peak,d2]
    fit = [pair[1] for pair in pairings.values()]
    return sum(fit)/len(fit)

def optimize_lattice(peaks,a1,a2):
    fit_func = lambda x: fitness(peaks,x[:2],x[2],a1,a2)
    return minimize(fit_func,numpy.array([0,0,0]),method='nelder-mead')

def get_background(Agrid):
    A = numpy.array([i[1] for i in Agrid]).T
    k = 2
    l = .02
    x = numpy.array([i/1000 for i in range(1044)])
    return BackgroundSubtraction.mcbl(A, k, x, l)

#so next: implement the background subtraction
#function to take in a basis and a grid, or just a list of weights...
#well, it might be a lot of things, but at any rate, need a function to make the grayscale image