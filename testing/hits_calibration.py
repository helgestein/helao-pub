from math import sin,cos,ceil,floor,pi
import os
import time
from copy import copy
import json
import numpy
from scipy.ndimage import correlate
from scipy.optimize import minimize
from sklearn.decomposition import NMF
from PIL import Image
import PySimpleGUI
from julia import BackgroundSubtraction
import asyncio


def kernel(d):
    #returns a dxd matrix with value 1 for all values i,j within radius d/2 of matrix center, 0 otherwise
    return numpy.array([[1 if (i-(d+1)/2)**2+(j-(d+1)/2)**2 <= d**2/4 else 0 for i in range(d)] for j in range(d)])

def list_to_matrix(l):
    #list contains a length 2 list for each spectrum
    #index 0 is list containing x-position and y-position
    #index 1 is grayscale value or color vector, should typically be non-background share of spectrum intensity

    #matrix format stores position in indices i and j in matrix
    #currently, a rectangular grid of samples is assumed
    #i = (x-x0)/dx, j = (y-y0)/dy
    #value at i,j is grayscale value or color vector, should typically be non-background share of spectrum intensity
    xs = list(dict.fromkeys([i[0][0] for i in l]))
    ys = list(dict.fromkeys([i[0][1] for i in l]))
    minx = min(xs)
    miny = min(ys)
    maxx = max(xs)
    maxy = max(ys)
    dx = (maxx-minx)/(len(xs)-1)
    dy = (maxy-miny)/(len(ys)-1)
    mat = [[None for i in range(round((maxy-miny)/dy)+1)] for j in range(round((maxx-minx)/dx)+1)]
    #print(f"minx: {minx}, maxx: {maxx}, miny: {miny}, maxy: {maxy}, shape: {mat.shape}")
    for i in l:
        mat[round((i[0][0]-minx)/dx)][round((i[0][1]-miny)/dy)] = i[1]
    return (numpy.array(mat),minx,miny,dx,dy)
    
def matrix_to_list(mat,x0=0,y0=0,dx=1,dy=1):
    return [[[x0+i*dx,y0+j*dy],mat[i,j]] for i in range(mat.shape[0]) for j in range(mat.shape[1])]

#take a greyscale image as a matrix and maximize contrast (darkest value to pure black and lightest to pure white)
#def contrast(mat):
#    matmax = numpy.amax(mat)
#    matmin = numpy.amin(mat)
#    return (mat - matmin)/(matmax-matmin)
#take a list of greyscale values tied to position and maximize contrast (darkest value to pure black and lightest to pure white)
def contrast(l):
    data = [i[1] for i in l]
    lmax = max(data)
    lmin = min(data)
    return [[i[0],(i[1]-lmin)/(lmax-lmin)] for i in l]

#take a spectral image in list format, and return local intensity maxima in that image
#currently only works for grayscale images
def list_correlate(l,k):
    mat,x0,y0,dx,dy = list_to_matrix(l)
    cor = correlate(mat,k)
    return (matrix_to_list(cor,x0,y0,dx,dy),MaxDetect(cor))

#porting Mathematica's MaxDetect function to python, as no equivalent appears to exist in scipy or numpy
def MaxDetect(mat,r=1):
    maxes = []
    shape = numpy.shape(mat)
    for i in range(shape[0]):
        for j in range(shape[1]):
            minimat = mat[max(i-r,0):min(i+r+1,shape[0]),max(0,j-r):min(j+r+1,shape[1])]
            if numpy.amax(minimat) == mat[i][j]:
                maxes.append([i,j])
    return maxes

#number that is minimized to evaluate goodness of fit for proposed sample grid
#peaks: list of peaks found experimentally
#x: displacement of grid starting point from (0,0) in image coordinate system
#theta: angle at which grid is rotated relative to image coordinate system
#a1,a2: basis vectors of grid. list_to_matrix currently doesn't work with non-rectangular basis choices
#each peak is paired with its nearest grid point if it is also the nearest peak to that grid point.
#square of distances between these pairs is summed, and divided by number of pairs
def fitness(peaks,x,y,theta,ax,ay):
    pairings = {}
    rot = numpy.dot(numpy.array([[cos(theta),-sin(theta)],[sin(theta),cos(theta)]]),numpy.array([[ax,0],[0,ay]]))
    for peak in peaks:
        index = numpy.round(numpy.dot(numpy.linalg.inv(rot),peak-numpy.array([x,y])))
        d2 = numpy.linalg.norm(peak - numpy.array([x,y]) - numpy.dot(rot,index))**2
        index = tuple(index)
        if index not in pairings or d2 < pairings[index][1]:
            pairings[index] = [peak,d2]
    fit = [pair[1] for pair in pairings.values()]
    return sum(fit)/len(fit)

def optimize_lattice(peaks,ax,ay):
    fit_func = lambda x: fitness(peaks,x[0],x[1],x[2],ax,ay)
    return minimize(fit_func,numpy.array([0,0,0]),method='Powell',bounds=((0,ax),(0,ay),(-pi/4,pi/4))).x

def get_background(Agrid,k=2,l=.02):
    A = numpy.array([i[1] for i in Agrid]).T
    x = numpy.array([i/1000 for i in range(1044)])
    bg = numpy.transpose(BackgroundSubtraction.mcbl(A, k, x, l)).tolist()
    return [[Agrid[i][0],bg[i]] for i in range(len(Agrid))]

def nnmf_basis(Xgrid,n,bg=None):
    X = numpy.array([i[1] for i in Xgrid])
    if bg != None:
        bg = numpy.array([i[1] for i in bg])
        X = X - bg
    X = X.T
    model = NMF(n_components=n,init='random',solver='mu',beta_loss='kullback-leibler',max_iter=1000)
    W = model.fit_transform(X).T.tolist()
    H = model.components_.T.tolist()
    Hgrid = [[Xgrid[i][0],H[i]] for i in range(len(Xgrid))]
    return (Hgrid,W)

def greyscale_background(Agrid,bg,neg=True):
    if neg: 
        greylist = [[Agrid[i][0],1-sum(bg[i][1])/sum(Agrid[i][1])] for i in range(len(Agrid))]
    else:
        greylist = [[Agrid[i][0],sum(bg[i][1])/sum(Agrid[i][1])] for i in range(len(Agrid))]
    return greylist
    #greymatrix = contrast(list_to_matrix(greylist)[0])
    #inflatedgreymatrix = numpy.repeat(numpy.repeat(greymatrix,inflation,axis=0),inflation,axis=1)
    #return Image.fromarray(inflatedgreymatrix,mode='I') #imshow? how do i look at it

def greyscale_basis(Hgrid,i,neg=True):
    if neg:
        greylist = [[Hgrid[j][0],1-Hgrid[j][1][i]/sum(Hgrid[j][1])] for j in range(len(Hgrid))]
    else:
        greylist = [[Hgrid[j][0],Hgrid[j][1][i]/sum(Hgrid[j][1])] for j in range(len(Hgrid))]
    return greylist
    #greymatrix = contrast(list_to_matrix(greylist)[0])
    #inflatedgreymatrix = numpy.repeat(numpy.repeat(greymatrix,inflation,axis=0),inflation,axis=1)
    #return Image.fromarray(inflatedgreymatrix,mode='I') #imshow? how do i look at it


async def constant_refresh(window):
    while len(asyncio.all_tasks()) == 2:
        window.refresh()
    return None

#refresh the gui while awaiting a long calculation, so that is does not freak out
async def await_calculation(window,f,params):
    keylist = []
    for item in window.layout:
        if not item.disabled and item.key != 'cancel':
            keylist.append(item.key)
            window[item.key].update(disabled=True)
    res = await asyncio.gather(asyncio.run_in_executor(None,f,params),constant_refresh(window))
    for key in keylist:
        window[key].update(disabled=False)
    return res[0]

#take in a greyscale list tied to positions and change each pixel value x to 1-x
def negate(l):
    return [[i[0],1-i[1]] for i in l]

#get the indices of all elements in a list 'l' that meet a condition 'c' 
def index_conditional(c,l):
    c2 = lambda x: c(x[1])
    return [i[0] for i in filter(c2,enumerate(l))]

#a key function to convert my lists of positions + image data to PIL images with all other necessary information superimposed
#image should be grayscale, color will be used to superimpose peaks and lat
def to_image(l,peaks=None,lat=None,inflation=10,filepath='C:/Users/Operator/Documents/calibration'):
    print(peaks)
    mat,x0,y0,dx,dy = list_to_matrix(contrast(l))
    bmat = numpy.repeat(numpy.repeat(mat,inflation,axis=0),inflation,axis=1)
    cmat = numpy.zeros((bmat.shape[0],bmat.shape[1],3),dtype=numpy.uint8)
    for i in range(cmat.shape[0]):
        for j in range(cmat.shape[1]):
            cmat[i][j]=numpy.uint8(numpy.ceil(numpy.repeat(bmat[i][j],3)*256)-1)
    h = (inflation+1)/2 if inflation%4 == 1 else (inflation-1)/2 if inflation%4 == 3 else 2*ceil(inflation/4)
    d = int((inflation-h)/2)
    if peaks != None:
        for peak in peaks:
            c = numpy.array(peak).astype(numpy.int)
            #c = numpy.round((numpy.array(peak)-numpy.array([x0,y0]))/numpy.array([dx,dy])).astype(numpy.int)
            #print([c[0]*inflation+d,c[0]*inflation+inflation-d,c[1]*inflation+d,c[1]*inflation+inflation-d])
            for i in range(cmat.shape[0]):
                for j in range(cmat.shape[1]):
                    if i in range(c[0]*inflation+d,c[0]*inflation+inflation-d) and j in range(c[1]*inflation+d,c[1]*inflation+inflation-d):
                        cmat[i][j] = numpy.uint8(numpy.array([0,0,255]))
    if str(type(lat)) != "<class 'NoneType'>":
        lx,ly,theta,ax,ay = lat
        print(mat.shape)
        xf,yf = x0+dx*(mat.shape[0]-1),y0+dy*(mat.shape[1]-1)
        ij = lambda x,y: [cos(theta)*(x-lx)/ax+sin(theta)*(y-ly)/ay,cos(theta)*(y-ly)/ay-sin(theta)*(x-lx)/ax]
        cs = [ij(x0,y0),ij(x0,yf),ij(xf,y0),ij(xf,yf)]
        print([x0,y0,xf,yf])
        print(cs)
        cis = [i[0] for i in cs]
        cjs = [j[1] for j in cs]
        cimin = floor(min(cis))
        cimax = ceil(max(cis))
        cjmin = floor(min(cjs))
        cjmax = ceil(max(cjs))
        grid = numpy.array(list(filter(lambda x: max(x0,lx)-ax <= x[0] <= xf+ax and max(y0,ly)-ay <= x[1] <= yf+ay,[[lx+i*cos(theta)*ax-j*sin(theta)*ay,ly+i*sin(theta)*ax+j*cos(theta)*ay] for i in range(cimin,cimax+1) for j in range(cjmin,cjmax+1)])))
        print(len(grid))
        basegrid = numpy.array([numpy.round((loc-numpy.array([x0,y0]))/numpy.array([dx,dy])).astype(numpy.int) for loc in grid])
        finegrid = numpy.array([numpy.round((loc-numpy.array([x0,y0]))/(numpy.array([dx,dy])/inflation)).astype(numpy.int) for loc in grid])
        mindexi = numpy.amin(basegrid[:,0])-1
        maxdexi = numpy.amax(basegrid[:,0])+1
        mindexj = numpy.amin(basegrid[:,1])-1
        maxdexj = numpy.amax(basegrid[:,1])+1
        bigmat = numpy.zeros(((maxdexi-mindexi+1)*inflation,(maxdexj-mindexj+1)*inflation,3),dtype=numpy.uint8)
        print(bigmat.shape)
        for i in range(cmat.shape[0]):
            for j in range(cmat.shape[1]):
                bigmat[i-mindexi*inflation][j-mindexj*inflation] = cmat[i][j]
        r = floor((inflation-1)/4)
        for loc in finegrid:
            for i in range(bigmat.shape[0]):
                for j in range(bigmat.shape[1]):
                    if i in range(loc[0]-r,loc[0]+r+1) and j in range(loc[1]-r,loc[1]+r+1):
                        bigmat[i][j] = numpy.uint8(numpy.array([255,0,0]))
        cmat = bigmat
    filename = 'calibration_'+str(time.time())+'.png'
    Image.fromarray(cmat,mode='RGB').save(os.path.join(filepath,filename))
    return os.path.join(filepath,filename)

#so next: implement the background subtraction
#function to take in a basis and a grid, or just a list of weights...
#well, it might be a lot of things, but at any rate, need a function to make the grayscale image

def calibration_gui(Xgrid,ax,ay):
    bg = get_background(Xgrid)
    calcs = [{'bg':bg,'H':None,'W':None,'l':bg,'peaks':None,'lat':None,'cor':None}]
    ims = [to_image(greyscale_background(Xgrid,calcs[0]['l']))]
    params = [{'phase':1,'mode':1,'bases':None,'basis':None,'neg':True,'cor':None}]
    exvals = copy(params[0])
    layout = [[PySimpleGUI.Text("Spectral Image Confirmation",k="phase")],
              [PySimpleGUI.Image(ims[0],k="im")],
              [PySimpleGUI.Radio("Image based on Background Subtraction","ops",k="ops1",default=True,enable_events=True),PySimpleGUI.Radio("Image based on NNMF","ops",k="ops2",enable_events=True),PySimpleGUI.Radio("Image based on NNMF after Background Subtraction","ops",k="ops3",enable_events=True),
               PySimpleGUI.Spin(list(range(2,17)),k="bases",disabled=True,enable_events=True,initial_value=3),PySimpleGUI.Text("# basis spectra",k="basest"),PySimpleGUI.Spin([0,1,2],k="basis",disabled=True,enable_events=True),PySimpleGUI.Text("key spectrum",k="basist"),
               PySimpleGUI.Checkbox("Negative",k="neg",default=True,enable_events=True),PySimpleGUI.Spin(list(range(1,31)),initial_value=11,k="cor",disabled=True,enable_events=True),PySimpleGUI.Text("Correlation Kernel Size",k="cort")],
              [PySimpleGUI.Button("Confirm",k="confirm",enable_events=True),PySimpleGUI.Button("Apply",k="apply",enable_events=True),PySimpleGUI.Button("Cancel",k="cancel",enable_events=True),PySimpleGUI.Button("Back",k="back",disabled=True,enable_events=True)]]
    window = PySimpleGUI.Window('HITS Calibration',layout)
    while True:
        event, values = window.read()
        print(event)
        print(values)
        if event == 'ops1':
            exvals['mode'] = 1
            exvals['basis'] = None
            exvals['bases'] = None
            window['bases'].update(disabled=True)
            window['basis'].update(disabled=True)
        elif event in ('ops2','ops3'):
            exvals['mode'] = int(event[3:])
            exvals['basis'] = values['basis']
            exvals['bases'] = values['bases']
            window['bases'].update(disabled=False)
            window['basis'].update(values=list(range(values['bases'])),disabled=False)
        elif event == 'bases':
            exvals['bases'] = values['bases']
            window['basis'].update(values=list(range(values['bases'])))
        elif event == 'basis':
            exvals['basis'] = values['basis']
        elif event == 'neg':
            exvals['neg'] = values['neg']
        elif event == 'cor':
            exvals['cor'] = values['cor']
        elif event == PySimpleGUI.WIN_CLOSED:
            break
        elif event == 'cancel':
            break
        elif event == 'apply':
            l,bg,H,W,cor,peaks = None,None,None,None,None,None
            if exvals['phase'] == 1:
                #first figure out what needs to be changed
                    #options: grab an old image, negate an old image, create a new image, do a new analysis and create a new image
                    #if a previous image shares mode, bases, basis, and neg with the current settings, you can grab an old image
                    #if a previous image shares mode, bases, and basis with the current settings, you can negate an old image
                    #if a previous image shares mode and basis with the current settings, you must create a new image
                    #otherwise, you must do a new analysis
                indices = index_conditional(lambda d: d['mode']==exvals['mode'],params)
                if indices != []:
                    indices2 = index_conditional(lambda d: d['mode']==exvals['mode'] and d['bases']==exvals['bases'],params)
                    if indices2 != []:
                        indices3 = index_conditional(lambda d: d['mode']==exvals['mode'] and d['bases']==exvals['bases'] and d['basis']==exvals['basis'],params)
                        if indices3 != []:
                            indices4 = index_conditional(lambda d: d['mode']==exvals['mode'] and d['bases']==exvals['bases'] and d['basis']==exvals['basis'] and d['neg']==exvals['neg'],params)
                            if indices4 != []:
                                bg,H,W = calcs[indices4[0]]['bg'],calcs[indices4[0]]['H'],calcs[indices4[0]]['W']
                                l = calcs[indices4[0]]['l']
                            else:
                                bg,H,W = calcs[indices3[0]]['bg'],calcs[indices3[0]]['H'],calcs[indices3[0]]['W']
                                l = negate(calcs[indices3[0]]['l'])
                        else:
                            bg,H,W = calcs[indices2[0]]['bg'],calcs[indices2[0]]['H'],calcs[indices2[0]]['W']
                            l = greyscale_basis(H,exvals['basis'],neg=exvals['neg'])
                    else:
                        if exvals['mode'] == 1:
                            bg,H,W = get_background(Xgrid),None,None
                            l = greyscale_background(Xgrid,bg,neg=exvals['neg'])
                        elif exvals['mode'] == 2:
                            bg = None
                            H,W = nnmf_basis(Xgrid,exvals['bases'])
                            l = greyscale_basis(H,exvals['basis'],neg=exvals['neg'])
                        elif exvals['mode'] == 3:
                            bg = get_background(Xgrid)
                            H,W = nnmf_basis(Xgrid,exvals['bases'],bg=bg)
                            l = greyscale_basis(H,exvals['basis'],neg=exvals['neg'])
                else:                        
                    if exvals['mode'] == 1:
                        bg,H,W = get_background(Xgrid),None,None
                        im = greyscale_background(Xgrid,bg,neg=exvals['neg'])
                    elif exvals['mode'] == 2:
                        bg = None
                        H,W = nnmf_basis(Xgrid,exvals['bases'])
                        l = greyscale_basis(H,exvals['basis'],neg=exvals['neg'])
                    elif exvals['mode'] == 3:
                        bg = get_background(Xgrid)
                        H,W = nnmf_basis(Xgrid,exvals['bases'],bg=bg)
                        l = greyscale_basis(H,exvals['basis'],neg=exvals['neg'])
                #update tracking information: ims, params, intermediate calculation results
                calcs.append({'bg':bg,'H':H,'W':W,'l':l,'peaks':None,'lat':None,'cor':None})
                ims.append(to_image(l))
                params.append(copy(exvals))
                window['im'].update(ims[-1])
            if exvals['phase'] == 2:
                indices = index_conditional(lambda d: d['mode']==exvals['mode'] and d['bases']==exvals['bases'] and d['basis']==exvals['basis'] and d['neg']==exvals['neg'] and d['cor']==exvals['cor'],params)
                if indices != []:
                    cor,peaks = calcs[indices[0]]['cor'],calcs[indices[0]]['peaks']
                else:
                    cor,peaks = list_correlate(calcs[-1]['l'],k=kernel(values['cor'])) # need to store list from previous image to pipe in here, also, disable confirm without applying newest changes
                #update tracking information: ims, params, intermediate calculation results
                calcs.append({'bg':calcs[-1]['bg'],'H':calcs[-1]['H'],'W':calcs[-1]['W'],'l':calcs[-1]['l'],'peaks':peaks,'lat':None,'cor':cor})
                ims.append(to_image(cor,peaks=peaks))
                params.append(copy(exvals))
                window['im'].update(ims[-1])
        elif event == 'confirm':
            if exvals['phase'] == 1:
                exvals['phase'] += 1
                exvals['cor'] = values['cor']
                cor,peaks = list_correlate(calcs[-1]['l'],k=kernel(values['cor']))
                calcs.append(dict(calcs[-1],**{'cor':cor,'peaks':peaks}))
                params.append(copy(exvals))
                ims.append(to_image(cor,peaks=peaks))
                window['phase'].update("Sample Center Confirmation")
                window['im'].update(ims[-1])
                window['ops1'].update(disabled=True)
                window['ops2'].update(disabled=True)
                window['ops3'].update(disabled=True)
                window['bases'].update(disabled=True)
                window['basis'].update(disabled=True)
                window['neg'].update(disabled=True)
                window['cor'].update(disabled=False)
                window['back'].update(disabled=False)
            elif exvals['phase'] == 2:
                exvals['phase'] += 1
                lat = optimize_lattice(calcs[-1]['peaks'],ax,ay)
                lat = (lat[0],lat[1],lat[2],ax,ay)
                print(lat)
                calcs.append(dict(calcs[-1],**{'lat':lat}))
                params.append(copy(exvals))
                ims.append(to_image(calcs[-1]['l'],peaks=calcs[-1]['peaks'],lat=lat))
                window['phase'].update("Sample Grid Confirmation")
                window['im'].update(ims[-1])
                window['cor'].update(disabled=True)
                window['apply'].update(disabled=True)
            elif exvals['phase'] == 3:
                break
        elif event == 'back':
            if exvals['phase'] == 2:
                exvals['phase'] -= 1
                exvals['cor'] = None
                calcs.append(copy(calcs[-1]))
                params.append(copy(exvals))
                ims.append(to_image(calcs[-1]['l']))
                window['phase'].update("Spectral Image Confirmation")
                window['im'].update(ims[-1])
                window['ops1'].update(disabled=False)
                window['ops2'].update(disabled=False)
                window['ops3'].update(disabled=False)
                window['bases'].update(disabled=False)
                window['basis'].update(disabled=False)
                window['neg'].update(disabled=False)
                window['cor'].update(disabled=True)
                window['back'].update(disabled=True)
            elif exvals['phase'] == 3:
                exvals['phase'] -= 1
                calcs.append(copy(calcs[-1]))
                params.append(copy(exvals))
                ims.append(to_image(calcs[-1]['l'],peaks=calcs[-1]['peaks']))
                window['phase'].update("Sample Center Confirmation")
                window['im'].update(ims[-1])
                window['cor'].update(disabled=False)
                window['apply'].update(disabled=False)
        if exvals != params[-1]:
            window['confirm'].update(disabled=True)
            window['apply'].update(disabled=False)
        else:
            window['confirm'].update(disabled=False)
            window['apply'].update(disabled=True)
    window.close()
    #write all the images makers for all the windows
    #get window image updates
    #get handling for slow calculations
    #get dictionary tracking (not on this pass)
    #uhhhh check i didn't forget anything else (hehehe you will find out when you try to test)
        #we should sort out what standards for data transfers we are using... don't want things to sometimes be a matrix and sometimes be a PIL image
        #i would like things to always stay in list format. every function should intake things in list format, and output them in list format too, unless it is an image
        #to say it more precisely, every data array here that has information that corresponds to a certain position/spectrum must hold the location of that spectrum
        #until it is converted into an actual image (PIL, numpy matrices are not images by my definition here)

#new standards changes, we need to keep both image and data lists directly preceeding it handy.
# probably keep ims as a list of images and add keys l,peaks,lat to calcs.
#also need to disable certain buttons: apply when on the final image, and confirm when changes have not been applied
#what else am i forgetting?
#still need handling for slow calculations. with these changes i should be good to go.
#question is: do i need to make any changes outside GUI function? currently, i do not think so... just need to finish the actual optimizer, which you never did.

#hide apply when changes have not been applied. update calcs, params, im, when pressing confirm or back, do slow calc handling
    #first task complete, second in progress, also need to add similar logic to reuse old images in correlation menu
        #i have discovered that my logic was bad. i do, in fact, think i need to keep the values and the params fully synchronized. will do that update next and then the rest above.
    

#back to work: keep the window from timing out and add the second image pane, then test

#next after i debug the process -- figure out why images look like shit (do a general mathematica comparison), maybe mix in await_calculation, and figure out why mode 3 is broken

#bugs: maxdetect (fixed?), controls for when apply and confirm are enabled, choosing a different spectrum from the basis -- fixed the latter 2 here
#negate isn't working, type error in peak display


#current plan: the last big struggle is to get the minimization and lattice display working. if i manage that, my python code has surpassed my mathematica code
#from there: figure out why background subtraction is bugged, add second image pane, double check everything, allow secondary basis to be imposed.
#if i do all that, i will then need to evaluate how well this works, but i should be pretty much finished. probably some optimization to do.

if __name__ == "__main__":
    #get peaks
        #take in data of whatever format
        #generate grayscale image and allow user (me) to modify it if it is bad
            #variables: negative = True, background = True, basis = None, fitted = N/A
        #get peaks of image and allow user (me) to modify them if they are bad
            #variables: kernel size = 11
        #optimize lattice

    #todo: test all, figure out if you can do expert-fitted background, learn to make and modify image
    with open('C:/Users/Operator/Desktop/Xgridmini.json','r') as infile:
        Xgrid = json.load(infile)
    calibration_gui(Xgrid,2.5,2.5)

