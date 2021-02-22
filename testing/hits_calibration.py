from math import sin,cos,ceil,floor,pi
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
    return (mat,minx,miny,dx,dy)
    
def matrix_to_list(mat,x0=0,y0=0,dx=1,dy=1):
    pass

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
    mat = list_to_matrix(l)[0]
    cor = correlate(mat,k)
    return (matrix_to_list(cor),MaxDetect(cor))

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
    return minimize(fit_func,numpy.array([0,0,0]),method='Powell',bounds=((0,max(a1[0],a2[0])),(0,max(a1[1],a2[1])),(-pi/4,pi/4))).x

def get_background(Agrid,k=2,l=.02):
    A = numpy.array([i[1] for i in Agrid]).T
    x = numpy.array([i/1000 for i in range(1044)])
    bg = BackgroundSubtraction.mcbl(A, k, x, l).T.tolist()
    return [[A[i][0],bg[i]] for i in range(len(A))]

def nnmf_basis(Xgrid,n,bg=None):
    X = list_to_matrix(Xgrid).T
    if bg != None:
        bg = list_to_matrix(bg)
        X = X - bg
    model = NMF(n_components=n,init='random',solver='mu',beta_loss='kullback-leibler')
    W = model.fit_transform(X).T.tolist()
    H = model.components_.T.tolist()
    Hgrid = [[Xgrid[i][0],H[i]] for i in range(len(Xgrid))]
    Wgrid = [[Xgrid[i][0],W[i]] for i in range(len(Xgrid))]
    return (Hgrid,Wgrid)

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


#so next: implement the background subtraction
#function to take in a basis and a grid, or just a list of weights...
#well, it might be a lot of things, but at any rate, need a function to make the grayscale image

def calibration_gui(Xgrid,a1,a2):
    bg = get_background(Xgrid)
    calcs = [{'bg':bg,'H':None,'W':None,'l':bg,'peaks':None,'lat':None,'cor':None}]
    ims = [greyscale_background(Xgrid,calcs[0]['bg'])]
    params = [{'phase':1,'mode':1,'bases':None,'basis':None,'neg':True,'cor':None}]
    layout = [[PySimpleGUI.Text("Spectral Image Confirmation",k="phase")],
              [PySimpleGUI.Image(ims[0],k="im")],
              [PySimpleGUI.Radio("Image based on Background Subtraction","ops",k="ops1",default=True),PySimpleGUI.Radio("Image based on NNMF","ops",k="ops2"),PySimpleGUI.Radio("Image based on NNMF after Background Subtraction","ops",k="ops3"),
               PySimpleGUI.Spin(list(range(3,17),k="bases"),disabled=True),PySimpleGUI.Text("# basis spectra",k="basest"),PySimpleGUI.Spin([],k="basis",disabled=True),PySimpleGUI.Text("key spectrum",k="basist"),
               PySimpleGUI.Checkbox("Negative",k="neg",default=True),PySimpleGUI.Spin(list(range(1,30)),k="cor",disabled=True),PySimpleGUI.Text("Correlation Kernel Size",k="cort",disabled=True)],
              [PySimpleGUI.Button("Confirm",k="confirm"),PySimpleGUI.Button("Apply",k="apply"),PySimpleGUI.Button("Cancel",k="cancel"),PySimpleGUI.Button("Back",k="back",disabled=True)]]
    window = PySimpleGui.Window('HITS Calibration',layout)
    while True:
        event, values = window.read()
        mode = 1 if values['ops1'] else 2 if values['ops2'] else 3 if values['ops3'] else None
        window['apply'].update(disabled=params[-1]['mode']==mode and params[-1]['bases'] in (None,values['bases']) and params[-1]['basis'] in (None,values['basis']) and params[-1]['neg']==values['neg'] and params[-1]['cor'] in (None,values['cor']))
        if event == 'ops1':
            window['bases'].update(initial_value=None,disabled=True)
            window['basis'].update(initial_value=None,disabled=True)
        if event in ('ops2','ops3') and values['bases'] == None:
            window['bases'].update(initial_value=3,disabled=False)
            window['basis'].update(initial_value=0,disabled=False)
        elif event == PySimpleGui.WIN_CLOSED:
            break
        elif event == 'cancel':
            break
        elif event == 'apply':
            l,bg,H,W,cor,peaks
            if values['phase'] == "Spectral Image Confirmation":
                #first figure out what needs to be changed
                    #options: grab an old image, negate an old image, create a new image, do a new analysis and create a new image
                    #if a previous image shares mode, bases, basis, and neg with the current settings, you can grab an old image
                    #if a previous image shares mode, bases, and basis with the current settings, you can negate an old image
                    #if a previous image shares mode and basis with the current settings, you must create a new image
                    #otherwise, you must do a new analysis
                indices = index_conditional(lambda d: d['mode']==mode,params)
                if indices != []
                    indices2 = index_conditional(lambda d: d['mode']==mode and d['bases']==values['bases'],params)
                    if indices2 != []:
                        indices3 = index_conditional(lambda d: d['mode']==mode and d['bases']==values['bases'] and d['basis']==values['basis'],params)
                        if indices3 != []:
                            indices4 = index_conditional(lambda d: d['mode']==mode and d['bases']==values['bases'] and d['basis']==values['basis'] and d['neg']==values['neg'],params)
                            if indices4 != []:
                                bg,H,W = calcs[indices4[0]]['bg'],calcs[indices4[0]]['H'],calcs[indices4[0]]['W']
                                l = calcs[indices4[0]]['l']
                            else:
                                bg,H,W = calcs[indices3[0]]['bg'],calcs[indices3[0]]['H'],calcs[indices3[0]]['W']
                                l = negate(calcs[indices3[0]]['l'])
                        else:
                            bg,H,W = calcs[indices2[0]]['bg'],calcs[indices2[0]]['H'],calcs[indices2[0]]['W']
                            l = greyscale_basis(H,values['basis'],neg=values['neg'])
                    else:
                        if mode == 1:
                            bg,H,W = get_background(Xgrid),None,None
                            l = greyscale_background(Xgrid,bg,neg=values['neg'])
                        elif mode == 2:
                            bg = None
                            H,W = nnmf_basis(Xgrid,values['bases'])
                            l = greyscale_basis(H,values['basis'],neg=values['neg'])
                        elif mode == 3:
                            bg = get_background(Xgrid)
                            H,W = nnmf_basis(Xgrid,bg=bg)
                            l = greyscale_basis(H,values['bases']),values['basis'],neg=values['neg'])
                else:                        
                    if mode == 1:
                        bg,H,W = get_background(Xgrid),None,None
                        im = greyscale_background(Xgrid,bg,neg=values['neg'])
                    elif mode == 2:
                        bg = None
                        H,W = nnmf_basis(Xgrid,values['bases'])
                        l = greyscale_basis(H,values['basis'],neg=values['neg'])
                    elif mode == 3:
                        bg = get_background(Xgrid)
                        H,W = nnmf_basis(Xgrid,bg=bg)
                        l = greyscale_basis(H,values['bases']),values['basis'],neg=values['neg'])
                #update tracking information: ims, params, intermediate calculation results
                calcs.append({'bg':bg,'H':H,'W':W,'l':l,'peaks':None,'lat':None,'cor':None})
                ims.append(to_image(l))
                params.append({'phase':1,'mode':mode,'bases':values['bases'],'basis':values['basis'],'neg':values['neg'],'cor':values['cor']})
                window['im'].update(data=ims[-1])
            if values['phase'] == "Sample Center Confirmation":
                indices = index_conditional(lambda d: d['mode']==mode and d['bases']==values['bases'] and d['basis']==values['basis'] and d['neg']==values['neg'] and d['cor']==values['cor'],params)
                if indices != None:
                    cor,peaks = calcs[indices[0]]['cor'],calcs[indices[0]]['cor']
                else:
                    cor,peaks = list_correlate(calcs[-1]['l'],k=kernel(values['cor'])) # need to store list from previous image to pipe in here, also, disable confirm without applying newest changes
                #update tracking information: ims, params, intermediate calculation results
                calcs.append({'bg':calcs[-1]['bg'],'H':calcs[-1]['H'],'W':calcs[-1]['W'],'l':calcs[-1]['l'],'peaks':peaks,'lat':None,'cor':cor})
                ims.append(to_image(cor,peaks=peaks))
                params.append({'phase':1,'mode':mode,'bases':values['bases'],'basis':values['basis'],'neg':values['neg'],'cor':values['cor']})
                window['im'].update(data=ims[-1])
        elif event == 'confirm':
            if values['phase'] == "Spectral Image Confirmation":
                cor,peaks = list_correlate(calcs[-1]['l'],k=kernel(values['cor']))
                calcs.append(calcs[-1].update({'cor':values['cor'],'peaks':peaks}))
                params.append(params[-1].update({'cor':values['cor']}))
                ims.append(to_image(cor,peaks=peaks))
                window['phase'].update(text="Sample Center Confirmation")
                window['im'].update(data=ims[-1])
                window['ops'].update(disabled=True)
                window['bases1'].update(disabled=True)
                window['bases2'].update(disabled=True)
                window['basest1'].update(disabled=True)
                window['basest2'].update(disabled=True)
                window['neg'].update(disabled=True)
                window['cor'].update(disabled=False,initial_value=11)
                window['cort'].update(disabled=False)
                window['back'].update(disabled=False)
            if values['phase'] == "Sample Center Confirmation":
                lat = optimize_lattice(calcs[-1]['peaks'],a1,a2)
                calcs.append(calcs[-1].update({'lat':lat}))
                params.append(params[-1])
                ims.append(to_image(calcs[-1]['l'],peaks=calcs[-1]['peaks'],lat=lat))
                window['phase'].update(text="Sample Grid Confirmation")
                window['im'].update(data=ims[-1])
                window['cor'].update(disabled=True)
                window['cort'].update(disabled=True)
                window['apply'].update(disabled=True)
            if values['phase'] == "Sample Grid Confirmation":
                break
        elif event == 'back':
            if values['phase'] == "Sample Center Confirmation":
                calcs.append(calcs[-1])
                params.append(params[-1].update({'cor':None}))
                ims.append(to_image(calcs[-1]['l']))
                window['phase'].update(text="Spectral Image Confirmation")
                window['im'].update(data=ims[-1])
                window['ops'].update(disabled=False)
                window['bases1'].update(disabled=False)
                window['bases2'].update(disabled=False)
                window['basest1'].update(disabled=False)
                window['basest2'].update(disabled=False)
                window['neg'].update(disabled=False)
                window['cor'].update(disabled=True,initial_value=None)
                window['cort'].update(disabled=True)
                window['back'].update(disabled=True)
            if values['phase'] == "Sample Grid Confirmation":
                calcs.append(calcs[-1])
                params.append(params[-1])
                ims.append(to_image(calcs[-1]['l'],peaks=calcs[-1]['peaks']))
                window['phase'].update(text="Sample Center Confirmation")
                window['im'].update(data=ims[-1])
                window['cor'].update(disabled=False)
                window['cort'].update(disabled=False)
                window['apply'].update(disabled=False)
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
    
    #refresh the gui while awaiting a long calculation, so that is does not freak out
    def await_calculation(window,f,params):
        keylist = []
        res = None
        for item in window.layout:
            if not item.disabled and item.key != 'cancel':
                keylist.append(item.key)
                window[item.key].update(disabled=True)
        while res == None:
            window.refresh()
            f(**params)
        return f(**params)
        for key in keylist:
            window[key].update(disabled=False)

    #take in a greyscale list tied to positions and change each pixel value x to 1-x
    def negate(l):
        return [[l[0],1-l[1]] for i in l]

    #get the indices of all elements in a list 'l' that meet a condition 'c' 
    def index_conditional(c,l):
        c2 = lambda x: c(x[1])
        return [i[0] for i in filter(c2,enumerate(l))]

    #a key function to convert my lists of positions + image data to PIL images with all other necessary information superimposed
    #image should be grayscale, color will be used to superimpose peaks and lat
    def to_image(l,peaks=None,lat=None,inflation=10):
        mat,x0,y0,dx,dy = list_to_matrix(contrast(l))
        mat = numpy.repeat(numpy.repeat(mat,inflation,axis=0),inflation,axis=1)
        cmat = mat[:,:,numpy.newaxis]
        for i in range(cmat.shape[0]):
            for j in range(cmat.shape[1]):
                cmat[i][j] = numpy.repeat(mat[i][j],3)
        h = (inflation+1)/2 if inflation%4 == 1 else (inflation-1)/2 if inflation%4 == 3 else 2*ceil(inflation/4)
        d = (inflation-h)/2
        for peak in peaks:
            c = numpy.round((numpy.array(peak)-numpy.array([x0,y0]))/numpy.array([dx,dy]))
            for i in range(cmat.shape[0]):
                for j in range(cmat.shape[1]):
                    if i in range(c[0]*inflation+d,c[0]*inflation+inflation-d) and j in range(c[1]*inflation+d,c[1]*inflation+inflation-d):
                        cmat[i][j] = numpy.array([0,0,1])
        if lat != None:
            lx,ly,theta = lat
            xf,yf = x0+dx*len(l),y0+dy*len(l)
            ij(x,y) = lambda x,y: [cos(theta)*(x-lx)/dx+sin(theta)*(y-ly)/dy,cos(theta)*(y-ly)/dy-sin(theta)*(x-lx)/dx]
            cs = [ij(x0,y0),ij(x0,yf),ij(xf,y0),ij(xf,yf)]
            cis = [i[0] for i in cs]
            cjs = [j[1] for j in cs]
            cimin = floor(min(cis))
            cimax = ciel(max(cis))
            cjmin = floor(min(cjs))
            cjmax = ciel(max(cjs))
            grid = numpy.array(filter(lambda x: max(x0,lx)-lx <= x[0] <= xf+lx and max(y0,ly)-ly <= x[1] <= yf+ly,[[lx+i*cos(theta)*dx-j*sin(theta)*dy,ly+i*sin(theta)*dx+j*cos(theta)*dy] for i in range(cimin,cimax+1) for j in range(cjmin,cjmax+1)]))
            basegrid = numpy.array([numpy.round((loc-numpy.array([x0,y0]))/numpy.array([dx,dy])) for loc in grid])
            finegrid = numpy.array([numpy.round((loc-numpy.array([x0,y0]))/(numpy.array([dx,dy])/inflation)) for loc in grid])
            mindexi = numpy.amin(basegrid[:,0])-1
            maxdexi = numpy.amax(basegrid[:,0])+1
            mindexj = numpy.amin(basegrid[:,1])-1
            maxdexj = numpy.amax(basegrid[:,1])+1
            bigmat = numpy.zeroes(((maxdexi-mindexi+1)*inflation,(maxdexj-mindexj+1)*inflation,3))
            for i in range(cmat.shape[0]):
                for j in range(cmat.shape[1]):
                    bigmat[i-mindexi*inflation][j-mindexj*inflation] = cmat[i][j]
            r = floor((inflation-1)/4)
            for loc in finegrid:
                for i in range(bigmat.shape[0]):
                    for j in range(bigmat.shape[1]):
                        if i in range(loc[0]-r,loc[0]+r+1) and j in range(loc[1]-r,loc[1]+r+1):
                            bigmat[i][j] = numpy.array([1,0,0])
            cmat = bigmat
        return Image.fromarray(cmat,mode='RGB')


if __name__ == "__main__":
    #get peaks
        #take in data of whatever format
        #generate grayscale image and allow user (me) to modify it if it is bad
            #variables: negative = True, background = True, basis = None, fitted = N/A
        #get peaks of image and allow user (me) to modify them if they are bad
            #variables: kernel size = 11
        #optimize lattice

    #todo: test all, figure out if you can do expert-fitted background, learn to make and modify image

    Xgrid = None
    calibration_gui(Xgrid)

