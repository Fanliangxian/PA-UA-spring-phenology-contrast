"""Figure 2: full pair-mean map, histogram and descriptive percentiles."""
from pathlib import Path
import csv,json,hashlib,os
os.environ['PROJ_NETWORK']='OFF'
import numpy as np
import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap,Normalize
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter,PercentFormatter
import os, shutil
ROOT=Path(__file__).resolve().parents[2]
OUTPUT=Path(os.environ.get('PHENOLOGY_OUTPUT', str(ROOT/'reproduced'))).resolve()
H=OUTPUT/'figures'/'Figure2'
H.mkdir(parents=True,exist_ok=True)
for _source in (ROOT/'data/figure_inputs'/'Figure2').iterdir():
 if _source.is_file():shutil.copy2(_source,H/_source.name)
OBS=ROOT/'data/summary'
SOURCE=H/'Figure2_pairwise_mean_source_v01.csv'
WORLD=ROOT/'assets/basemap/naturalearth_lowres.shp'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
check=json.loads((H/'data_verification_v01.json').read_text(encoding='utf-8'))
assert check['status']=='PASS_PAIRWISE_MAP_SOURCE_RECONCILIATION' and sha(SOURCE)==check['output']['sha256']
tracked=[SOURCE,OBS/'figure_source_data_v01.json']+[WORLD.with_suffix(s) for s in ('.shp','.shx','.dbf','.prj')]
before={str(p):sha(p) for p in tracked}
rows=list(csv.DictReader(SOURCE.open(encoding='utf-8-sig',newline='')))
assert len(rows)==18862 and [r['pair_id'] for r in rows]==sorted({r['pair_id'] for r in rows})
lon=np.array([float(r['ua_longitude']) for r in rows]);lat=np.array([float(r['ua_latitude']) for r in rows])
value=np.array([float(r['mean_UA_minus_PA_days']) for r in rows])
assert np.isfinite(value).all() and np.isfinite(lon).all() and np.isfinite(lat).all()
d=json.loads((OBS/'figure_source_data_v01.json').read_text(encoding='utf-8'))
summary=check['summary'];edges=np.array(d['histogram']['edges']);counts=np.array(d['histogram']['counts'])
assert np.array_equal(np.histogram(value,bins=edges)[0],counts)
world=gpd.read_file(WORLD,engine='pyogrio')
assert world.crs.to_epsg()==4326 and world.geometry.is_valid.all() and not world.geometry.is_empty.any() and not world.geometry.isna().any()
UA='#AD1A60';PA='#4260CF';GRAY='#68727A'
plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['DejaVu Sans'],
 'font.size':8,'axes.titlesize':9,'axes.labelsize':8,'xtick.labelsize':7,'ytick.labelsize':7,
 'legend.fontsize':7,'svg.fonttype':'none','pdf.fonttype':42,'savefig.dpi':600,
 'axes.linewidth':.65,'svg.hashsalt':'phenology4-layout-v02-Fig2-v01','savefig.facecolor':'white'})
WIDTH_MM=183
fig=plt.figure(figsize=(WIDTH_MM/25.4,150/25.4))
ax=fig.add_axes([.085,.575,.88,.285])
world.plot(ax=ax,color='#F3F3F3',edgecolor='#BFBFBF',linewidth=.25,zorder=0)
cmap=LinearSegmentedColormap.from_list('UA_PA',[(0,UA),(.25,'#BD4C82'),(.45,'#D995B5'),
 (.50,'#F0F0F0'),(.55,'#AFBDEA'),(.75,'#667EDB'),(1,PA)])
norm=Normalize(vmin=-60,vmax=60)
assert value.min()>=norm.vmin and value.max()<=norm.vmax
pts=ax.scatter(lon,lat,c=value,cmap=cmap,norm=norm,s=2.5,edgecolors='#A3A3A3',linewidths=.06,rasterized=True,zorder=3)
ax.set(xlim=(-180,180),ylim=(18,74),xticks=np.arange(-150,180,50),yticks=[30,45,60],aspect='auto')
ax.xaxis.set_major_formatter(FuncFormatter(lambda x,p:'0°' if x==0 else f'{abs(x):g}°'+('E' if x>0 else 'W')))
ax.yaxis.set_major_formatter(FuncFormatter(lambda y,p:f'{y:g}°N'))
ax.grid(color='#DCDCDC',lw=.35)
for y in [23.44,66.56]:
 ax.axhline(y,color='#999999',ls='--',lw=.6,zorder=1)
 ax.text(.985,y+.45,f'{y:.2f}°N',transform=ax.get_yaxis_transform(),ha='right',va='bottom',fontsize=7,color='#555555',zorder=8,bbox={'facecolor':'white','edgecolor':'none','alpha':.9,'pad':1})
ax.set_title('a  Spatial distribution of pairwise mean differences',loc='left',fontweight='bold',pad=9)
ax.text(.015,.86,'18,862 pairs · 2003–2024',transform=ax.transAxes,fontsize=7,
 bbox={'facecolor':'white','edgecolor':'none','alpha':.9,'pad':2})
cax=fig.add_axes([.235,.493,.60,.018])
cb=fig.colorbar(pts,cax=cax,orientation='horizontal',ticks=[-60,-40,-20,0,20,40,60])
cb.set_label('Pairwise mean UA − PA spring onset difference (days)',fontsize=8,labelpad=4)
cax.text(-.045,.5,'UA earlier',ha='right',va='center',transform=cax.transAxes,color=UA,fontsize=7)
cax.text(1.045,.5,'UA later',ha='left',va='center',transform=cax.transAxes,color=PA,fontsize=7)

ax=fig.add_axes([.10,.15,.415,.205])
ax.bar(edges[:-1],counts/18862,width=np.diff(edges),align='edge',
 color=[UA if edge<0 else PA for edge in edges[:-1]],alpha=.80,linewidth=0)
ax.axvline(0,color=GRAY,lw=.7,ls='--')
ax.set(xlim=(-60,60),xticks=[-60,-30,0,30,60],xlabel='Pairwise mean UA − PA (days)',ylabel='Pairs per 1-day bin')
ax.yaxis.set_major_formatter(PercentFormatter(1,decimals=0))
ax.spines['top'].set_visible(False);ax.spines['right'].set_visible(False)
ax.set_title('b  Full observed distribution',loc='left',fontweight='bold',pad=10)
ax.text(.035,.96,'Mean = −0.99 days\nMedian = −0.77 days',transform=ax.transAxes,va='top',fontsize=7)

ax=fig.add_axes([.655,.15,.31,.205])
lo,q1,med,q3,hi=[summary[k] for k in ['q05','q25','median','q75','q95']]
ax.axvline(0,color=GRAY,lw=.7,ls='--')
ax.plot([lo,hi],[0,0],color=GRAY,lw=1.2)
ax.plot([lo,hi],[0,0],color=GRAY,marker='|',ms=6,ls='')
ax.plot([q1,q3],[0,0],color=GRAY,lw=5,solid_capstyle='butt')
ax.plot(med,0,color='black',marker='|',ms=10,ls='')
ax.plot(summary['mean'],.16,marker='D',ms=4,mfc='white',mec='black',ls='')
for x,y,text in [(lo,-.16,'−12.24'),(hi,-.16,'9.77'),(q1,.20,'−4.45'),(q3,.20,'2.64')]:
 ax.text(x,y,text,ha='center',va='center',fontsize=7)
ax.text(.5,.88,'Central 50%: −4.45 to 2.64 days',transform=ax.transAxes,ha='center',fontsize=7)
ax.set(xlim=(-16,16),ylim=(-.65,.9),yticks=[],xticks=[-15,0,15],xlabel='Pairwise mean UA − PA (days)')
for spine in ['top','right','left']:ax.spines[spine].set_visible(False)
ax.set_title('c  Centre and spread',loc='left',fontweight='bold',pad=10)
handles=[Line2D([],[],color=GRAY,lw=1.2,label='5th–95th percentiles'),Line2D([],[],color=GRAY,lw=5,label='25th–75th percentiles'),
 Line2D([],[],marker='|',color='black',ms=8,ls='',label='Median'),Line2D([],[],marker='D',mfc='white',mec='black',ms=3.5,ls='',label='Mean')]
fig.legend(handles=handles,loc='lower center',bbox_to_anchor=(.53,.047),ncols=4,frameon=False,handlelength=1.3,columnspacing=1.1)
fig.text(.5,.975,'A small mean advance at UA sites coexists with broad pairwise variation',ha='center',fontweight='bold',fontsize=10)
fig.text(.5,.018,'Percentile ranges describe observed variation; they are not confidence intervals.',ha='center',fontsize=7,color=GRAY)

# Remove empty header space while preserving physical panel sizes and data positions.
import xml.etree.ElementTree as _ET
_old_a_y=50.527559  # Frozen layout scalar; provenance in layout_parameters.json.
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
  q=t.get_window_extent(renderer)
  if q.width and q.height and (q.x0<0 or q.y0<0 or q.x1>fig.bbox.x1 or q.y1>fig.bbox.y1):outside.append(t.get_text())
fig.savefig(H/'Figure2_pairwise_mean_v03.svg',metadata={'Date':None})
fig.savefig(H/'Figure2_pairwise_mean_v03.pdf',metadata={'CreationDate':None})
fig.savefig(H/'Figure2_pairwise_mean_v03.png',dpi=600)
fig.savefig(H/'Figure2_pairwise_mean_v03.tiff',dpi=600,pil_kwargs={'compression':'tiff_lzw'})
fig.savefig(H/'Figure2_pairwise_mean_preview_v03.png',dpi=300)
plt.close(fig)
assert before=={str(p):sha(p) for p in tracked}
report=dict(status='COMPLETE_FIGURE2_V02',sources_sha256=before,sources_unchanged=True,
 map_points=18862,map_location='Frozen UA endpoint; one point per pair',point_order='ascending frozen pair_id',
 no_sampling=True,no_jitter=True,no_interpolation=True,color_scale=dict(type='linear',min=-60,max=60,zero_centered=True,clipped_values=0),
 actual_range=[float(value.min()),float(value.max())],histogram_count=int(counts.sum()),histogram_bin_width_days=1,
 quantile_ranges='Empirical spread, not confidence or credible intervals',width_mm=183,height_mm=150,bitmap_dpi=600,
 text_outside_canvas=outside,outcome_scope='Existing released main-filter means only',random_execution=False,new_model=False,
 manuscript_references_updated=False)
(H/'figure_verification_v03.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':report['status'],'outside_canvas':outside}))

_verification=H/('figure_verification_v03.json' if (H/'figure_verification_v03.json').exists() else 'verification_v03.json')
_v=json.loads(_verification.read_text(encoding='utf-8'))
_v.update(status=_v['status'].replace('_V02','_V03').replace('_V01','_V03'),height_mm=_new_h/72*25.4,header_title_to_panel_a_baseline_gap_pt=_baseline_gap_pt,
 header_title_baseline_from_top_pt=_top_baseline_pt,presentation_only_revision=True)
_verification.write_text(json.dumps(_v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
