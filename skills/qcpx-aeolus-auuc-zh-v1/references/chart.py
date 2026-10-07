import csv, math, shutil
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

BASE=Path('output/uplift_6641741')
rows100=list(csv.DictReader(open(BASE/'uplift_100bin_sep_snapshot.csv')))
rows20=list(csv.DictReader(open(BASE/'uplift_20bin_sep_snapshot.csv')))
treatments=[20,25,30,35,40]
colors={20:'#5377a0',25:'#d6616b',30:'#68a25a',35:'#f2b347',40:'#a97aa0'}
core=[]; diag=[]; plotdata={}

def ranks(a):
    order=np.argsort(a); out=np.empty(len(a),float); out[order]=np.arange(1,len(a)+1); return out

def f4(x):
    return float(f'{float(x):.4g}')

for t in treatments:
    r100=sorted([r for r in rows100 if int(r['treatment'])==t], key=lambda r:int(r['bucket_100']))
    nt=sum(int(r['treatment_n']) for r in r100); nc=sum(int(r['control_n']) for r in r100)
    pt=sum(float(r['treatment_positive']) for r in r100); pc=sum(float(r['control_positive']) for r in r100)
    tcvr=pt/nt; ccvr=pc/nc; ate=tcvr-ccvr; rel=ate/ccvr
    N=nt+nc; cumn=0; cumt=0.; cumc=0.; xs=[0.]; curve=[0.]; random=[0.]
    for r in r100:
        cumn += int(r['n']); cumt += float(r['treatment_positive']); cumc += float(r['control_positive'])
        x=cumn/N; xs.append(x); curve.append(cumt/nt-cumc/nc); random.append(ate*x)
    raw=float(np.trapz(curve,xs)); random_auuc=ate/2; normalized=raw/ate if ate else float('nan')
    adjusted=raw-random_auuc
    r20=sorted([r for r in rows20 if int(r['treatment'])==t], key=lambda r:int(r['bucket_20']))
    n=np.array([int(r['n']) for r in r20],float)
    tn=np.array([int(r['treatment_n']) for r in r20],float)
    cn=np.array([int(r['control_n']) for r in r20],float)
    shares=tn/n; overall=nt/N
    obs=np.array([float(r['observed_uplift']) for r in r20])
    pred=np.array([float(r['predicted_uplift']) for r in r20])
    w=n/n.sum()
    share_cv=float(np.std(shares)/np.mean(shares)); maxdev=float(np.max(np.abs(shares-overall)))
    mae=float(np.sum(w*np.abs(pred-obs))); bias=float(np.sum(w*(pred-obs)))
    pearson=float(np.corrcoef(pred,obs)[0,1]); spearman=float(np.corrcoef(ranks(pred),ranks(obs))[0,1])
    sign_rate=float(np.mean(np.sign(pred)==np.sign(obs)))
    core.append({'折扣对比组':f'{t} vs 15','normalized_AUUC':f4(normalized),'总体_CVR_uplift':f4(ate),'实验组_CVR':f4(tcvr),'15基准组_CVR':f4(ccvr),'CVR相对提升幅度':f4(rel),'样本数_实验组':nt,'样本数_15组':nc,'raw_AUUC':f4(raw),'random_AUUC':f4(random_auuc),'adjusted_AUUC':f4(adjusted)})
    diag.append({'折扣对比组':f'{t} vs 15','实验组总体占比':f4(overall),'20桶占比CV':f4(share_cv),'最大占比偏差_pp':f4(maxdev*100),'值准_MAE':f4(mae),'值准偏差_预测减实际':f4(bias),'Pearson_r':f4(pearson),'Spearman_rho':f4(spearman),'同号率':f4(sign_rate)})
    plotdata[t]={'xs':np.array(xs),'curve':np.array(curve),'random':np.array(random),'obs':obs,'pred':pred,'shares':shares,'overall':overall}

def write_csv(path, rows):
    with open(path,'w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
write_csv(BASE/'01_SIPW_9月核心指标汇总.csv',core)
write_csv(BASE/'02_SIPW_9月均匀度与值准诊断.csv',diag)
shutil.copyfile(BASE/'uplift_100bin_sep_snapshot.csv',BASE/'03_SIPW_9月100桶AUUC明细.csv')
shutil.copyfile(BASE/'uplift_20bin_sep_snapshot.csv',BASE/'04_SIPW_9月20桶诊断明细.csv')
shutil.copyfile(BASE/'uplift_100bin_sep_snapshot.sql',BASE/'05_SIPW_9月100桶SQL.sql')
shutil.copyfile(BASE/'uplift_20bin_sep_snapshot.sql',BASE/'06_SIPW_9月20桶SQL.sql')

plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Noto Sans CJK SC','Source Han Sans SC','Hiragino Sans GB','Microsoft YaHei','DejaVu Sans'],'axes.spines.top':False,'axes.spines.right':False,'axes.grid':True,'grid.color':'#e5e7eb','grid.linewidth':0.8,'grid.alpha':0.9,'axes.axisbelow':True})
fig,axes=plt.subplots(3,5,figsize=(4966/300,3097/300),dpi=300)
fig.patch.set_facecolor('white')
fig.suptitle('QCPX SIPW Uplift 诊断矩阵',fontsize=20,fontweight='bold',y=0.995)
fig.text(0.5,0.947,'模型：shop_qcpx_t3_sipw_0813_streaming_r6641741_0 | 对照组：15 | 2026年9月1日至10日',ha='center',fontsize=10,color='#4b5563')
for c,t in enumerate(treatments):
    d=plotdata[t]; col=colors[t]
    ax=axes[0,c]
    ax.plot(d['xs']*100,d['curve'],color=col,lw=2.8,label='策略排序')
    ax.plot(d['xs']*100,d['random'],color='#8c8c8c',lw=1.8,ls='--',label='随机排序')
    ax.set_title(f'{t} vs 15',fontsize=13,fontweight='bold',color=col,pad=10)
    ax.set_xlabel('累计样本占比 (%)',fontsize=8); ax.set_ylabel('累计增益',fontsize=8)
    ax.text(0.03,0.94,f"AUUC = {core[c]['normalized_AUUC']:.4f}",transform=ax.transAxes,va='top',fontsize=9,color=col,fontweight='bold',bbox=dict(boxstyle='round,pad=0.3',fc='white',ec=col,lw=1.2))
    ax.legend(loc='lower right',fontsize=7,frameon=False)
    ax=axes[1,c]; x=np.arange(1,21); width=.38
    ax.bar(x-width/2,d['obs']*100,width,color='#5377a0',label='观测值')
    ax.bar(x+width/2,d['pred']*100,width,color='#c4b5d8',label='预测值')
    ax.set_xlabel('预测 uplift 分位桶',fontsize=8); ax.set_ylabel('Uplift（百分点）',fontsize=8)
    ax.set_xticks([1,5,10,15,20]); ax.tick_params(labelsize=7)
    if c==4: ax.legend(loc='upper right',fontsize=7,frameon=False)
    ax=axes[2,c]
    base_share=(1-d['shares'])*100; treat_share=d['shares']*100
    ax.bar(x,base_share,color='#5377a0',width=.78,label='对照组 15')
    ax.bar(x,treat_share,bottom=base_share,color='#cd5c5c',width=.78,label=f'实验组 {t}')
    ax.axhline(d['overall']*100,color='#7f7f7f',lw=1.7,ls='--',label='全量实验组占比')
    ax.set_ylim(0,100); ax.set_xlabel('预测 uplift 分位桶',fontsize=8); ax.set_ylabel('样本占比 (%)',fontsize=8)
    ax.set_xticks([1,5,10,15,20]); ax.tick_params(labelsize=7)
    if c==4: ax.legend(loc='lower right',bbox_to_anchor=(0.98,0.02),fontsize=6.2,frameon=False)
axes[0,0].text(-0.38,0.5,'AUUC',transform=axes[0,0].transAxes,rotation=90,ha='center',va='center',fontsize=14,fontweight='bold',color='#374151')
axes[1,0].text(-0.38,0.5,'校准',transform=axes[1,0].transAxes,rotation=90,ha='center',va='center',fontsize=14,fontweight='bold',color='#374151')
axes[2,0].text(-0.38,0.5,'均匀度',transform=axes[2,0].transAxes,rotation=90,ha='center',va='center',fontsize=14,fontweight='bold',color='#374151')
fig.text(0.5,0.012,'数据：DeepInsight 冻结快照 | server_time 与 req_time：2026-09-01 至 2026-09-10 | 仅随机样本 | 标签：head_68',ha='center',fontsize=9,color='#6b7280')
plt.subplots_adjust(left=.07,right=.985,top=.88,bottom=.065,wspace=.34,hspace=.42)
out=BASE/'SIPW_9月Uplift综合诊断.png'; fig.savefig(out,dpi=300,facecolor='white'); plt.close(fig)
from PIL import Image
im=Image.open(out)
print('IMAGE',out,im.size)
print('CORE')
for r in core: print(r)
print('DIAG')
for r in diag: print(r)
