import json
import numpy as np
import matplotlib.pyplot as plot
from julia import BackgroundSubtraction
from sklearn.decomposition import NMF

#load the data
with open('C:/Users/Operator/Desktop/Xgridmini.json') as json_file:
    data = json.load(json_file)

#make a matrix for the data and a list for position
mat = np.array([d[1] for d in data])
pos = np.array([d[0] for d in data])

#use MCBL for background subtraction
A = mat.T
k = 2
l = 20/1000
x = np.array([i/1000 for i in range(1044)])
background = BackgroundSubtraction.mcbl(A, k, x, l)

#subtract the background
diff = A-background
#plt.plot(diff[:,2084])

#scale
diff = diff/(-np.min(diff))+1

#identify phases with nnmf
model = NMF(n_components=4, init='nndsvd', random_state=0,max_iter=2000)
W = model.fit_transform(diff)
H = model.components_
hc = np.array([h/sum(h) for h in H.T])

def cmyk_to_rgb(c, m, y, k, cmyk_scale, rgb_scale=255):
    r = rgb_scale (1.0 - c / float(cmyk_scale)) (1.0 - k / float(cmyk_scale))
    g = rgb_scale (1.0 - m / float(cmyk_scale)) (1.0 - k / float(cmyk_scale))
    b = rgb_scale (1.0 - y / float(cmyk_scale)) (1.0 - k / float(cmyk_scale))
    return [r/256, g/256, b/256]
    #scale to rgb
color = np.array([cmyk_to_rgb(*h,1) for h in hc])

#plot and enjoy
#plt.scatter(pos[:,0],pos[:,1],marker='s',color=color)
#plt.show()

#get some info from image
xpos = int(np.unique(pos[:,0]).shape[0])
ypos = int(np.unique(pos[:,1]).shape[0])

#plt.imshow(color[:,0].reshape(xpos,ypos))
#plt.show()

#plt.scatter(pos[:,0],pos[:,1],marker='s',c=color[:,0])
#plt.show()

import cv2 as cv
image = color[:,0].reshape(xpos,ypos)
im = np.array(image*265,dtype=np.uint8)
circ = cv.HoughCircles(im, cv.HOUGH_GRADIENT, 10, 10,param1=10,param2=10)

circles = np.uint16(np.around(circ))


fig, ax = plt.subplots() # note we must use plt.subplots, not plt.subplot
ax.imshow(im.T)
for i in circles[0,:]:
# draw the outer circle
    print(i)
    ax.scatter(i[1],i[0],color='red')
# draw the center of the circle
#circle2 = ax.Circle((i[1],i[0]),2,color='red',alpha=0.1)
#ax.add_artist(circle1)
#ax.add_artist(circle2)
plt.show()