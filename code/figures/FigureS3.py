"""Supplementary Fig. S3: support-only maps with strict-zero callouts."""
from pathlib import Path
import csv,json,hashlib,os
os.environ['PROJ_NETWORK']='OFF'
import numpy as np
import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap,BoundaryNorm
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter
import os, shutil
ROOT=Path(__file__).resolve().parents[2]
OUTPUT=Path(os.environ.get('PHENOLOGY_OUTPUT', str(ROOT/'reproduced'))).resolve()
H=OUTPUT/'figures'/'FigureS3'
H.mkdir(parents=True,exist_ok=True)
for _source in (ROOT/'data/figure_inputs'/'FigureS3').iterdir():
 if _source.is_file():shutil.copy2(_source,H/_source.name)
SOURCE=H/'FigS3_support_source_v01.csv';VERIFY=H/'data_verification_v01.json'
WORLD=ROOT/'assets/basemap/naturalearth_lowres.shp'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
check=json.loads(VERIFY.read_text(encoding='utf-8'))
assert check['status']=='PASS_SUPPORT_MAP_SOURCE_RECONCILIATION' and sha(SOURCE)==check['output_sha256']
tracked=[SOURCE,VERIFY]+[WORLD.with_suffix(s) for s in ['.shp','.shx','.dbf','.prj']]
before={str(p):sha(p) for p in tracked}
rows=list(csv.DictReader(SOURCE.open(encoding='utf-8-sig',newline='')))
assert len(rows)==18862 and [r['pair_id'] for r in rows]==sorted({r['pair_id'] for r in rows})
lon=np.array([float(r['ua_longitude']) for r in rows]);lat=np.array([float(r['ua_latitude']) for r in rows])
main=np.array([int(r['n_main']) for r in rows]);strict=np.array([int(r['n_strict']) for r in rows]);loss=main-strict
assert all(int(r['years_removed_by_strict'])==v for r,v in zip(rows,loss))
zero=strict==0;assert zero.sum()==5 and (loss>=0).all()
world=gpd.read_file(WORLD,engine='pyogrio')
assert world.crs.to_epsg()==4326 and world.geometry.is_valid.all() and not world.geometry.isna().any() and not world.geometry.is_empty.any()
BLUE='#4260CF';MAGENTA='#AD1A60';GRAY='#68727A'
plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['DejaVu Sans'],
 'font.size':8,'axes.titlesize':9,'axes.labelsize':8,'xtick.labelsize':7,'ytick.labelsize':7,
 'legend.fontsize':7,'svg.fonttype':'none','pdf.fonttype':42,'savefig.dpi':600,
 'axes.linewidth':.65,'svg.hashsalt':'phenology4-layout-v02-FigS3-v01','savefig.facecolor':'white'})
WIDTH_MM=183
fig=plt.figure(figsize=(WIDTH_MM/25.4,180/25.4))
axes=[fig.add_axes(p) for p in [[.085,.605,.88,.265],[.085,.17,.88,.265]]]
positions={1:(-112,63),2:(-62,60),3:(55,62)}
inset_bounds=[.035,.12,.12,.32]
# This Pacific inset footprint covers no frozen sample position on the overview.
x0,x1=-180+360*inset_bounds[0],-180+360*(inset_bounds[0]+inset_bounds[2])
y0,y1=18+56*inset_bounds[1],18+56*(inset_bounds[1]+inset_bounds[3])
assert not ((lon>=x0)&(lon<=x1)&(lat>=y0)&(lat<=y1)).any()
zero_indices=np.flatnonzero(zero)
assert [int(rows[j]['zero_support_label']) for j in zero_indices]==[1,2,3,4,5]
cmap_main=LinearSegmentedColormap.from_list('support_blue',['#EEF0FC',BLUE],N=23)
cmap_loss=LinearSegmentedColormap.from_list('removed_magenta',[(0,'#E8E8E8'),(.05,'#F2D6E3'),(1,MAGENTA)],N=21)
norm_main=BoundaryNorm(np.arange(-.5,23.5),cmap_main.N)
norm_loss=BoundaryNorm(np.arange(-.5,21.5),cmap_loss.N)
configs=[(main,cmap_main,norm_main,'a  Common supported years under the main filter',.535,
 'Common supported years, main QA (2003–2024)',[0,5,10,15,20,22]),
 (loss,cmap_loss,norm_loss,'b  Common supported years removed by strict filtering',.100,
 'Years removed, main QA minus strict QA (2003–2024)',[0,5,10,15,20])]
zoom_counts=[]
for ax,(values,cmap,norm,title,cy,label,ticks) in zip(axes,configs):
 world.plot(ax=ax,color='#F3F3F3',edgecolor='#BFBFBF',linewidth=.25,zorder=0)
 pts=ax.scatter(lon,lat,c=values,cmap=cmap,norm=norm,s=2.5,edgecolors='#A3A3A3',linewidths=.06,rasterized=True,zorder=3)
 ax.set(xlim=(-180,180),ylim=(18,74),xticks=np.arange(-150,180,50),yticks=[30,45,60],aspect='auto')
 ax.xaxis.set_major_formatter(FuncFormatter(lambda x,p:'0°' if x==0 else f'{abs(x):g}°'+('E' if x>0 else 'W')))
 ax.yaxis.set_major_formatter(FuncFormatter(lambda y,p:f'{y:g}°N'))
 ax.grid(color='#DCDCDC',lw=.35)
 for y in [23.44,66.56]:ax.axhline(y,color='#999999',ls='--',lw=.6,zorder=1)
 ax.set_title(title,loc='left',fontweight='bold',pad=10)
 ax.text(.015,.91,'18,862 matched pairs',transform=ax.transAxes,fontsize=7,
   bbox={'facecolor':'white','edgecolor':'none','alpha':.9,'pad':2})
 ax.scatter(lon[zero],lat[zero],s=31,facecolors='none',edgecolors='black',linewidths=.85,zorder=6)
 for j in zero_indices[:3]:
  number=int(rows[j]['zero_support_label'])
  ax.annotate(str(number),xy=(lon[j],lat[j]),xytext=positions[number],ha='center',va='center',
   fontsize=8,fontweight='bold',bbox={'facecolor':'white','edgecolor':'none','alpha':.9,'pad':1},
   arrowprops={'arrowstyle':'-','color':'black','lw':.65},zorder=7)
 ax.annotate('4–5 (inset)',xy=(float(lon[zero_indices[3:]].mean()),float(lat[zero_indices[3:]].mean())),
   xytext=(155,57),ha='center',va='center',fontsize=7,fontweight='bold',
   bbox={'facecolor':'white','edgecolor':'none','alpha':.9,'pad':1},
   arrowprops={'arrowstyle':'-','color':'black','lw':.65},zorder=7)
 inset=ax.inset_axes(inset_bounds,zorder=10)
 world.plot(ax=inset,color='#F3F3F3',edgecolor='#BFBFBF',linewidth=.25,zorder=0)
 zoom=(lon>=142.30)&(lon<=142.80)&(lat>=44.12)&(lat<=44.52)
 zoom_counts.append(int(zoom.sum()))
 inset.scatter(lon[zoom],lat[zoom],c=values[zoom],cmap=cmap,norm=norm,s=9,edgecolors='#777777',linewidths=.2,zorder=2)
 for j,offset in zip(zero_indices[3:],[(-6,7),(6,-8)]):
  inset.scatter([lon[j]],[lat[j]],s=32,facecolors='none',edgecolors='black',linewidths=.85,zorder=5)
  inset.annotate(rows[j]['zero_support_label'],xy=(lon[j],lat[j]),xytext=offset,textcoords='offset points',
    fontsize=6.5,fontweight='bold',ha='center',va='center',zorder=6,
    bbox={'facecolor':'white','edgecolor':'none','alpha':.9,'pad':.7})
 inset.set(xlim=(142.30,142.80),ylim=(44.12,44.52),xticks=[142.4,142.7],yticks=[44.2,44.4],aspect='auto')
 inset.tick_params(labelsize=5.5,length=2,pad=1)
 inset.grid(color='#DDDDDD',lw=.3)
 inset.set_title('Japan: pairs 4–5',fontsize=6.5,pad=3)
 cax=fig.add_axes([.25,cy,.61,.014])
 cb=fig.colorbar(pts,cax=cax,orientation='horizontal',ticks=ticks,spacing='uniform')
 cb.set_label(label,fontsize=8,labelpad=4)
fig.text(.5,.98,'Spatial distribution of common support and quality-related year loss',ha='center',fontweight='bold',fontsize=10)
axes[0].legend(handles=[Line2D([],[],marker='o',mfc='none',mec='black',ms=5,ls='',label='Strict zero support: 5 pairs (labels 1–5)')],
 loc='upper right',bbox_to_anchor=(.995,.995),frameon=True,facecolor='white',edgecolor='none',framealpha=.92)
fig.text(.5,.040,'Dots locate paired comparisons at their UA sites. Black rings mark pairs with no strict-filter support.',ha='center',fontsize=7)
fig.text(.5,.018,'Panel b: zero means no supported years removed. No phenological date difference is displayed.',ha='center',fontsize=7,color=GRAY)

# Remove empty header space while preserving physical panel sizes and data positions.
import xml.etree.ElementTree as _ET
_old_a_y=56.330709  # Frozen layout scalar; provenance in layout_parameters.json.
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
fig.savefig(H/'FigS3_support_maps_v03.svg',metadata={'Date':None})
fig.savefig(H/'FigS3_support_maps_v03.pdf',metadata={'CreationDate':None})
fig.savefig(H/'FigS3_support_maps_v03.png',dpi=600)
fig.savefig(H/'FigS3_support_maps_v03.tiff',dpi=600,pil_kwargs={'compression':'tiff_lzw'})
fig.savefig(H/'FigS3_support_maps_preview_v03.png',dpi=300)
plt.close(fig)
assert before=={str(p):sha(p) for p in tracked}
report=dict(status='COMPLETE_FIGS3_SUPPORT_MAPS_V02',source_sha256=before,sources_unchanged=True,
 points_each_overview=18862,strict_zero_pairs_marked_each_panel=5,zero_labels=[1,2,3,4,5],
 map_location='Frozen UA endpoint, one dot per matched pair',point_order='ascending pair_id',
 main_color_scale=[0,22],removed_color_scale=[0,20],color_scale_type='Discrete sequential integer-year bins',
 no_sampling=True,no_jitter=True,no_interpolation=True,inset_extent=[142.30,142.80,44.12,44.52],
 inset_points_each_panel=zoom_counts,inset_covers_no_overview_sample=True,
 labels_move_text_only_not_points=True,width_mm=183,height_mm=180,bitmap_dpi=600,text_outside_canvas=outside,
 SOS_dates_read=False,random_execution=False,new_model=False,manuscript_references_updated=False)
(H/'figure_verification_v03.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':report['status'],'outside_canvas':outside,'inset_counts':zoom_counts}))

_verification=H/('figure_verification_v03.json' if (H/'figure_verification_v03.json').exists() else 'verification_v03.json')
_v=json.loads(_verification.read_text(encoding='utf-8'))
_v.update(status=_v['status'].replace('_V02','_V03').replace('_V01','_V03'),height_mm=_new_h/72*25.4,header_title_to_panel_a_baseline_gap_pt=_baseline_gap_pt,
 header_title_baseline_from_top_pt=_top_baseline_pt,presentation_only_revision=True)
_verification.write_text(json.dumps(_v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
