"""Supplementary Fig. S1 from sealed annual summaries only."""
from pathlib import Path
import csv,json,hashlib,sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import StrMethodFormatter
import os, shutil
ROOT=Path(__file__).resolve().parents[2]
OUTPUT=Path(os.environ.get('PHENOLOGY_OUTPUT', str(ROOT/'reproduced'))).resolve()
H=OUTPUT/'figures'/'FigureS1'
H.mkdir(parents=True,exist_ok=True)
for _source in (ROOT/'data/figure_inputs'/'FigureS1').iterdir():
 if _source.is_file():shutil.copy2(_source,H/_source.name)
OBS=ROOT/'data/summary'
inputs=[OBS/n for n in ['annual_observed_summary.csv','figure_source_data_v01.json','independent_reconciliation_v01.json']]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
hashes={str(p):sha(p) for p in inputs}
d=json.loads(inputs[1].read_text(encoding='utf-8'))
assert json.loads(inputs[2].read_text(encoding='utf-8'))['status']=='INDEPENDENT_SQL_AND_RATIONAL_RECONCILIATION_PASS'
rows=list(csv.DictReader(inputs[0].open(encoding='utf-8-sig',newline='')))
assert len(rows)==len(d['annual'])==22
for row,r in zip(rows,d['annual']):
 assert set(row)==set(r)
 for k,v in row.items():assert abs(float(v)-float(r[k]))<1e-12
years=np.array([int(r['year']) for r in rows]);assert np.array_equal(years,np.arange(2003,2025))
val=lambda k:np.array([float(r[k]) for r in rows])
assert np.all(val('main_median')==-1) and np.all(val('complete22_median')==-1)
assert np.all(val('n_complete22')==14180)
assert int(val('n_main').sum())==403981 and int(val('n_strict').sum())==382773
assert val('n_main').min()==17739 and val('n_main').max()==18625
assert np.all(val('n_strict')<=val('n_main'))
for prefix in ['main','strict','complete22']:
 assert np.all(val(prefix+'_q25')<=val(prefix+'_median')) and np.all(val(prefix+'_median')<=val(prefix+'_q75'))
(H/'FigS1_annual_source_v01.csv').write_bytes(inputs[0].read_bytes())
BLUE='#4260CF';MAGENTA='#AD1A60';GRAY='#68727A'
plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['DejaVu Sans'],
 'font.size':8,'axes.titlesize':9,'axes.labelsize':8,'xtick.labelsize':7,'ytick.labelsize':7,
 'legend.fontsize':7,'svg.fonttype':'none','pdf.fonttype':42,'savefig.dpi':600,
 'axes.linewidth':.65,'svg.hashsalt':'phenology4-layout-v02-FigS1-v01','savefig.facecolor':'white'})
WIDTH_MM=183
fig=plt.figure(figsize=(WIDTH_MM/25.4,145/25.4))
ax=fig.add_axes([.12,.545,.835,.255])
ax.fill_between(years,val('main_q25'),val('main_q75'),color=BLUE,alpha=.17,linewidth=0)
for key in ['complete22_q25','complete22_q75']:ax.plot(years,val(key),color=GRAY,lw=1,ls='--')
ax.plot(years,val('main_median'),color=BLUE,lw=1.7,marker='o',ms=2.6)
ax.plot(years,val('complete22_median'),color=GRAY,lw=1.1,ls='--')
ax.axhline(0,color='#999999',ls=':',lw=.7,zorder=0)
ax.set(xlim=(2002.5,2024.5),ylim=(-8,7),ylabel='Annual UA − PA difference (days)',xticks=np.arange(2003,2025,3),yticks=[-5,0,5])
ax.tick_params(labelbottom=False)
ax.text(.025,.91,'Both annual medians = −1 day in every year',transform=ax.transAxes,fontsize=7.5,va='top')
fig.text(.12,.90,'a  Annual medians and interquartile ranges',fontweight='bold',fontsize=9)
for s in ['top','right']:ax.spines[s].set_visible(False)
ax.grid(axis='y',color='#E2E2E2',lw=.4)

ax=fig.add_axes([.12,.155,.835,.255])
ax.plot(years,val('n_main'),color=BLUE,lw=1.5,marker='o',ms=2.6,label='Main QA')
ax.plot(years,val('n_strict'),color=MAGENTA,lw=1.3,ls='--',marker='s',ms=2.4,label='Strict QA')
ax.plot(years,val('n_complete22'),color=GRAY,lw=1.2,ls=':',label='Fixed complete-record cohort')
ax.set(xlim=(2002.5,2024.5),ylim=(13200,19400),xticks=np.arange(2003,2025,3),yticks=[14000,16000,18000],
 xlabel='Product year',ylabel='Effective pairs with common support')
ax.yaxis.set_major_formatter(StrMethodFormatter('{x:,.0f}'))
fig.text(.12,.49,'b  Annual effective pair counts',fontweight='bold',fontsize=9)
for s in ['top','right']:ax.spines[s].set_visible(False)
ax.grid(axis='y',color='#E2E2E2',lw=.4)
for y,text,offset in [(2013,'17,739',-450),(2020,'18,625',300)]:
 v=val('n_main')[years==y][0]
 ax.annotate(text,xy=(y,v),xytext=(y,v+offset),ha='center',va='center',fontsize=7,color=BLUE)
ax.text(2003,14350,'14,180 complete-record pairs',fontsize=7,color=GRAY,va='bottom')
fig.legend(*ax.get_legend_handles_labels(),loc='upper center',bbox_to_anchor=(.54,.476),ncols=3,frameon=False,handlelength=2)
handles=[Patch(facecolor=BLUE,alpha=.17,label='Main: IQR'),Line2D([],[],color=GRAY,ls='--',lw=1,label='Complete: IQR limits'),
 Line2D([],[],color=BLUE,marker='o',ms=2.5,lw=1.7,label='Main: median'),Line2D([],[],color=GRAY,ls='--',lw=1.1,label='Complete: median')]
fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.54,.878),ncols=4,frameon=False,columnspacing=1,handlelength=1.5)
fig.text(.5,.98,'Annual spring onset contrasts and observation support',ha='center',fontweight='bold',fontsize=10)
fig.text(.5,.023,'Interquartile ranges describe observed variation. Lines connect annual summaries; no temporal trends were fitted.',ha='center',fontsize=7,color=GRAY)

# Remove empty header space while preserving physical panel sizes and data positions.
import xml.etree.ElementTree as _ET
_old_a_y=41.102362  # Frozen layout scalar; provenance in layout_parameters.json.
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
fig.savefig(H/'FigS1_annual_v03.svg',metadata={'Date':None})
fig.savefig(H/'FigS1_annual_v03.pdf',metadata={'CreationDate':None})
fig.savefig(H/'FigS1_annual_v03.png',dpi=600)
fig.savefig(H/'FigS1_annual_v03.tiff',dpi=600,pil_kwargs={'compression':'tiff_lzw'})
fig.savefig(H/'FigS1_annual_preview_v03.png',dpi=300)
plt.close(fig)
assert hashes=={str(p):sha(p) for p in inputs}
assert sha(H/'FigS1_annual_source_v01.csv')==sha(inputs[0])
report=dict(status='COMPLETE_FIGS1_ANNUAL_V02',source_sha256=hashes,sources_unchanged=True,
 annual_csv_and_aggregate_JSON_all_fields_match=True,source_copy_identical=True,years=years.tolist(),
 main_pair_years=int(val('n_main').sum()),strict_pair_years=int(val('n_strict').sum()),
 main_annual_count_range=[int(val('n_main').min()),int(val('n_main').max())],
 complete_pair_count_each_year=14180,main_and_complete_medians_each_year=-1,
 panel_a='Main IQR band plus fixed-complete IQR limits and both medians',panel_b='Main, strict and fixed-complete counts',
 count_axis_limits=[13200,19400],text_outside_canvas=outside,width_mm=183,height_mm=145,bitmap_dpi=600,
 date_level_reads=False,random_execution=False,trend_fitted=False,
 runtime=dict(python=sys.version.split()[0],numpy=np.__version__,matplotlib=matplotlib.__version__),manuscript_references_updated=False)
(H/'verification_v03.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':report['status'],'outside_canvas':outside}))

_verification=H/('figure_verification_v03.json' if (H/'figure_verification_v03.json').exists() else 'verification_v03.json')
_v=json.loads(_verification.read_text(encoding='utf-8'))
_v.update(status=_v['status'].replace('_V02','_V03').replace('_V01','_V03'),height_mm=_new_h/72*25.4,header_title_to_panel_a_baseline_gap_pt=_baseline_gap_pt,
 header_title_baseline_from_top_pt=_top_baseline_pt,presentation_only_revision=True)
_verification.write_text(json.dumps(_v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
