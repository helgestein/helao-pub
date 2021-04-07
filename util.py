from decimal import Decimal
import numpy as np
import itertools as it

def makeMeshBrute(offset_x=0,offset_y=0,a=50,b=50,da=0.01,db=0.01):
    x_pos = np.arange(0+offset_x,a+da+offset_x,da)
    y_pos = np.arange(0+offset_y,b+db+offset_y,db)
    x,y = np.meshgrid(x_pos,y_pos)
    x = x.flatten()
    y = y.flatten()
    MA_ID = [i+1 for i in range(len(x))]
    return x,y,MA_ID

# test: x[4567890]=19.77, y[4567890]=9.13, MA_ID[4567890]=4567891
def getMAFromXY(x_,y_,a=50,b=50,da=0.01,db=0.01):
    '''this function returns the measurement area for a position and the corresponing grid
    it is assumed that you giv the position x_,y_ in mm from the top left corner.
    positive x is from left to right and 
    positive y is from top to bottom'''
    from decimal import Decimal
    dm_x = Decimal(str(x_))//Decimal(str(da))
    mod_x = Decimal(str(x_))%Decimal(str(da))
    if not mod_x == 0:
        raise ValueError
    dm_y = Decimal(str(y_))//Decimal(str(db))
    mod_y = Decimal(str(y_))%Decimal(str(db))
    if not mod_y == 0:
        raise ValueError
    MA_ID = dm_y*Decimal(str(b))/Decimal(str(db))+dm_y+Decimal(str(x_))/Decimal(str(db))+1
    if MA_ID<0:
        raise ValueError
    return dict(a=a,b=b,da=da,db=db,MA=int(MA_ID))

def getCircularMA(x_offset,y_offset,r,gridSpec=None,da=0.01,db=0.01):
    x,y,_ = makeMeshBrute(offset_x=x_offset-r/2,offset_y=y_offset-r/2,a=r,b=r,da=0.01,db=0.01)
    MAlist = []
    for x_,y_ in zip(x,y):
        x_=round(x_,len(str(da-int(da)))-2)#jack's edit to avoid floating point errors
        y_=round(y_,len(str(db-int(db)))-2)
        dist = np.sqrt((x_offset-x_)**2+(y_offset-y_)**2)
        if dist<r:
            MAlist.append(getMAFromXY(x_,y_,a=r,b=r,da=0.01,db=0.01)['MA'])
    return MAlist

def makeNAry(n,steps,shuffle=True):
    np.random.seed(23)
    tern = np.array([c for c in it.product([i/10 for i in range(11)],repeat=3) if np.isclose(sum(c),1)])
    np.random.shuffle(tern)
    return tern

def ternToCart(tern):
    redc=tern[:,0:2]
    cartxs = 1.-redc[:, 0]-redc[:, 1]/2.
    cartys = np.sqrt(3) * redc[:, 1] / 2.0

def plotTriangle(ax): 
    lines = [[0,0],[0.5,np.sqrt(3)/2],[1,0]]
    for i in [[0,1],[1,2],[2,0]]:
        ax.plot([lines[i[0]][0],lines[i[1]][0]],[lines[i[0]][1],lines[i[1]][1]],color='black',linewidth=3)
    ax.axes('equal')
    ax.axis('off')


def list_to_dict(my_list):
    return {a:a_ for a,a_ in enumerate(my_list)}


def incrementName(s:str):
    #i am incrementing names of runs, sessions, substrates, and measurement numbers numbers enough
    #go from run_1 to run_2 or from substrate_1_session_1.hdf5 to substrate_1_session_2.hdf5, etc...
    segments = s.split('_')
    if '.' in segments[-1]:
        #so that we can increment filenames too
        subsegment = segments[-1].split('.') 
        subsegment[0] = str(int(subsegment[0])+1)
        segments[-1] = '.'.join(subsegment)
    else:
        segments[-1] = str(int(segments[-1])+1)
    return '_'.join(segments)

def highestName(names:list):
    #take in a list of strings which differ only by an integer, and return the one for which that integer is highest
    #another function I am performing often enough that it deserves it's own tool
    #used for finding the most recent run, measurement number, and session
    if len(names) == 1:
        return names[0]
    else:
        slen = min([len(i) for i in names])
        leftindex = None
        rightindex = None
        for i in range(slen):
            for s in names:
                if s[i] != names[0][i]:
                    leftindex = i
                    break
            if leftindex != None:
                break
        for i in range(-1,-slen-1,-1):
            for s in names:
                if s[i] != names[0][i]:
                    rightindex = i
                    break
            if rightindex != None:
                break
        numbers = [int(s[leftindex:rightindex+1] if rightindex != -1 else s[leftindex:]) for s in names]
        return names[numbers.index(max(numbers))]

#for a string of dict keys seperated by '/', get the value of d under that series
def dict_address(address,d):
    address = address.split('/')
    if len(address) == 1:
        return d[address[0]]
    else:
        return dict_address('/'.join(address[1:]),d[address[0]])

#for a string of dict keys seperated by '/', set the value of dictionary d at that address to val
def dict_address_set(address,d,val):
    address = address.split('/')
    if len(address) == 1:
        d[address[0]] = val
    else:
        dict_address_set('/'.join(address[1:]),d[address[0]],val)