"""
Light-transmission test coupon: 7 steps (0.4 - 3.2 mm), tick bumps count the step.
Print in your plate filament, hold over a lit LED, pick the thickness you like.
Usage: python thickness_coupon.py [output.stl]
"""
import numpy as np, struct, sys
OUT = sys.argv[1] if len(sys.argv) > 1 else 'Thickness_Test_Coupon.stl'
steps=[0.4,0.8,1.2,1.6,2.0,2.4,3.2]; w=6.0; D=14.0; tris=[]
def quad(p,q,r,s): tris.extend([[p,q,r],[p,r,s]])
def block(x0,y0,x1,y1,z0,z1,bottom=True):
    v=[(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]
    faces=[(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]+([(0,3,2,1)] if bottom else [])
    for f in faces: quad(*[v[i] for i in f])
for k,t in enumerate(steps):
    block(k*w,0,(k+1)*w,D,0,t)
    for m in range(k+1):
        bx=k*w+0.8+m*0.75; block(bx,D-2.0,bx+0.45,D-0.8,t,t+0.4)
T=np.array(tris,dtype=np.float32); N=np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0])
with open(OUT,'wb') as f:
    f.write(b'thickness coupon'.ljust(80,b' ')); f.write(struct.pack('<I',len(T)))
    rec=np.zeros(len(T),dtype=[('n','<f4',3),('v','<f4',(3,3)),('a','<u2')])
    rec['n']=N/np.linalg.norm(N,axis=1,keepdims=True); rec['v']=T; f.write(rec.tobytes())
print(OUT,'written')
