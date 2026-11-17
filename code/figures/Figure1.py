"""Figure 1: frozen matched sites over audited display domains; Python only."""
from pathlib import Path
import csv,hashlib,json,os,sys
os.environ['PROJ_NETWORK']='OFF'
import geopandas as gpd
import numpy as np
import rasterio
from rasterio.windows import from_bounds
from rasterio.transform import array_bounds
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Patch,Rectangle
from matplotlib.ticker import FuncFormatter

import os, shutil
ROOT=Path(__file__).resolve().parents[2]
OUTPUT=Path(os.environ.get('PHENOLOGY_OUTPUT', str(ROOT/'reproduced'))).resolve()
H=OUTPUT/'figures'/'Figure1'
H.mkdir(parents=True,exist_ok=True)
for _source in (ROOT/'data/figure_inputs'/'Figure1').iterdir():
 if _source.is_file():shutil.copy2(_source,H/_source.name)
A=Path(os.environ.get('PHENOLOGY_DOMAIN_INPUTS', str(ROOT/'assets/domain'))).resolve()
PAIRS=ROOT/'data/frozen_pairs.csv'
FREEZE=A/'frozen_design_record.json'
MOSAIC=A/'E1_study_domain_display_mosaic_v01.tif'
AGG=A/'domain_quicklook_aggregate_v01.npz'
WORLD=ROOT/'assets/basemap/naturalearth_lowres.shp'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
sources=[PAIRS,FREEZE,MOSAIC,AGG,A/'verification_v01.json']+[WORLD.with_suffix(s) for s in ('.shp','.shx','.dbf','.prj')]
before={str(p):sha(p) for p in sources}
assert sha(PAIRS)==json.loads(FREEZE.read_text(encoding='utf-8'))['final_primary_pairs']['sha256']
audit=json.loads((A/'verification_v01.json').read_text(encoding='utf-8'))
assert audit['status']=='PASS_DISPLAY_MASK_RETURN_AND_LOSSLESS_MOSAIC'
assert sha(MOSAIC)==audit['output']['sha256']
rows=list(csv.DictReader(PAIRS.open(encoding='utf-8-sig',newline='')))
assert len(rows)==len({r['pair_id'] for r in rows})==18862
assert len({r['city_id'] for r in rows})==7422 and len({r['pa_id'] for r in rows})==9597
for role in ['ua','pa']:
 assert len({r[role+'_support_unit_id'] for r in rows})==18862
fields=['pair_id','ua_support_unit_id','pa_support_unit_id','city_id','pa_id',
        'ua_longitude','ua_latitude','pa_longitude','pa_latitude']
with (H/'Figure1_source_sites_v01.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows({k:r[k] for k in fields} for r in rows)
coords={role:np.array([[float(r[role+'_longitude']),float(r[role+'_latitude'])] for r in rows]) for role in ['ua','pa']}
assert all(np.isfinite(x).all() for x in coords.values())
assert all(((x[:,1]>=23.44)&(x[:,1]<66.56)&(x[:,0]>=-180)&(x[:,0]<=180)).all() for x in coords.values())
world=gpd.read_file(WORLD,engine='pyogrio')
assert world.crs.to_epsg()==4326 and world.geometry.is_valid.all()
assert not world.geometry.isna().any() and not world.geometry.is_empty.any()

UA='#C65A8D';PA='#4260CF';NEUTRAL='#686868'
plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['DejaVu Sans'],
 'font.size':8,'axes.titlesize':9,'axes.labelsize':8,'xtick.labelsize':7,'ytick.labelsize':7,
 'legend.fontsize':7,'svg.fonttype':'none','pdf.fonttype':42,'savefig.dpi':600,
 'axes.linewidth':.65,'svg.hashsalt':'phenology4-layout-v02-study-area-v01','savefig.facecolor':'white'})
WIDTH_MM=183
fig=plt.figure(figsize=(WIDTH_MM/25.4,150/25.4))
axes=[fig.add_axes(p) for p in [[.075,.555,.90,.285],[.075,.155,.405,.27],[.57,.155,.405,.27]]]
windows=[(-180,180,18,74),(-100,-65,27,52),(-12,40,36,63)]
titles=['a  Study domain and matched sites','b  North America','c  Europe']
lonfmt=FuncFormatter(lambda x,p:'0°' if x==0 else f'{abs(x):g}°'+('E' if x>0 else 'W'))
latfmt=FuncFormatter(lambda y,p:f'{y:g}°N')
agg=np.load(AGG)
counts=[]
mask_rendering=[]
with rasterio.open(MOSAIC) as src:
 assert src.crs.to_epsg()==4326 and src.count==2 and src.descriptions==('UA_domain','PA_domain')
 for panel,(ax,bounds,title) in enumerate(zip(axes,windows,titles)):
  left,right,bottom,top=bounds
  world.plot(ax=ax,color='#F3F3F3',edgecolor='#BFBFBF',linewidth=.25,zorder=0)
  if panel==0:
   masks=agg['masks'];extent=agg['extent'].tolist()
  else:
   win=from_bounds(left,bottom,right,top,src.transform).round_offsets().round_lengths()
   masks=src.read(window=win)
   south_west_north_east=array_bounds(masks.shape[1],masks.shape[2],src.window_transform(win))
   west,south,east,north=south_west_north_east
   extent=[west,east,south,north]
  mask_rendering.append({'panel':panel,'extent':extent,'array_shape':list(masks.shape),
    'aggregation':'aligned 10x10 maximum presence' if panel==0 else 'native 0.01-degree grid'})
  for band,color,alpha in [(1,PA,.22),(0,UA,.25)]:
   ax.imshow(np.ma.masked_where(masks[band]==0,masks[band]),extent=extent,origin='upper',
      cmap=ListedColormap([color]),vmin=0,vmax=1,alpha=alpha,interpolation='nearest',zorder=1)
  per_panel={}
  # PA triangles have an open centre so nearby UA circles remain distinguishable.
  for role,color,marker in [('pa',PA,'^'),('ua',UA,'o')]:
   xy=coords[role]
   keep=(xy[:,0]>=left)&(xy[:,0]<=right)&(xy[:,1]>=bottom)&(xy[:,1]<=top)
   per_panel[role]=int(keep.sum())
   if role=='pa':
    ax.scatter(xy[keep,0],xy[keep,1],s=1.5 if panel==0 else 3.3,marker=marker,
      facecolors='none',edgecolors=color,linewidths=.27 if panel==0 else .35,
      rasterized=True,zorder=4)
   else:
    ax.scatter(xy[keep,0],xy[keep,1],s=.7 if panel==0 else 1.5,marker=marker,
      color=color,edgecolors='none',rasterized=True,zorder=5)
  counts.append(per_panel)
  ax.set(xlim=(left,right),ylim=(bottom,top),aspect='auto')
  if panel==0:ax.set(xticks=np.arange(-150,180,50),yticks=[30,45,60])
  elif panel==1:ax.set(xticks=[-100,-90,-80,-70],yticks=[30,40,50])
  else:ax.set(xticks=[0,10,20,30,40],yticks=[40,50,60])
  ax.xaxis.set_major_formatter(lonfmt);ax.yaxis.set_major_formatter(latfmt)
  ax.grid(color='#DCDCDC',lw=.35,zorder=0)
  ax.set_title(title,loc='left',pad=8,fontweight='bold')
  if panel==0:
   for latitude in [23.44,66.56]:
    ax.axhline(latitude,color='#777777',ls='--',lw=.65,zorder=3)
    ax.text(.985,latitude+.45,f'{latitude:.2f}°N',transform=ax.get_yaxis_transform(),ha='right',va='bottom',fontsize=7,color='#555555',zorder=8,bbox={'facecolor':'white','edgecolor':'none','alpha':.9,'pad':1})
   ax.text(.015,.86,'18,862 matched pairs',transform=ax.transAxes,fontsize=7,
      bbox={'facecolor':'white','edgecolor':'none','alpha':.85,'pad':2})
assert counts[0]=={'ua':18862,'pa':18862}
for box,letter in zip(windows[1:],['b','c']):
 l,r,b,t=box
 axes[0].add_patch(Rectangle((l,b),r-l,t-b,fill=False,edgecolor='#343434',lw=.8,zorder=6))
 axes[0].text(l+1,t+1,letter,fontweight='bold',fontsize=8,zorder=7,
   bbox={'facecolor':'white','edgecolor':'none','alpha':.85,'pad':1})

fig.text(.5,.975,'Matched vegetation sites in the UA and PA sampling domains',ha='center',fontweight='bold',fontsize=10)
handles=[Patch(facecolor=UA,alpha=.25,label='UA domain'),Patch(facecolor=PA,alpha=.22,label='PA domain'),
 Line2D([],[],marker='o',color=UA,ls='',ms=3,label='Sampled UA site'),
 Line2D([],[],marker='^',mec=PA,mfc='none',ls='',ms=3.7,label='Sampled PA site')]
fig.legend(handles=handles,loc='center',bbox_to_anchor=(.53,.493),ncols=4,frameon=False,columnspacing=1.5,handlelength=1.3)
fig.text(.5,.080,'18,862 pairs  ·  7,422 UA identifiers  ·  9,597 PA identifiers',ha='center',fontsize=8)
fig.text(.5,.043,'Pale fills: regional domains; symbols: sampled vegetation. Dashed limits: 23.44°N–66.56°N.',ha='center',fontsize=7)


# Remove empty header space while preserving physical panel sizes and data positions.
import xml.etree.ElementTree as _ET
_old_a_y=60.031496  # Frozen layout scalar; provenance in layout_parameters.json.
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
fig.savefig(H/'Figure1_study_area_v03.svg',metadata={'Date':None})
fig.savefig(H/'Figure1_study_area_v03.pdf',metadata={'CreationDate':None})
fig.savefig(H/'Figure1_study_area_v03.png',dpi=600)
fig.savefig(H/'Figure1_study_area_v03.tiff',dpi=600,pil_kwargs={'compression':'tiff_lzw'})
fig.savefig(H/'Figure1_study_area_preview_v03.png',dpi=300)
plt.close(fig)
assert before=={str(p):sha(p) for p in sources}
out_rows=list(csv.DictReader((H/'Figure1_source_sites_v01.csv').open(encoding='utf-8-sig',newline='')))
assert len(out_rows)==18862
assert all({k:r[k] for k in fields}==o for r,o in zip(rows,out_rows))
report=dict(status='COMPLETE_STUDY_AREA_FIGURE_V02',source_sha256=before,sources_unchanged=True,
 frozen_pair_hash_pass=True,site_source_roundtrip_pass=True,pair_count=18862,
 UA_sites=18862,PA_sites=18862,UA_identifiers=7422,PA_identifiers=9597,
 viewports=windows,plotted_site_counts=counts,mask_rendering=mask_rendering,
 overview_includes_all_sites=True,no_point_sampling_or_jitter=True,
 world_CRS=str(world.crs),world_features=len(world),world_geometries_valid=True,
 coordinate_transform=False,spatial_join=False,geometry_repair=False,
 text_outside_canvas=outside,width_mm=183,height_mm=150,bitmap_dpi=600,
 runtime=dict(python=sys.version.split()[0],geopandas=gpd.__version__,matplotlib=matplotlib.__version__,rasterio=rasterio.__version__),
 outcome_data_read=False,random_execution=False,
 limitation='Display masks do not certify precise boundaries, areas, or historical geometry identity; dense site symbols overlap.',
 manuscript_references_updated=False)
(H/'verification_v03.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':report['status'],'panel_counts':counts,'outside_canvas':outside},ensure_ascii=False))

_verification=H/('figure_verification_v03.json' if (H/'figure_verification_v03.json').exists() else 'verification_v03.json')
_v=json.loads(_verification.read_text(encoding='utf-8'))
_v.update(status=_v['status'].replace('_V02','_V03').replace('_V01','_V03'),height_mm=_new_h/72*25.4,header_title_to_panel_a_baseline_gap_pt=_baseline_gap_pt,
 header_title_baseline_from_top_pt=_top_baseline_pt,presentation_only_revision=True)
_verification.write_text(json.dumps(_v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
