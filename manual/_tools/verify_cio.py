# 겸용 펌프(옥내소화전 + 옥외소화전) v5.1.0 독립 검증 — 앱 엔진(index.html <script id="cio-engine"> cioCalc)과 따로 짠 파이썬 구현을 무작위 대조
# usage: python3 -I verify_cio.py <index.html> [건수]
#  · 원문: NFPC 102(제2025-25호) 제4조①② · 제5조①3호 · 4호 · 제6조① · 제12조①② / NFTC 102(제2026-34호) 2.1.1 · 2.1.2 · 2.3.5
#           NFPC 109(제2025-28호) 제4조① · 제5조①3호 · 제6조②③ · 제11조①② / NFTC 109(제2026-9호) 2.3.3.2 · 2.8.1 · 2.8.2 / NFTC 604 2.1.1 · 2.1.3
#  · KS 강관 내경 = 외경 − 2 × 두께 (KS D 3507 · KS D 3562 Sch40) — 이 파일에서 다시 계산 · 참고값은 앱과 같은 값을 따로 옮겨 적음
import sys,json,math,random,subprocess,os,tempfile
html=open(sys.argv[1],encoding='utf-8').read(); N=int(sys.argv[2]) if len(sys.argv)>2 else 50000
a=html.index('<script id="cio-engine">')+len('<script id="cio-engine">'); eng=html[a:html.index('</script>',a)]
OD={'3507':{25:(34.0,3.2),32:(42.7,3.5),40:(48.6,3.5),50:(60.5,3.8),65:(76.3,4.2),80:(89.1,4.2),100:(114.3,4.5),125:(139.8,4.5),150:(165.2,5.0),200:(216.3,5.8)},
    '3562':{25:(34.0,3.4),32:(42.7,3.6),40:(48.6,3.7),50:(60.5,3.9),65:(76.3,5.2),80:(89.1,5.5),100:(114.3,6.0),125:(139.8,6.6),150:(165.2,7.1),200:(216.3,8.2)}}
INNER={'SCH10':({d:round(o-2*t,2) for d,(o,t) in OD['3507'].items()},120),'SCH40':({d:round(o-2*t,2) for d,(o,t) in OD['3562'].items()},120),
 'STS':({25:27.6,32:36.8,40:42.8,50:54.8,65:70.0,80:85.0,100:108.2,125:133.4,150:160.0,200:210.0},150),
 'CPVC':({25:26.6,32:35.1,40:40.9,50:52.5,65:62.7,80:79.4,100:101.6,125:127.0,150:154.1,200:203.2},150)}
FIT={25:[0.9,0.54,1.5,0.27,0.18,7.5,4.5,2.0],32:[1.2,0.72,1.8,0.36,0.24,10.5,5.4,2.5],40:[1.5,0.90,2.1,0.45,0.30,13.8,6.5,3.1],50:[2.1,1.20,3.0,0.60,0.39,16.5,8.4,4.0],
 65:[2.4,1.30,3.6,0.75,0.48,19.5,10.2,4.6],80:[3.0,1.80,4.5,0.90,0.60,24.0,12.0,5.7],100:[4.2,2.40,6.3,1.20,0.81,37.5,16.5,7.6],125:[5.1,3.00,7.5,1.50,0.99,42.0,21.0,10.0],
 150:[6.0,3.60,9.0,1.80,1.20,49.5,24.0,12.0],200:[6.5,3.70,14.0,4.00,1.40,70.0,33.0,15.0]}
HHOSE={1:(26,None),2:(12,None),3:(7,None),4:(3,None),5:(0,14)}; OHOSE={1:8,2:4}
K={1:1.1,2:1.15}; HP=[3,5,7.5,10,15,20,25,30,40,50,60,75,100,125,150,200]; FK=['e90','e45','teeB','teeS','gate','ball','angle','check']
MPA=9.80665e-3
def loss(segs,pt):
    inner,C=INNER[pt]; F=0.0; vo=0
    for s in segs:
        Di=inner[s['dia']]; L=s['len']+sum(s[k]*FIT[s['dia']][i] for i,k in enumerate(FK))
        F+=10.67*L*(s['flow']/60000)**1.852/(C**1.852*(Di/1000)**4.87)
        v=(s['flow']/60000)/(math.pi*(Di/2000)**2); vo+= v>4
    return F,vo
def py(h,hs,o,os_,c,cs,bf):
    Fc,v1=loss(cs,c['pipeType'])
    hA=min(2 if bf==1 else 5,max(1,h['hydrants'])); hQ=130*hA; hD=hA*{1:2.6,2:5.2,3:7.8}[bf]
    hF,v2=loss(hs,h['pipeType']); r,fx=HHOSE[h['hoseType']]; hG=fx if fx is not None else r*h['hoseLen']/100
    hJ=math.ceil((h['actualHead']+Fc+hF+hG+17)*1.1)
    oA=min(2,max(1,o['hydrants'])); oQ=350*oA; oD=7*oA
    oF,v3=loss(os_,o['pipeType']); oG=OHOSE[o['hoseType']]*o['hoseLen']/100
    oJ=math.ceil((o['actualHead']+Fc+oF+oG+25)*1.1)
    Q=hQ+oQ; D=hD+oD                      # 합산 — NFPC 102 제12조 · NFPC 109 제11조 (단서 해당 없음)
    R=0 if c['roofEx'] else hD/3; Dt=D+R  # 옥상수조는 옥내소화전 유효수량에만
    J=max(hJ,oJ); P=0.163*(Q/1000)*J*K[c['transType']]/(c['pumpEff']/100); hp=P*1.341; Php=next((x for x in HP if x>=hp), math.ceil(hp/5)*5)
    S=J*MPA; ok=S<1.2 or all(x=='SCH40' for x in (h['pipeType'],o['pipeType'],c['pipeType']))
    Th=(J-h['lowHead']-hG)*MPA; To=(J-o['lowHead']-oG)*MPA
    return dict(Fc=Fc,hJ=hJ,oJ=oJ,hD=hD,oD=oD,Q=Q,D=D,Dt=Dt,J=J,Pkw=P,Php=Php,S=S,ok=ok,prvH=Th>0.7,prvO=To>0.7,vo=v1+v2+v3,hi=bf>1)
random.seed(20261016); cases=[]
def segs(fl,sizes):
    return [dict(flow=random.choice(fl),dia=random.choice(sizes),len=round(random.uniform(0,80),1),**{k:random.randint(0,6) for k in FK}) for _ in range(random.randint(1,4))]
for _ in range(N):
    bf=random.randint(1,3); P=list(INNER)
    h=dict(hydrants=random.randint(1,7),actualHead=round(random.uniform(5,150),1),hoseLen=random.choice([15,30]),hoseType=random.randint(1,5),pipeType=random.choice(P),lowHead=round(random.uniform(-10,30),1))
    o=dict(hydrants=random.randint(1,4),actualHead=round(random.uniform(-10,40),1),hoseLen=random.choice([15,30,45]),hoseType=random.randint(1,2),pipeType=random.choice(P),lowHead=round(random.uniform(-15,20),1))
    c=dict(pumpDia=125,pumpEff=random.randint(10,80),transType=random.randint(1,2),roofEx=random.randint(0,1),pipeType=random.choice(P))
    cases.append((h,segs([130*k for k in range(1,6)],[40,50,65,80,100,125,150,200]),o,segs([350,700],[40,50,65,80,100,125,150,200]),c,segs([10*k for k in range(30,200)],[65,80,100,125,150,200]),bf))
tf=os.path.join(tempfile.gettempdir(),'_cio_cases.json'); json.dump(cases,open(tf,'w'))
js=os.path.join(tempfile.gettempdir(),'_cio_run.js')
open(js,'w',encoding='utf-8').write("var window=globalThis;\n"+eng+"\nconst cs=require(process.argv[2]);process.stdout.write(JSON.stringify(cs.map(a=>{const x=cioCalc(...a);"
 "return {Fc:x.Fc,hJ:x.H.J,oJ:x.O.J,hD:x.H.D,oD:x.O.D,Q:x.C.Clpm,D:x.C.D,Dt:x.C.Dt,J:x.C.J,Pkw:x.C.Pkw,Php:x.C.Php,S:x.C.Pdis,ok:x.C.pipePressOK,prvH:x.H.needPRV,prvO:x.O.needPRV,vo:x.C.velOverN,hi:x.C.hiRise}})));")
E=json.loads(subprocess.check_output(['node','--max-old-space-size=4096',js,tf])); bad=[]
for i,(cs,e) in enumerate(zip(cases,E)):
    p=py(*cs)
    for k in p:
        if isinstance(p[k],bool) or k in('vo','Php','hJ','oJ','J','Q'):
            if p[k]!=e[k]: bad.append((i,k,p[k],e[k])); break
        elif abs(p[k]-e[k])>1e-9*max(1,abs(p[k])): bad.append((i,k,p[k],e[k])); break
print(f'검사 {N}건 · 불일치 {len(bad)}건'); print(bad[:5])
print(f'판정 분포 — 고층 경고 {sum(1 for e in E if e["hi"])}건 · 배관 부적합 {sum(1 for e in E if not e["ok"])}건 · 옥내 감압 {sum(1 for e in E if e["prvH"])}건 · 옥외 감압 {sum(1 for e in E if e["prvO"])}건 · 유속 초과 포함 {sum(1 for e in E if e["vo"])}건 · 옥외 전양정 채택 {sum(1 for e in E if e["oJ"]>e["hJ"])}건')
