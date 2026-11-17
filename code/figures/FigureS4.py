"""Figure 4: a nested-window map with marginal and within-pair summaries."""
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
from matplotlib.ticker import FuncFormatter
import os, shutil
ROOT=Path(__file__).resolve().parents[2]
OUTPUT=Path(os.environ.get('PHENOLOGY_OUTPUT', str(ROOT/'reproduced'))).resolve()
H=OUTPUT/'figures'/'FigureS4'
H.mkdir(parents=True,exist_ok=True)
for _source in (ROOT/'data/figure_inputs'/'FigureS4').iterdir():
 if _source.is_file():shutil.copy2(_source,H/_source.name)
SOURCE=H/'Figure4_window_changes_source_v01.csv'
VERIFY=H/'data_verification_v01.json'
WORLD=ROOT/'assets/basemap/naturalearth_lowres.shp'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
check=json.loads(VERIFY.read_text(encoding='utf-8'))
assert check['status']=='PASS_WINDOW_MAP_AND_SUMMARY_RECONCILIATION' and sha(SOURCE)==check['output']['sha256']
tracked=[SOURCE,VERIFY]+[WORLD.with_suffix(s) for s in ('.shp','.shx','.dbf','.prj')]
before={str(p):sha(p) for p in tracked}
rows=list(csv.DictReader(SOURCE.open(encoding='utf-8-sig',newline='')))
assert len(rows)==18862 and [r['pair_id'] for r in rows]==sorted({r['pair_id'] for r in rows})
lon=np.array([float(r['ua_longitude']) for r in rows]);lat=np.array([float(r['ua_latitude']) for r in rows])
value=np.array([float(r['recent_minus_full_days']) for r in rows])
assert np.isfinite(value).all() and np.isfinite(lon).all() and np.isfinite(lat).all()
assert all(float(r['recent_minus_full_days'])==float(r['mean_recent_days'])-float(r['mean_full_days']) for r in rows)
assert sum(int(r['complete22']) for r in rows)==14180
g=check['groups'];c=check['changes']
world=gpd.read_file(WORLD,engine='pyogrio')
assert world.crs.to_epsg()==4326 and world.geometry.is_valid.all() and not world.geometry.isna().any() and not world.geometry.is_empty.any()
BLUE='#4260CF';MAGENTA='#AD1A60';GRAY='#68727A'
plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['DejaVu Sans'],
 'font.size':8,'axes.titlesize':9,'axes.labelsize':8,'xtick.labelsize':7,'ytick.labelsize':7.5,
 'legend.fontsize':7,'svg.fonttype':'none','pdf.fonttype':42,'savefig.dpi':600,
 'axes.linewidth':.65,'svg.hashsalt':'phenology4-layout-v02-Fig4-v01','savefig.facecolor':'white'})
WIDTH_MM=183
fig=plt.figure(figsize=(WIDTH_MM/25.4,160/25.4))
ax=fig.add_axes([.085,.60,.88,.27])
world.plot(ax=ax,color='#F3F3F3',edgecolor='#BFBFBF',linewidth=.25,zorder=0)
cmap=LinearSegmentedColormap.from_list('change',[(0,MAGENTA),(.25,'#BD4C82'),(.45,'#D995B5'),
 (.50,'#F0F0F0'),(.55,'#AFBDEA'),(.75,'#667EDB'),(1,BLUE)])
norm=Normalize(vmin=-20,vmax=20)
assert norm.vmin<=value.min() and norm.vmax>=value.max()
pts=ax.scatter(lon,lat,c=value,cmap=cmap,norm=norm,s=2.5,edgecolors='#A3A3A3',linewidths=.06,rasterized=True,zorder=3)
ax.set(xlim=(-180,180),ylim=(18,74),xticks=np.arange(-150,180,50),yticks=[30,45,60],aspect='auto')
ax.xaxis.set_major_formatter(FuncFormatter(lambda x,p:'0°' if x==0 else f'{abs(x):g}°'+('E' if x>0 else 'W')))
ax.yaxis.set_major_formatter(FuncFormatter(lambda y,p:f'{y:g}°N'))
ax.grid(color='#DCDCDC',lw=.35)
for y in [23.44,66.56]:
 ax.axhline(y,color='#999999',ls='--',lw=.6,zorder=1)
 ax.text(.985,y+.45,f'{y:.2f}°N',transform=ax.get_yaxis_transform(),ha='right',va='bottom',fontsize=7,color='#555555',zorder=8,bbox={'facecolor':'white','edgecolor':'none','alpha':.9,'pad':1})
ax.set_title('a  Changes within matched pairs across averaging windows',loc='left',fontweight='bold',pad=9)
ax.text(.015,.86,'18,862 pairs · recent minus full window',transform=ax.transAxes,fontsize=7,
 bbox={'facecolor':'white','edgecolor':'none','alpha':.9,'pad':2})
ax.legend(handles=[Line2D([],[],marker='o',mfc='#BBBBBB',mec='#777777',ms=3.5,ls='',label='One UA–PA pair')],loc='upper right',bbox_to_anchor=(.80,.98),frameon=True,facecolor='white',edgecolor='none',framealpha=.9)
cax=fig.add_axes([.24,.52,.60,.016])
cb=fig.colorbar(pts,cax=cax,orientation='horizontal',ticks=[-20,-10,0,10,20])
cb.set_label('Within-pair change, 2013–2024 minus 2003–2024 (days)',fontsize=8,labelpad=4)
cax.text(-.045,.5,'More negative\nUA − PA contrast',transform=cax.transAxes,ha='right',va='center',color=MAGENTA,fontsize=7)
cax.text(1.045,.5,'More positive\nUA − PA contrast',transform=cax.transAxes,ha='left',va='center',color=BLUE,fontsize=7)
fmt=lambda v:f'{v:.2f}'.replace('-','−')
def summary(ax,letter,title,items,labels,colors,limits,xlabel,endpoints=False):
 for y,(r,color) in enumerate(zip(items,colors)):
  lo,q1,med,q3,hi=[r[k] for k in ['q05','q25','median','q75','q95']]
  ax.plot([lo,hi],[y,y],color=color,lw=1.3)
  ax.plot([lo,hi],[y,y],marker='|',color=color,ms=5,ls='')
  ax.plot([q1,q3],[y,y],color=color,lw=5,solid_capstyle='butt')
  ax.plot(med,y,marker='|',color='black',ms=9,ls='',mew=1.1)
  ax.plot(r['mean'],y-.16,marker='D',mfc='white',mec=color,ms=4,ls='')
  ax.text(1.04,y,fmt(r['mean']),transform=ax.get_yaxis_transform(),ha='left',va='center',fontsize=7.5)
  if endpoints:
   for x in [lo,hi]:ax.text(x,y+.24,fmt(x),ha='center',va='top',fontsize=7,color=color)
 ax.text(1.04,1.04,'Mean\n(days)',transform=ax.transAxes,ha='left',va='bottom',fontsize=7)
 ax.axvline(0,color='#999999',ls='--',lw=.7,zorder=0)
 ax.set(yticks=range(len(items)),yticklabels=labels,ylim=(len(items)-.35,-.55),xlim=limits,xlabel=xlabel)
 ax.tick_params(axis='y',length=0,pad=9)
 for spine in ['top','right','left']:ax.spines[spine].set_visible(False)
 ax.set_title(f'{letter}  {title}',loc='left',fontweight='bold',pad=12)
 ax.tick_params(axis='y',labelsize=7)
ax=fig.add_axes([.245,.17,.24,.235])
summary(ax,'b','Window comparisons',
 [g[k] for k in ['main_all','recent_native','main_complete22','recent_complete22']],
 ['All: full\n(n = 18,862)','All: recent\n(n = 18,862)',
  'Complete: full\n(n = 14,180)','Complete: recent\n(n = 14,180)'],
 [BLUE,MAGENTA,BLUE,MAGENTA],(-16,16),'Pairwise mean UA − PA\n(days)')
ax.axhline(1.5,color='#DDDDDD',lw=.6)
ax=fig.add_axes([.735,.17,.20,.235])
summary(ax,'c','Pairwise changes',
 [c[k] for k in ['recent_vs_full','recent_vs_full_complete22']],
 ['All pairs\n(n = 18,862)','Complete\n(n = 14,180)'],[BLUE,GRAY],(-4,4),
 'Within-pair change\nrecent − full (days)',endpoints=True)
handles=[Line2D([],[],color=GRAY,lw=1.3,label='5th–95th percentiles'),Line2D([],[],color=GRAY,lw=5,label='25th–75th percentiles'),
 Line2D([],[],marker='|',color='black',ls='',ms=8,label='Median'),Line2D([],[],marker='D',mfc='white',mec='black',ls='',ms=3.5,label='Mean')]
fig.text(.5,.98,'Similar overall means accompany within-pair changes across windows',ha='center',fontweight='bold',fontsize=10)
fig.legend(handles=handles,loc='center',bbox_to_anchor=(.53,.074),ncols=4,frameon=False,handlelength=1.3,columnspacing=1.1)
fig.text(.5,.043,'The recent window is nested within the full window; changes describe sensitivity to the averaging period.',ha='center',fontsize=7)
fig.text(.5,.020,'Percentile ranges describe observed variation, not confidence intervals or fitted temporal trends.',ha='center',fontsize=7,color=GRAY)

# Remove empty header space while preserving physical panel sizes and data positions.
import xml.etree.ElementTree as _ET
_old_a_y=49.96063  # Frozen layout scalar; provenance in layout_parameters.json.
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
fig.savefig(H/'Figure4_window_changes_v03.svg',metadata={'Date':None})
fig.savefig(H/'Figure4_window_changes_v03.pdf',metadata={'CreationDate':None})
fig.savefig(H/'Figure4_window_changes_v03.png',dpi=600)
fig.savefig(H/'Figure4_window_changes_v03.tiff',dpi=600,pil_kwargs={'compression':'tiff_lzw'})
fig.savefig(H/'Figure4_window_changes_preview_v03.png',dpi=300)
plt.close(fig)
assert before=={str(p):sha(p) for p in tracked}
summaries=[]
for panel,collection in [('b',g),('c',c)]:
 for key,r in collection.items():summaries.append(dict(panel=panel,condition=key,**r))
(H/'Figure4_summary_source_v01.json').write_text(json.dumps(summaries,indent=2)+'\n',encoding='utf-8')
report=dict(status='COMPLETE_FIGURE4_WINDOW_CHANGES_V02',source_sha256=before,sources_unchanged=True,
 map_points=18862,map_location='Frozen UA endpoint, one point per pair',point_order='ascending pair_id',
 color_scale=dict(type='linear',min=-20,max=20,actual_min=float(value.min()),actual_max=float(value.max()),clipped_values=0),
 no_sampling=True,no_jitter=True,no_interpolation=True,paired_changes_directly_computed=True,
 map_is_not_temporal_trend=True,intervals='Empirical percentiles, not uncertainty intervals',
 panel_b_limits=[-16,16],panel_c_limits=[-4,4],width_mm=183,height_mm=160,bitmap_dpi=600,
 text_outside_canvas=outside,random_execution=False,new_model=False,manuscript_references_updated=False)
(H/'figure_verification_v03.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':report['status'],'outside_canvas':outside}))

_verification=H/('figure_verification_v03.json' if (H/'figure_verification_v03.json').exists() else 'verification_v03.json')
_v=json.loads(_verification.read_text(encoding='utf-8'))
_v.update(status=_v['status'].replace('_V02','_V03').replace('_V01','_V03'),height_mm=_new_h/72*25.4,header_title_to_panel_a_baseline_gap_pt=_baseline_gap_pt,
 header_title_baseline_from_top_pt=_top_baseline_pt,presentation_only_revision=True)
_verification.write_text(json.dumps(_v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
