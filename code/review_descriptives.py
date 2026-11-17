"""Deterministic revision summaries from archived sufficient statistics, no RNG.
Run from the extracted revision package: python code/review_descriptives.py
Does not read annual SOS, rematch sites, bootstrap, or estimate latent equivalence.
"""
from pathlib import Path
import json, hashlib
import numpy as np
import pandas as pd

H = Path(__file__).resolve().parents[1]
D = H / 'data'
import os
O = Path(os.environ.get('PHENOLOGY_OUTPUT', str(H/'reproduced'))).resolve()/'tables'
O.mkdir(parents=True,exist_ok=True)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def stats(x):
    x=np.asarray(x,float)
    q=np.quantile(x,[.05,.25,.5,.75,.95],method='linear')
    return dict(n=len(x),mean=float(x.mean()),q05=float(q[0]),q25=float(q[1]),median=float(q[2]),q75=float(q[3]),q95=float(q[4]))
def main():
    w=pd.read_csv(D/'pair_window_summaries.csv')
    f=pd.read_csv(D/'frozen_pairs.csv')
    assert len(w)==len(f)==18862 and w.pair_id.is_unique and f.pair_id.is_unique
    x=w.merge(f,on='pair_id',validate='one_to_one',suffixes=('','_design'))
    assert len(x)==18862
    assert np.allclose(x.mean_full_days,x.sum_full_days/x.n_full,atol=1e-12,rtol=0)
    assert np.allclose(x.mean_recent_days,x.sum_recent_days/x.n_recent,atol=1e-12,rtol=0)
    assert (x.n_full==22).equals(x.complete22==1)
    assert x.n_full.sum()==403981 and x.n_recent.sum()==220767
    signs=[]
    for label,mask in [('UA earlier',x.sum_full_days<0),('exact zero',x.sum_full_days==0),('UA later',x.sum_full_days>0)]:
        signs.append(dict(category=label,count=int(mask.sum()),denominator=len(x),percent=float(mask.mean()*100)))
    for delta in (3,5,7):
        mask=x.sum_full_days.abs()<=delta*x.n_full
        signs.append(dict(category=f'absolute observed mean <= {delta} days',count=int(mask.sum()),denominator=len(x),percent=float(mask.mean()*100)))
    pd.DataFrame(signs).to_csv(O/'Table_S4_direction_and_tolerances.csv',index=False)
    c=x[x.complete22==1].copy()
    assert len(c)==14180 and (c.n_recent==12).all()
    c['sum_early_days']=c.sum_full_days-c.sum_recent_days
    c['mean_early_days']=c.sum_early_days/10
    c['recent_minus_early_days']=c.mean_recent_days-c.mean_early_days
    assert np.allclose(c.recent_minus_early_days,2.2*c.recent_minus_full_days,atol=2e-14,rtol=1e-14)
    c[['pair_id','sum_early_days','sum_recent_days','mean_early_days','mean_recent_days','recent_minus_early_days']].to_csv(O/'complete_pair_periods.csv',index=False)
    a=np.sign(c.sum_early_days).astype(int); b=np.sign(c.sum_recent_days).astype(int)
    trans=[dict(early_sign=i,recent_sign=j,count=int(((a==i)&(b==j)).sum()),denominator=len(c)) for i in (-1,0,1) for j in (-1,0,1)]
    pd.DataFrame(trans).to_csv(O/'Table_S5_sign_transitions.csv',index=False)
    # Average ranks for exact ties. No p values or independence-based intervals.
    rho=float(np.corrcoef(c.mean_early_days.rank(method='average'),c.mean_recent_days.rank(method='average'))[0,1])
    same=int(((a==b)&(a!=0)).sum()); opposite=int((a*b==-1).sum()); zeros=int(((a==0)|(b==0)).sum())
    out=dict(full=stats(x.mean_full_days),early_complete=stats(c.mean_early_days),recent_complete=stats(c.mean_recent_days),
      recent_minus_early=stats(c.recent_minus_early_days),spearman_rho=rho,
      pearson_r=float(np.corrcoef(c.mean_early_days,c.mean_recent_days)[0,1]),
      same_nonzero_sign=same,opposite_nonzero_sign=opposite,at_least_one_exact_zero=zeros,
      denominator=len(c),same_nonzero_sign_percent_all=100*same/len(c),same_sign_percent_nonzero=100*same/(len(c)-zeros),
      direction_and_tolerances=signs,analysis_status='post-review descriptive extension',
      interpretation='Non-overlapping years, not independent replicates; no latent error decomposition, trend inference or ecological equivalence.')
    assert same+opposite+zeros==len(c)
    groups=[]; balance=[]
    cov=['latitude','longitude','elevation_m','slope_deg','mat_c','log_map_mm','vegetation_fraction']
    for kind,labels in [('all',{'All':np.ones(len(x),bool)}),('tier',{z:x.pft_tier==z for z in sorted(x.pft_tier.unique())}),
      ('realm',{'Nearctic':x.ua_continental_region==5,'Palearctic':x.ua_continental_region==8,'Unclassified':x.ua_continental_region==-1})]:
        for label,mask in labels.items():
            g=x[mask]
            if len(g)==0:continue
            groups.append(dict(group_type=kind,group=label,percent=100*len(g)/len(x),**stats(g.mean_full_days)))
            for v in cov:
                u=g['ua_'+v].to_numpy(float);p=g['pa_'+v].to_numpy(float)
                den=np.sqrt((u.var(ddof=1)+p.var(ddof=1))/2)
                smd=float((u.mean()-p.mean())/den) if den else None
                balance.append(dict(group_type=kind,group=label,n=len(g),covariate=v,ua_mean=float(u.mean()),pa_mean=float(p.mean()),matched_pooled_sd=float(den),smd=smd))
    pd.DataFrame(groups).to_csv(O/'Table_S6_groups.csv',index=False)
    pd.DataFrame(balance).to_csv(O/'Table_S7_group_balance.csv',index=False)
    # Verify uniqueness of physical native grid coordinates after removing Tier from IDs.
    for role in ['ua','pa']:
        grid=x[role+'_support_unit_id'].str.extract(r'(x\d+_y\d+)$')[0]
        assert grid.notna().all() and grid.is_unique
        assert not x[[role+'_latitude',role+'_longitude']].duplicated().any()
    out['physical_grid_reuse']=False
    (O/'revision_results.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(out,indent=2,ensure_ascii=False))
if __name__=='__main__': main()
