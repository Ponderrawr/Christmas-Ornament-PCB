"""
Wreath front plate generator (heightmap -> watertight binary STL).
Usage:  python wreath_plate.py [output.stl]
Requires: numpy
Edit the CONFIG block to match your board.
"""
import numpy as np, struct, os, sys
# ===================== CONFIG (mm) =====================
RES    = 0.15                 # grid resolution
R      = 40.0                 # plate radius (matches PCB)
BASE   = 1.6                  # background thickness (glows when lit)
LEDS   = [(16.256,19.939),(28.575,-0.762),(16.129,-22.987),
          (-16.383,-22.987),(-28.575,-1.016),(-16.129,20.066)]
MOUNTS = [(-25.781,25.654),(-25.781,-25.781),(25.654,25.654),(25.527,-25.781)]
MOUNT_HOLE = 1.35             # M2.5 clearance radius
POCKET_R, POCKET_D = 3.0, 0.8 # back-side light pocket over each LED -> 0.8 mm shell
HUB_R  = 2.9                  # flat glowing hub around each LED
BERRY_R, BERRY_OFF = 0.75, 1.30   # 3 x 1.5 mm through-holes per LED
EW     = 0.35                 # edge smoothing width
OUT    = sys.argv[1] if len(sys.argv) > 1 else 'Wreath_Plate_v4.stl'
# =======================================================
rng = np.random.default_rng(11)
xs = np.arange(-R-0.3, R+0.3+1e-9, RES); n=len(xs)
X,Y = np.meshgrid(xs,xs); Rr=np.hypot(X,Y)
H = np.full(X.shape, BASE)
def sm(x): x=np.clip(x,0,1); return x*x*(3-2*x)
def box(cx,cy,ext):
    i0=max(0,int((cx-ext-xs[0])/RES)); i1=min(n,int((cx+ext-xs[0])/RES)+2)
    j0=max(0,int((cy-ext-xs[0])/RES)); j1=min(n,int((cy+ext-xs[0])/RES)+2)
    return slice(j0,j1),slice(i0,i1)
def raise_(sl, z):   H[sl]=np.maximum(H[sl], z)
def blend(sl, z, w): H[sl]=H[sl]*(1-w)+z*w

def capsule(x0,y0,x1,y1,w0,w1,h,zoff):
    sl=box((x0+x1)/2,(y0+y1)/2,np.hypot(x1-x0,y1-y0)/2+max(w0,w1))
    px,py=X[sl],Y[sl]; dx,dy=x1-x0,y1-y0; L2=dx*dx+dy*dy+1e-9
    t=np.clip(((px-x0)*dx+(py-y0)*dy)/L2,0,1)
    d=np.hypot(px-(x0+t*dx),py-(y0+t*dy)); hw=(w0+(w1-w0)*t)/2
    prof=np.sqrt(np.clip(1-(d/hw)**2,0,1))
    raise_(sl, BASE+(zoff+h*prof)*sm((hw-d)/min(EW,hw.max())))

# rim: lip + beaded border
lip=np.clip((Rr-39.3)/0.7,0,1)
H=np.maximum(H, BASE+0.7*np.sin(np.pi*lip)**0.7*(Rr>39.3))
for k in range(150):
    a=2*np.pi*k/150; cx,cy=38.55*np.cos(a),38.55*np.sin(a)
    sl=box(cx,cy,0.8); d=np.hypot(X[sl]-cx,Y[sl]-cy)
    raise_(sl, BASE+0.55*np.clip(1-(d/0.6)**2,0,1)**0.6)
H=np.maximum(H, BASE+0.25*np.exp(-((Rr-37.6)/0.18)**2))

# pine branches
def branch(r0,th0,length,direction,zoff):
    steps=int(length/0.7); drift=rng.uniform(-0.12,0.12)
    pts=np.array([((r0+drift*s*0.7)*np.cos(th0+direction*s*0.7/r0),
                   (r0+drift*s*0.7)*np.sin(th0+direction*s*0.7/r0)) for s in range(steps+1)])
    for s in range(steps): capsule(*pts[s],*pts[s+1],0.6,0.5,0.4,zoff)
    for s in range(1,steps):
        frac=s/steps; p=pts[s]; tg=pts[s+1]-pts[s-1]; tg/=np.linalg.norm(tg)
        a0=np.arctan2(tg[1],tg[0]); L=(3.3-1.6*frac)*rng.uniform(0.85,1.1)
        for side in (1,-1):
            a=a0+side*np.radians(rng.uniform(38,52))
            capsule(p[0],p[1],p[0]+L*np.cos(a),p[1]+L*np.sin(a),0.75,0.4,0.8,zoff)
for row,(rr,nb) in enumerate([(19.6,16),(23.0,19),(26.8,22),(30.6,24),(33.6,26)]):
    for k in range(nb):
        th=2*np.pi*(k+0.5*(row%2))/nb+rng.uniform(-0.05,0.05)
        branch(rr+rng.uniform(-0.5,0.5),th,rng.uniform(8,11.5),-1,rng.uniform(0.1,0.6))

# holly leaves around each LED
def holly(cx,cy,ang,L,W,h,zoff):
    sl=box(cx,cy,L/2+0.8); x=X[sl]-cx; y=Y[sl]-cy
    c,s=np.cos(ang),np.sin(ang); u=x*c+y*s; v=-x*s+y*c; t=2*u/L
    env=(W/2)*np.clip(1-t**2,0,None)**0.5
    hw=env*(0.62+0.38*np.abs(np.cos(3.0*np.pi*(t+1)/2)))
    sd=np.maximum(np.abs(v)-hw, np.abs(u)-L/2)
    with np.errstate(divide='ignore',invalid='ignore'):
        prof=np.sqrt(np.clip(1-(v/np.where(hw>0,hw,1))**2,0,1))**0.6*np.clip(1-t**2,0,1)**0.3
    vein=0.3*sm((0.25-np.abs(v))/0.15)*(np.abs(t)<0.9)
    z=BASE+(zoff+h*prof-vein)
    raise_(sl, BASE+(z-BASE)*sm(-sd/EW))
for (lx,ly) in LEDS:
    th=np.arctan2(ly,lx)
    for da in (70,190,310):
        a=th+np.radians(da+rng.uniform(-10,10)); L=rng.uniform(8.0,9.0)
        d=HUB_R+L/2-0.5
        holly(lx+d*np.cos(a),ly+d*np.sin(a),a,L,rng.uniform(4.6,5.0),1.2,0.6)

# pinecone at 6 o'clock
pcx,pcy,pa=0.0,-29.0,np.pi/2
sl=box(pcx,pcy,5.5); x=X[sl]-pcx; y=Y[sl]-pcy
u=x*np.cos(pa)+y*np.sin(pa); v=-x*np.sin(pa)+y*np.cos(pa)
e=np.sqrt((u/4.6)**2+(v/2.9)**2)
g=np.minimum(np.abs(np.sin(np.pi*(u*1.1+np.abs(v)*0.9))),np.abs(np.sin(np.pi*(u*1.1-np.abs(v)*0.9))))
blend(sl, BASE+1.0+1.3*np.sqrt(np.clip(1-e**2,0,1))-0.45*sm((0.35-g)/0.25), sm((1-e)*2.9/EW))

# bow at 12 o'clock
bx,by=0.0,28.6
def bowloop(cx,cy,a,b,tilt):
    sl=box(cx,cy,a+0.6); x=X[sl]-cx; y=Y[sl]-cy; c,s=np.cos(tilt),np.sin(tilt)
    u=x*c+y*s; v=-x*s+y*c; e=np.sqrt((u/a)**2+(v/b)**2)
    inner=np.sqrt(((u-0.25*a)/(0.45*a))**2+(v/(0.42*b))**2)
    z=BASE+1.4+1.0*np.sqrt(np.clip(1-e**2,0,1))-0.8*sm(1-inner)
    z-=0.25*sm((np.abs(np.sin(5*np.arctan2(v,u-0.9*a)))-0.9)/0.08)
    blend(sl, z, sm((1-e)*min(a,b)/EW))
bowloop(bx-5.0,by+0.4,5.2,3.1,np.radians(195))
bowloop(bx+5.0,by+0.4,5.2,3.1,np.radians(-15))
def tail(x0,y0,x1,y1,w):
    sl=box((x0+x1)/2,(y0+y1)/2,np.hypot(x1-x0,y1-y0)/2+w); px,py=X[sl],Y[sl]
    dx,dy=x1-x0,y1-y0; L=np.hypot(dx,dy); t=((px-x0)*dx+(py-y0)*dy)/L**2
    perp=((px-x0)*(-dy)+(py-y0)*dx)/L; hw=w/2*(1+0.25*t)
    sd=np.maximum.reduce([np.abs(perp)-hw, -t*L, (t-1)*L])
    sd=np.maximum(sd, np.where(t>0.85, (t-0.85)*6*hw-np.abs(perp), -9))
    z=BASE+1.3+0.6*np.sqrt(np.clip(1-(perp/hw)**2,0,1))+0.35*np.sin(np.clip(t,0,1)*np.pi*2.2)
    blend(sl, z, sm(-sd/EW))
tail(-1.0,by-1.0,-5.2,by-12.5,2.8)
tail( 1.0,by-1.0, 5.4,by-12.0,2.8)
sl=box(bx,by,2.6); d=np.hypot(X[sl]-bx,(Y[sl]-by)/1.15)
blend(sl, BASE+2.0+0.9*np.sqrt(np.clip(1-(d/2.1)**2,0,1)), sm((2.1-d)/EW))

# center sparkles
for (sx,sy,ss) in [(0,2,3.2),(-7.5,-5,1.8),(7,-6,1.6),(-6,9,1.4),(6.5,8,1.2),(0,-11,1.3),(-11,2,1.0),(11,1,1.1)]:
    sl=box(sx,sy,ss+0.3); q=(np.abs(X[sl]-sx)**(2/3)+np.abs(Y[sl]-sy)**(2/3))/ss**(2/3)
    raise_(sl, BASE+0.6*np.clip(1-q,0,1)**1.3)

# flat LED hubs + screw seats
for (lx,ly) in LEDS:
    sl=box(lx,ly,HUB_R+0.6); d=np.hypot(X[sl]-lx,Y[sl]-ly); blend(sl, BASE, sm((HUB_R-d)/0.4+0.5))
for (mx,my) in MOUNTS:
    sl=box(mx,my,3.4); d=np.hypot(X[sl]-mx,Y[sl]-my); blend(sl, BASE+0.6, sm((2.9-d)/0.4+0.5))

# bottom surface: light pockets
B=np.zeros_like(H)
for (lx,ly) in LEDS: B=np.where(np.hypot(X-lx,Y-ly)<POCKET_R, POCKET_D, B)

# cell mask + exact circular holes
cc=xs[:-1]+RES/2; CX,CY=np.meshgrid(cc,cc)
M=np.hypot(CX,CY)<=R; circles=[(0,0,R)]
for (lx,ly) in LEDS:
    th=np.arctan2(ly,lx)
    for da in (90,210,330):
        hx,hy=lx+BERRY_OFF*np.cos(th+np.radians(da)),ly+BERRY_OFF*np.sin(th+np.radians(da))
        M&=np.hypot(CX-hx,CY-hy)>BERRY_R; circles.append((hx,hy,BERRY_R))
for (mx,my) in MOUNTS:
    M&=np.hypot(CX-mx,CY-my)>MOUNT_HOLE; circles.append((mx,my,MOUNT_HOLE))
Mp=np.pad(M,1); inn=Mp[:-1,:-1].astype(int)+Mp[:-1,1:]+Mp[1:,:-1]+Mp[1:,1:]
BV=(inn>0)&(inn<4); VX,VY=X.copy(),Y.copy(); best=np.full(X.shape,np.inf)
for (cx,cy,r) in circles:
    sl=box(cx,cy,r+2*RES) if r<10 else (slice(None),slice(None))
    d=np.hypot(X[sl]-cx,Y[sl]-cy); err=np.abs(d-r); take=BV[sl]&(err<1.2*RES)&(err<best[sl])
    best[sl]=np.where(take,err,best[sl])
    VX[sl]=np.where(take,cx+(X[sl]-cx)*r/np.maximum(d,1e-9),VX[sl])
    VY[sl]=np.where(take,cy+(Y[sl]-cy)*r/np.maximum(d,1e-9),VY[sl])
J,I=np.nonzero(M)
for it in range(20):          # undo any snap that would fold a cell
    P=lambda i,j: np.stack([VX[j,i],VY[j,i]],-1)
    a,b,c,d=P(I,J),P(I+1,J),P(I+1,J+1),P(I,J+1)
    cz=lambda p,q,r:(q[:,0]-p[:,0])*(r[:,1]-p[:,1])-(q[:,1]-p[:,1])*(r[:,0]-p[:,0])
    bad=(cz(a,b,c)<=1e-6)|(cz(a,c,d)<=1e-6)
    if not bad.any(): break
    for (di,dj) in ((0,0),(1,0),(1,1),(0,1)):
        VX[J[bad]+dj,I[bad]+di]=X[J[bad]+dj,I[bad]+di]; VY[J[bad]+dj,I[bad]+di]=Y[J[bad]+dj,I[bad]+di]

# mesh
def V(i,j,top=True): return np.stack([VX[j,i],VY[j,i],(H if top else B)[j,i]],-1)
a,b,c,d=V(I,J),V(I+1,J),V(I+1,J+1),V(I,J+1)
diag=np.abs(H[J,I]-H[J+1,I+1]) <= np.abs(H[J,I+1]-H[J+1,I])
t1=np.where(diag[:,None,None],np.stack([a,b,c],1),np.stack([a,b,d],1))
t2=np.where(diag[:,None,None],np.stack([a,c,d],1),np.stack([b,c,d],1))
ab,bb,cb,db=V(I,J,0),V(I+1,J,0),V(I+1,J+1,0),V(I,J+1,0)
tris=[t1,t2,np.stack([ab,cb,bb],1),np.stack([ab,db,cb],1)]
def walls(di,dj,ia,ja,ib,jb):
    sel=~Mp[J+1+dj,I+1+di]; i_,j_=I[sel],J[sel]
    A0,B0=V(i_+ia,j_+ja,0),V(i_+ib,j_+jb,0); AT,BT=V(i_+ia,j_+ja),V(i_+ib,j_+jb)
    tris.extend([np.stack([A0,B0,BT],1),np.stack([A0,BT,AT],1)])
walls(-1,0,0,1,0,0); walls(1,0,1,0,1,1); walls(0,-1,0,0,1,0); walls(0,1,1,1,0,1)
T=np.concatenate(tris).astype(np.float32); Nm=np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0])
with open(OUT,'wb') as f:
    f.write(b'Wreath front plate v4'.ljust(80,b' ')); f.write(struct.pack('<I',len(T)))
    rec=np.zeros(len(T),dtype=[('n','<f4',3),('v','<f4',(3,3)),('a','<u2')])
    rec['n']=Nm/(np.linalg.norm(Nm,axis=1,keepdims=True)+1e-12); rec['v']=T; f.write(rec.tobytes())
print(f'{OUT}: {len(T)} triangles, {os.path.getsize(OUT)/1e6:.1f} MB, max height {H.max():.2f} mm')
