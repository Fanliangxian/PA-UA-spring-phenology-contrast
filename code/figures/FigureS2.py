"""Supplementary Fig. S2: full ECDF values and support-year counts."""
from pathlib import Path
from collections import Counter
import csv,json,hashlib,sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import StrMethodFormatter
import os, shutil
ROOT=Path(__file__).resolve().parents[2]
OUTPUT=Path(os.environ.get('PHENOLOGY_OUTPUT', str(ROOT/'reproduced'))).resolve()
H=OUTPUT/'figures'/'FigureS2'
H.mkdir(parents=True,exist_ok=True)
for _source in (ROOT/'data/figure_inputs'/'FigureS2').iterdir():
 if _source.is_file():shutil.copy2(_source,H/_source.name)
OBS=ROOT/'data/summary'
inputs=[OBS/n for n in ['figure_source_data_v01.json','support_year_distribution.csv','Table1_descriptive_support.csv','independent_reconciliation_v01.json']]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
hashes={str(p):sha(p) for p in inputs}
d=json.loads(inputs[0].read_text(encoding='utf-8'))
assert json.loads(inputs[3].read_text(encoding='utf-8'))['status']=='INDEPENDENT_SQL_AND_RATIONAL_RECONCILIATION_PASS'
groups={r['group']:r for r in d['groups']}
for r in csv.DictReader(inputs[2].open(encoding='utf-8-sig',newline='')):
 for k,v in r.items():
  if k!='group':assert abs(float(v)-float(groups[r['group']][k]))<1e-12
support=list(csv.DictReader(inputs[1].open(encoding='utf-8-sig',newline='')))
assert len(support)==len(d['support_distribution'])==23
for row,r in zip(support,d['support_distribution']):
 assert set(row)==set(r)
 for k,v in row.items():assert int(v)==r[k]
year=np.array([int(r['common_years']) for r in support]);assert np.array_equal(year,np.arange(23))
main=np.array([int(r['main_pairs']) for r in support]);strict=np.array([int(r['strict_pairs']) for r in support])
assert main.sum()==strict.sum()==18862 and main[0]==0 and strict[0]==5
assert (year*main).sum()==403981 and (year*strict).sum()==382773
assert main[-1]==14180 and strict[-1]==10405
counters={};cdf_rows=[]
for key,n,group in [('ALL',18862,'main_all'),('COMPLETE22',14180,'main_complete22'),('INCOMPLETE',4682,'main_incomplete')]:
 r=d['cdf'][key];v=np.asarray(r['value'],float);c=np.asarray(r['count'],int)
 assert len(v)==len(c) and np.isfinite(v).all() and np.all(np.diff(v)>0) and np.all(c>0)
 assert r['n']==c.sum()==n and -60<=v.min() and v.max()<=60
 assert v.min()==groups[group]['min'] and v.max()==groups[group]['max']
 cum=c.cumsum()/n;assert np.all(np.diff(cum)>0) and cum[-1]==1
 counters[key]=Counter(dict(zip(v.tolist(),c.tolist())))
 for x,count,fraction in zip(v,c,cum):cdf_rows.append(dict(cohort=key,pairwise_mean_days=float(x),pair_count=int(count),cumulative_fraction=float(fraction)))
assert counters['COMPLETE22']+counters['INCOMPLETE']==counters['ALL']
with (H/'FigS2_ECDF_source_v01.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(cdf_rows[0]));w.writeheader();w.writerows(cdf_rows)
source_support=[dict(common_years=int(x),main_pairs=int(m),strict_pairs=int(s)) for x,m,s in zip(year,main,strict)]
with (H/'FigS2_support_source_v01.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(source_support[0]));w.writeheader();w.writerows(source_support)
BLUE='#4260CF';MAGENTA='#AD1A60';GRAY='#68727A'
plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['DejaVu Sans'],
 'font.size':8,'axes.titlesize':9,'axes.labelsize':8,'xtick.labelsize':7,'ytick.labelsize':7,
 'legend.fontsize':7,'svg.fonttype':'none','pdf.fonttype':42,'savefig.dpi':600,
 'axes.linewidth':.65,'svg.hashsalt':'phenology4-layout-v02-FigS2-v01','savefig.facecolor':'white'})
WIDTH_MM=183
fig=plt.figure(figsize=(WIDTH_MM/25.4,145/25.4))
ax=fig.add_axes([.12,.585,.835,.265])
for key,color,style,label in [('ALL',GRAY,'-','All pairs (18,862)'),('COMPLETE22',BLUE,'--','Complete 22 years (14,180)'),('INCOMPLETE',MAGENTA,':','Incomplete records (4,682)')]:
 r=d['cdf'][key];v=np.asarray(r['value']);c=np.asarray(r['count'])
 # Constant CDF tails extend to the axis limits; no observations are added.
 ax.step(np.r_[-60,v,60],np.r_[0,c.cumsum()/r['n'],1],where='post',color=color,ls=style,lw=1.25,label=label)
ax.axvline(0,color='#999999',ls='--',lw=.7,zorder=0)
ax.set(xlim=(-60,60),ylim=(0,1.03),xticks=[-60,-40,-20,0,20,40,60],yticks=[0,.25,.5,.75,1],
 xlabel='Pairwise mean UA − PA (days)',ylabel='Cumulative fraction of pairs')
ax.set_title('a  Full distributions by record completeness',loc='left',fontweight='bold',pad=11)
ax.grid(axis='y',color='#E2E2E2',lw=.4)
for s in ['top','right']:ax.spines[s].set_visible(False)
fig.legend(*ax.get_legend_handles_labels(),loc='center',bbox_to_anchor=(.54,.493),ncols=3,frameon=False,columnspacing=1.1,handlelength=2)

ax=fig.add_axes([.12,.155,.835,.24])
ax.bar(year-.19,main,width=.38,color=BLUE,label='Main QA')
ax.bar(year+.19,strict,width=.38,color=MAGENTA,label='Strict QA')
ax.set(xlim=(-.6,22.8),ylim=(0,16100),xticks=np.arange(0,23,2),yticks=[0,5000,10000,15000],
 xlabel='Common supported years (2003–2024)',ylabel='Pairs')
ax.yaxis.set_major_formatter(StrMethodFormatter('{x:,.0f}'))
ax.set_title('b  Support retained by quality filter',loc='left',fontweight='bold',pad=11)
for s in ['top','right']:ax.spines[s].set_visible(False)
ax.grid(axis='y',color='#E2E2E2',lw=.4);ax.set_axisbelow(True)
ax.annotate('Strict QA: 5 pairs\nwith zero supported years',xy=(.19,5),xytext=(3.2,4800),
 fontsize=7.5,color=MAGENTA,ha='left',va='center',arrowprops=dict(arrowstyle='->',color=MAGENTA,lw=.7))
ax.text(21.81,main[-1]+350,'14,180',ha='right',va='bottom',fontsize=7,color=BLUE)
ax.text(22.19,strict[-1]+350,'10,405',ha='center',va='bottom',fontsize=7,color=MAGENTA)
ax.text(.035,.86,'Both profiles account for all 18,862 original pairs',transform=ax.transAxes,fontsize=7.5)
fig.legend(*ax.get_legend_handles_labels(),loc='lower center',bbox_to_anchor=(.54,.056),ncols=2,frameon=False,columnspacing=2)
fig.text(.5,.98,'Record completeness and quality-dependent observation support',ha='center',fontweight='bold',fontsize=10)
fig.text(.5,.023,'Zero strict support means an undefined strict-filter pair mean; it does not mean a zero date difference.',ha='center',fontsize=7,color=GRAY)

# Remove empty header space while preserving physical panel sizes and data positions.
import xml.etree.ElementTree as _ET
_old_a_y=50.653543  # Frozen layout scalar; provenance in layout_parameters.json.
_title=next(t for t in fig.texts if abs(t.get_fontsize()-10)<.01)
_top_baseline_pt=10.629921
_baseline_gap_pt=24.7007875
_old_h=fig.get_size_inches()[1]*72
_cut=_old_a_y-_top_baseline_pt-_baseline_gap_pt
_new_h=_old_h-_cut
_ratio=_old_h/_new_h
_axes_positions=[(a,a.get_position().frozen()) for a in fig.axes]
_text_positions=[(t,t.get_position()) for t in fig.texts]
_legend_positions=[(l,l.get_bbox_to_anchor().transformed(fig.transFigure.inverted()).frozen()) for l in fig.legends]
fig.set_size_inches(fig.get_size_inches()[0],_new_h/72,forward=True)
for _ax,_p in _axes_positions:
 _ax.set_position([_p.x0,_p.y0*_ratio,_p.width,_p.height*_ratio])
for _t,(_x,_y) in _text_positions:
 _t.set_position((_x,_y*_ratio))
_title.set_position((_title.get_position()[0],1-_top_baseline_pt/_new_h))
for _leg,_p in _legend_positions:
 _leg.set_bbox_to_anchor((_p.x0,_p.y0*_ratio,_p.width,_p.height*_ratio),transform=fig.transFigure)
if False:
 # Retain this figure's descriptive-symbol legend in the reduced header gap.
 for _leg in fig.legends:
  _leg.set_loc('center')
  _leg.set_bbox_to_anchor((.53,1-20.8/_new_h),transform=fig.transFigure)

fig.canvas.draw();renderer=fig.canvas.get_renderer();outside=[]
for t in fig.findobj(matplotlib.text.Text):
 if t.get_visible() and t.get_text():
  b=t.get_window_extent(renderer)
  if b.width and b.height and (b.x0<0 or b.y0<0 or b.x1>fig.bbox.x1 or b.y1>fig.bbox.y1):outside.append(t.get_text())
fig.savefig(H/'FigS2_distributions_v03.svg',metadata={'Date':None})
fig.savefig(H/'FigS2_distributions_v03.pdf',metadata={'CreationDate':None})
fig.savefig(H/'FigS2_distributions_v03.png',dpi=600)
fig.savefig(H/'FigS2_distributions_v03.tiff',dpi=600,pil_kwargs={'compression':'tiff_lzw'})
fig.savefig(H/'FigS2_distributions_preview_v03.png',dpi=300)
plt.close(fig)
assert hashes=={str(p):sha(p) for p in inputs}
roundtrip=list(csv.DictReader((H/'FigS2_ECDF_source_v01.csv').open(encoding='utf-8-sig',newline='')))
assert len(roundtrip)==len(cdf_rows)
for original,r in zip(cdf_rows,roundtrip):
 assert original['cohort']==r['cohort']
 for k in ['pairwise_mean_days','pair_count','cumulative_fraction']:assert float(r[k])==original[k]
roundtrip_support=list(csv.DictReader((H/'FigS2_support_source_v01.csv').open(encoding='utf-8-sig',newline='')))
assert [{k:int(v) for k,v in r.items()} for r in roundtrip_support]==source_support
report=dict(status='COMPLETE_FIGS2_DISTRIBUTIONS_V02',source_sha256=hashes,sources_unchanged=True,
 cohort_counts=dict(ALL=18862,COMPLETE22=14180,INCOMPLETE=4682),
 full_CDF_values_and_frequencies_retained=True,cohort_frequency_partition_exact=True,
 support_CSV_and_JSON_all_fields_match=True,source_tables_roundtrip_exact=True,
 main_and_strict_support_denominator=18862,main_pair_years=403981,strict_pair_years=382773,
 main_zero_support=0,strict_zero_support=5,main_full22=14180,strict_full22=10405,
 histogram_zero_bins_retained=True,no_bar_height_adjustment=True,
 ECDF_source_rows=len(cdf_rows),support_source_rows=23,text_outside_canvas=outside,
 width_mm=183,height_mm=145,bitmap_dpi=600,date_level_reads=False,random_execution=False,new_model=False,
 runtime=dict(python=sys.version.split()[0],numpy=np.__version__,matplotlib=matplotlib.__version__),manuscript_references_updated=False)
(H/'verification_v03.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':report['status'],'outside_canvas':outside,'CDF_source_rows':len(cdf_rows)}))

_verification=H/('figure_verification_v03.json' if (H/'figure_verification_v03.json').exists() else 'verification_v03.json')
_v=json.loads(_verification.read_text(encoding='utf-8'))
_v.update(status=_v['status'].replace('_V02','_V03').replace('_V01','_V03'),height_mm=_new_h/72*25.4,header_title_to_panel_a_baseline_gap_pt=_baseline_gap_pt,
 header_title_baseline_from_top_pt=_top_baseline_pt,presentation_only_revision=True)
_verification.write_text(json.dumps(_v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
