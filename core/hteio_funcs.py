# -*- coding: utf-8 -*-
"""
Created on Mon Dec 14 10:24:55 2020

@author: yul69
"""

import os, numpy
import zipfile
from re import compile as regexcompile


PLATEMAPFOLDERS=[r'\\htejcap.caltech.edu\share\data\hte_jcap_app_proto\map', r'J:\hte_jcap_app_proto\map', \
                       r'\\htejcap.caltech.edu\share\home\users\hte\platemaps', r'ERT',r'K:\users\hte\platemaps']
PLATEFOLDERS=[r'\\htejcap.caltech.edu\share\data\hte_jcap_app_proto\plate', r'J:\hte_jcap_app_proto\plate']


#######################################################################################################################
# for getplatemappath_plateid: 
# inside of this function, the info prints are investigated and the screening_map_id is used to get the map id, 
# and then rules about the file naming of map files is used to look it up from J
######################################################################################################################

def rcp_to_dict(rcppath):  # read standard rcp/exp/ana/info structure to dict
    dlist = []

    def tab_level(astr):
        """Count number of leading tabs in a string
        """
        return (len(astr) - len(astr.lstrip("    "))) / 4

    if rcppath.endswith(".zip"):
        if "analysis" in os.path.dirname(rcppath):
            ext = ".ana"
        elif "experiment" in os.path.dirname(rcppath):
            ext = ".exp"
        else:
            ext = ".rcp"
        rcpfn = os.path.basename(rcppath).split(".copied")[0] + ext
        archive = zipfile.ZipFile(rcppath, "r")
        with archive.open(rcpfn, "r") as f:
            for l in f:
                k, v = l.decode("ascii").split(":", 1)
                lvl = tab_level(l.decode("ascii"))
                dlist.append(
                    {"name": k.strip(), "value": v.strip(), "level": lvl})
    else:
        with open(rcppath, "r") as f:
            for l in f:
                k, v = l.split(":", 1)
                lvl = tab_level(l)
                dlist.append(
                    {"name": k.strip(), "value": v.strip(), "level": lvl})
                
def tryprependpath(preppendfolderlist, p, testfile=True, testdir=True):
    #if (testfile and os.path.isfile(p)) or (testdir and os.path.isdir(p)):
    if os.path.isfile(p):
        return p
    p=p.strip(chr(47)).strip(chr(92))
    for folder in preppendfolderlist:
        pp=os.path.join(folder, p)
        if (testdir and os.path.isdir(pp)) or (testfile and os.path.isfile(pp)):
            return pp
    return ''

def getinfopath_plateid(plateidstr, erroruifcn=None):
    p=''
    fld=os.path.join(tryprependpath(PLATEFOLDERS, ''), plateidstr)
    if os.path.isdir(fld):
        l=[fn for fn in os.listdir(fld) if fn.endswith('info')]+['None']
        p=os.path.join(fld, l[0])
    if (not os.path.isfile(p)) and not erroruifcn is None:
        p=erroruifcn('', '')
    if (not os.path.isfile(p)):
        return None
    return p


#def getplatemappath_plateid(plateidstr, erroruifcn=None):
#    p=''
#    fld=os.path.join(tryprependpath(PLATEFOLDERS, ''), plateidstr)
#    if os.path.isdir(fld):
#        l=[fn for fn in os.listdir(fld) if fn.endswith('map')]+['None']
#        p=os.path.join(fld, l[0])
#    if (not os.path.isfile(p)) and not erroruifcn is None:
#        p=erroruifcn('', tryprependpath(PLATEFOLDERS[::-1], ''))
#    return p
def getplatemappath_plateid(plateidstr, erroruifcn=None, infokey='screening_map_id:', return_pmidstr=False, pmidstr=None):
    pmfold=tryprependpath(PLATEMAPFOLDERS, '')
    p=''
    if pmidstr is None:
        pmidstr=''
        infop=getinfopath_plateid(plateidstr)
        if infop is None:
            if not erroruifcn is None:
                p=erroruifcn('', tryprependpath(PLATEMAPFOLDERS, ''))
            return (p, pmidstr) if return_pmidstr else p
        with open(infop, mode='r') as f:
            s=f.read(1000)

        if pmfold=='' or (not infokey in s and not 'prints' in s):
            if not erroruifcn is None:
                p=erroruifcn('', tryprependpath(PLATEMAPFOLDERS, ''))
            return (p, pmidstr) if return_pmidstr else p
        pmidstr=s.partition(infokey)[2].partition('\n')[0].strip()
        if pmidstr=='' and 'prints' in s:
            infod = rcp_to_dict(infop)
            printdlist = [v for k,v in infod['prints'].items()]
            printdlist.sort(key=lambda x: int(x['id']), reverse=True)
            printd = printdlist[0]
            pmidstr = printd['map_id']
    fns=[fn for fn in os.listdir(pmfold) if fn.startswith('0'*(4-len(pmidstr))+pmidstr+'-') and fn.endswith('-mp.txt')]
    if len(fns)!=1:
        if not erroruifcn is None:
            p=erroruifcn('', tryprependpath(PLATEMAPFOLDERS, ''))
        return (p, pmidstr) if return_pmidstr else p
    p=os.path.join(pmfold, fns[0])
    return (p, pmidstr) if return_pmidstr else p

#######################################################################################################################
# for readsingleplatemaptxt: 
#this list has 1 entry for each sample and pmdlist[0] is a dictionary with keys that are the column headings of platemap files. 
#Not clear we should deal with platemaps in this format vs using a pandas dataframe
######################################################################################################################

def myeval(c):
    if c=='None':
        c=None
    elif c=='nan' or c=='NaN':
        c=numpy.nan
    else:
        temp=c.lstrip('0')
        if (temp=='' or temp=='.') and '0' in c:
            c=0
        else:
            c=eval(temp)
    return c

def readsingleplatemaptxt(p, returnfiducials=False,  erroruifcn=None, lines=None):
    if lines is None:
        try:
            f=open(p, mode='r')
        except:
            if erroruifcn is None:
                return []
            p=erroruifcn('bad platemap path')
            if len(p)==0:
                return []
            f=open(p, mode='r')

        ls=f.readlines()
        f.close()
    else:
        ls=lines
    if returnfiducials:
        s=ls[0].partition('=')[2].partition('mm')[0].strip()
        if not ',' in s[s.find('('):s.find(')')]: #needed because sometimes x,y in fiducials is comma delim and sometimes not
            print('WARNING: commas inserted into fiducials line to adhere to format.')
            print(s)
            s=s.replace('(   ', '(  ',).replace('(  ', '( ',).replace('( ', '(',).replace('   )', '  )',).replace(',  ', ',',).replace(', ', ',',).replace('  )', ' )',).replace(' )', ')',).replace('   ', ',',).replace('  ', ',',).replace(' ', ',',)
            print(s)
        fid=eval('[%s]' %s)
        fid=numpy.array(fid)
    for count, l in enumerate(ls):
        if not l.startswith('%'):
            break
    keys=ls[count-1][1:].split(',')
    keys=[(k.partition('(')[0]).strip() for k in keys]
    dlist=[]
    samplelines=[l for l in ls[count:] if l.count(',')==(len(keys)-1)]
    for l in samplelines:
        sl=l.split(',')
        d=dict([(k, myeval(s.strip())) for k, s in zip(keys, sl)])
        dlist+=[d]
    if not 'sample_no' in keys:
        dlist=[dict(d, sample_no=d['Sample']) for d in dlist]
    if returnfiducials:
        return dlist, fid
    return dlist

#######################################################################################################################
# for importinfo: dictionary version of info file
######################################################################################################################
def partitionlineitem(ln):
    a, b, c=ln.strip().partition(':')
    return (a.strip(), c.strip())

def createdict_tup(nam_listtup):
    k_vtup=partitionlineitem(nam_listtup[0])
    if len(nam_listtup[1])==0:
        return k_vtup
    d=dict([createdict_tup(v) for v in nam_listtup[1]])
    return (k_vtup[0], d)

getnumspaces=lambda a:len(a) - len(a.lstrip(' '))
def createnestparamtup(lines):
    ln=str(lines.pop(0).rstrip())
    numspaces=getnumspaces(ln)
    subl=[]
    while len(lines)>0 and getnumspaces(lines[0])>numspaces:
        tu=createnestparamtup(lines)
        subl+=[tu]

    return (ln.lstrip(' '), subl)

def filedict_lines(lines):
    lines=[l for l in lines if len(l.strip())>0]
    exptuplist=[]
    while len(lines)>0:
        exptuplist+=[createnestparamtup(lines)]
    return dict([createdict_tup(tup) for tup in exptuplist])

def importinfo(plateidstr):
    fn=plateidstr+'.info'
    p=tryprependpath(PLATEFOLDERS, os.path.join(plateidstr, fn), testfile=True, testdir=False)
    if not os.path.isfile(p):
        return "No plate found!"
    with open(p, mode='r') as f:
        lines=f.readlines()
    infofiled=filedict_lines(lines)
    return infofiled


#######################################################################################################################
# for getelements_plateidstr: 
# gets the elements from the screening print in the info file (see getelements_plateidstr()) and presents them to user
######################################################################################################################


def get_multielementink_concentrationinfo(printd, els, return_defaults_if_none=False):#None if nothing to report, (True, str) if error, (False, (cels_set_ordered, conc_el_chan)) with the set of elements and how to caclualte their concentration from the platemap

    searchstr1='concentration_elements'
    searchstr2='concentration_values'
    if not (searchstr1 in printd.keys() and searchstr2 in printd.keys()):
        if return_defaults_if_none:
            nels_printchannels=[len(regexcompile("[A-Z][a-z]*").findall(el)) for el in els]
            if max(nels_printchannels)>1:
                return True, 'concentration info required when there are multi-ink channels'
            els_set=set(els)
            if len(els_set)<len(els):#only known cases of this (same element used in multiple print channels and no concentration info provided) is when Co printed in library and as internal reference, in which case 2 channels never printed together but make code assume each ink with equal concentration regardless of duplicates
                conc_el_chan=numpy.zeros((len(els_set), len(els)), dtype='float64')
                cels_set_ordered=[]
                for j, cel in enumerate(els):#assume
                    if not cel in cels_set_ordered:
                        cels_set_ordered+=[cel]
                    i=cels_set_ordered.index(cel)
                    conc_el_chan[i, j]=1
            else: #this is generic case with no concentration info
                cels_set_ordered=els
                conc_el_chan=numpy.identity(len(els), dtype='float64')
            return False, (cels_set_ordered, conc_el_chan)
        else:
            return None
    cels=printd[searchstr1]
    concstr=printd[searchstr2]
    conclist=[float(s) for s in concstr.split(',')]

    cels=[cel.strip() for cel in cels.split(',')]
    cels_set=set(cels)
    if len(cels_set)<len(cels) or True in [conclist[0]!=cv for cv in conclist]:#concentrations available where an element is used multiple times. or 1 of the concentrations is different from the rest
        els_printchannels=[regexcompile("[A-Z][a-z]*").findall(el) for el in els]
        els_tuplist=[(el, i, j) for i, l in enumerate(els_printchannels) for j, el in enumerate(l)]
        cels_tuplist=[]
        for cel in cels:
            while len(els_tuplist)>0:
                tup=els_tuplist.pop(0)
                if tup[0]==cel:
                    cels_tuplist+=[tup]
                    break
        if len(cels_tuplist)!=len(cels):
            return True,  'could not find the concentration_elements in order in the elements list'
        cels_set_ordered=[]
        for cel, chanind, ind_elwithinchan in cels_tuplist:
            if not cel in cels_set_ordered:
                cels_set_ordered+=[cel]

        conc_el_chan=numpy.zeros((len(cels_set_ordered), cels_tuplist[-1][1]+1), dtype='float32')#tthe number of elements in the net composition space by the max ink channel
        for (cel, chanind, ind_elwithinchan), conc in zip(cels_tuplist, conclist):
            conc_el_chan[cels_set_ordered.index(cel), chanind]=conc
        #for a given platemap sample with x being the 8-component vecotr of ink channel intensity, the unnormalized concentration of cels_set_ordered is conc_el_chan*x[:conc_el_chan.shape[0]]
        return False, (cels_set_ordered, conc_el_chan)
    if return_defaults_if_none:#this handles the case when the length of concentration_elements does not match elements,, which usually hapens when only partial concentration info is available
        return False, (els, numpy.identity(len(els), dtype='float64')*conclist[0])
    return None

def getelements_plateidstr(plateidstr_or_filed, multielementink_concentrationinfo_bool=False,print_key_or_keyword='screening_print_id', exclude_elements_list=[''], return_defaults_if_none=False):#print_key_or_keyword can be e.g. "print__3" or screening_print_id
    if isinstance(plateidstr_or_filed, dict):
        infofiled=plateidstr_or_filed
    else:
        infofiled=importinfo(plateidstr_or_filed)
        if infofiled is None:
            return None
    requiredkeysthere=lambda infofiled: ('screening_print_id' in infofiled.keys()) if print_key_or_keyword=='screening_print_id' \
                                                           else (print_key_or_keyword in infofiled['prints'].keys())
    while not ('prints' in infofiled.keys() and requiredkeysthere(infofiled)):
        if not 'lineage' in infofiled.keys() or not ',' in infofiled['lineage']:
            return None
        parentplateidstr=infofiled['lineage'].split(',')[-2].strip()
        infofiled=importinfo(parentplateidstr)
    if print_key_or_keyword=='screening_print_id':
        printdlist=[printd for printd in infofiled['prints'].values() if 'id' in printd.keys() and printd['id']==infofiled['screening_print_id']]
        if len(printdlist)==0:
            return None
        printd=printdlist[0]
    else:
        printd=infofiled['prints'][print_key_or_keyword]
    if not 'elements' in printd.keys():
        return None
    els=[x for x in printd['elements'].split(',') if x not in exclude_elements_list]

    if multielementink_concentrationinfo_bool:
        return els, get_multielementink_concentrationinfo(printd,els, return_defaults_if_none=return_defaults_if_none)
    return els

##############################################################################################################
##############################################################################################################
#function that access info file and platemaps:
# 1. check if the plate_id(info file) exists
##############################################################################################################
    
def readinfoplatemap(plateidstr):
    infod=importinfo(str(plateidstr))
    # 1. checks that the plate_id (info file) exists
    if infod!="No plate found!":
        #print(infod)    
    
    # 2. gets the elements from the screening print in the info file (see getelements_plateidstr()) and presents them to user
        elements=getelements_plateidstr(plateidstr)
        print("Elements:", elements)
    
    # 3. checks that a print 5and anneal record exist in the info file
        if not 'prints' or not 'anneals' in infod.keys():
            print('Warning: no print or anneal record exists')
      
    # 4. gets platemap and passes to alignment code
    #pmpath=getplatemappath_plateid(plateidstr, return_pmidstr=True)
        pmpath=getplatemappath_plateid(plateidstr)
        pmdlist=readsingleplatemaptxt(pmpath)
        return pmdlist
         
    else:
        return "No plate found!"