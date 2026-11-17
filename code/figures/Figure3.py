"""Figure 3: sealed completeness and QA summaries, no new outcome analysis."""
from pathlib import Path
import csv,json,hashlib,sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import os, shutil
ROOT=Path(__file__).resolve().parents[2]
OUTPUT=Path(os.environ.get('PHENOLOGY_OUTPUT', str(ROOT/'reproduced'))).resolve()
H=OUTPUT/'figures'/'Figure3'
H.mkdir(parents=True,exist_ok=True)
for _source in (ROOT/'data/figure_inputs'/'Figure3').iterdir():
 if _source.is_file():shutil.copy2(_source,H/_source.name)
OBS=ROOT/'data/summary'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
inputs=[OBS/n for n in ['figure_source_data_v01.json','Table1_descriptive_support.csv',
 'Table2_sensitivity_contrasts.csv','independent_reconciliation_v01.json']]
hashes={str(p):sha(p) for p in inputs}
d=json.loads(inputs[0].read_text(encoding='utf-8'))
g={r['group']:r for r in d['groups']};c={r['contrast']:r for r in d['contrasts']}
assert json.loads(inputs[3].read_text(encoding='utf-8'))['status']=='INDEPENDENT_SQL_AND_RATIONAL_RECONCILIATION_PASS'
for path,reference,key in [(inputs[1],g,'group'),(inputs[2],c,'contrast')]:
 for row in csv.DictReader(path.open(encoding='utf-8-sig',newline='')):
  for k,v in row.items():
   if k!=key:assert abs(float(v)-float(reference[row[key]][k]))<1e-12
assert g['main_all']['pairs']==18862 and g['main_complete22']['pairs']==14180 and g['main_incomplete']['pairs']==4682
assert g['main_all']['pair_years']==403981
assert g['strict_native']['pairs']==g['main_on_strict_roster']['pairs']==18857
assert g['strict_native']['zero_support_pairs']==5
assert g['main_on_strict_roster']['pair_years']==403946 and g['strict_native']['pair_years']==382773
assert c['strict_vs_main']['paired_roster']==18857
assert all(c['strict_vs_main']['paired_change_'+k]==0 for k in ['median','q25','q75'])
source=[]
configs=[('a', ['main_all','main_complete22','main_incomplete']),('b',['main_on_strict_roster','strict_native'])]
for panel,keys in configs:
 for key in keys:
  r=g[key];source.append({'panel':panel,'condition':key,'pairs':r['pairs'],'pair_years':r['pair_years'],
   **{k:r[k] for k in ['mean','q05','q25','median','q75','q95']}})
r=c['strict_vs_main'];source.append({'panel':'c','condition':'strict_minus_main','pairs':18857,'pair_years':'',
 'mean':r['same_pair_mean_change'],**{k:r['paired_change_'+k] for k in ['q05','q25','median','q75','q95']}})
with (H/'Figure3_source_summaries_v01.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(source[0]));w.writeheader();w.writerows(source)
BLUE='#4260CF';MAGENTA='#AD1A60';GRAY='#68727A'
plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['DejaVu Sans'],
 'font.size':8,'axes.titlesize':9,'axes.labelsize':8,'xtick.labelsize':7,'ytick.labelsize':7.5,
 'legend.fontsize':7,'svg.fonttype':'none','pdf.fonttype':42,'savefig.dpi':600,
 'axes.linewidth':.65,'svg.hashsalt':'phenology4-Fig3-v01','savefig.facecolor':'white'})
WIDTH_MM=183
fig=plt.figure(figsize=(WIDTH_MM/25.4,150/25.4))
fmt=lambda x:f'{x:.2f}'.replace('-','−')
def panel(ax,letter,title,items,labels,colors,limits,xlabel):
 for y,(row,color) in enumerate(zip(items,colors)):
  lo,q1,median,q3,hi=[row[k] for k in ['q05','q25','median','q75','q95']]
  ax.plot([lo,hi],[y,y],color=color,lw=1.3)
  ax.plot([lo,hi],[y,y],color=color,marker='|',ms=5,ls='')
  ax.plot([q1,q3],[y,y],color=color,lw=5,solid_capstyle='butt')
  ax.plot(median,y,marker='|',color='black',ms=9,mew=1.1,ls='')
  ax.plot(row['mean'],y-.16,marker='D',mfc='white',mec=color,ms=4,ls='',zorder=4)
  for x in [lo,hi]:ax.text(x,y+.24,fmt(x),ha='center',va='top',fontsize=7,color=color)
  ax.text(1.04,y,fmt(row['mean']),transform=ax.get_yaxis_transform(),ha='left',va='center',fontsize=8)
 ax.text(1.04,1.08,'Mean\n(days)',transform=ax.transAxes,ha='left',va='bottom',fontsize=7)
 ax.axvline(0,color='#999999',ls='--',lw=.7,zorder=0)
 ax.set(xlim=limits,ylim=(len(items)-.35,-.55),yticks=range(len(items)),yticklabels=labels,xlabel=xlabel)
 for name in ['top','right','left']:ax.spines[name].set_visible(False)
 ax.tick_params(axis='y',length=0,pad=9)
 ax.set_title(f'{letter}  {title}',loc='left',fontweight='bold',pad=13)

ax=fig.add_axes([.31,.665,.54,.205])
panel(ax,'a','Record completeness',source[:3],
 ['All pairs  (18,862)','Complete 22 years  (14,180)','Incomplete records  (4,682)'],
 [GRAY,BLUE,MAGENTA],(-18,16),'Pairwise mean UA − PA (days)')
ax=fig.add_axes([.31,.385,.54,.145])
panel(ax,'b','Quality filtering within the same pairs',source[3:5],
 ['Main QA  (18,857)','Strict QA  (18,857)'],[BLUE,MAGENTA],(-18,16),'Pairwise mean UA − PA (days)')
ax=fig.add_axes([.31,.14,.54,.09])
panel(ax,'c','Within-pair changes under strict screening',source[5:],
 ['Shared pairs  (18,857)'],[GRAY],(-1.5,1.5),'Within-pair change, strict − main (days)')
fig.text(.5,.98,'Mean contrasts change little under record and quality restrictions',ha='center',fontweight='bold',fontsize=10)
handles=[Line2D([],[],color=GRAY,lw=1.3,label='5th–95th percentiles'),Line2D([],[],color=GRAY,lw=5,label='25th–75th percentiles'),
 Line2D([],[],marker='|',color='black',ls='',ms=8,label='Median'),Line2D([],[],marker='D',mec='black',mfc='white',ls='',ms=3.5,label='Mean')]
fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.53,.958),ncols=4,frameon=False,handlelength=1.3,columnspacing=1.1)
fig.text(.5,.064,'Strict QA: 382,773 pair-years; 5 original pairs have zero support.',ha='center',fontsize=7)
fig.text(.5,.033,'Panel c: median and both quartiles = 0.00 days. Ranges are descriptive percentiles, not confidence intervals.',ha='center',fontsize=7,color=GRAY)

# Remove empty header space while preserving physical panel sizes and data positions.
import xml.etree.ElementTree as _ET
_old_a_y=42.275591  # Frozen layout scalar; provenance in layout_parameters.json.
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
if True:
 # Retain this figure's descriptive-symbol legend in the reduced header gap.
 for _leg in fig.legends:
  _leg.set_loc('center')
  _leg.set_bbox_to_anchor((.53,1-20.8/_new_h),transform=fig.transFigure)

fig.canvas.draw();renderer=fig.canvas.get_renderer();outside=[]
for t in fig.findobj(matplotlib.text.Text):
 if t.get_visible() and t.get_text():
  b=t.get_window_extent(renderer)
  if b.width and b.height and (b.x0<0 or b.y0<0 or b.x1>fig.bbox.x1 or b.y1>fig.bbox.y1):outside.append(t.get_text())
fig.savefig(H/'Figure3_sensitivities_v03.svg',metadata={'Date':None})
fig.savefig(H/'Figure3_sensitivities_v03.pdf',metadata={'CreationDate':None})
fig.savefig(H/'Figure3_sensitivities_v03.png',dpi=600)
fig.savefig(H/'Figure3_sensitivities_v03.tiff',dpi=600,pil_kwargs={'compression':'tiff_lzw'})
fig.savefig(H/'Figure3_sensitivities_preview_v03.png',dpi=300)
plt.close(fig)
assert hashes=={str(p):sha(p) for p in inputs}
reopened=list(csv.DictReader((H/'Figure3_source_summaries_v01.csv').open(encoding='utf-8-sig',newline='')))
assert len(reopened)==6
for original,row in zip(source,reopened):
 for k,v in original.items():
  if isinstance(v,(int,float)):assert abs(float(row[k])-v)<1e-12
  else:assert str(row[k])==str(v)
verification=dict(status='COMPLETE_FIGURE3_SENSITIVITIES_V01',source_sha256=hashes,sources_unchanged=True,
 all_table1_table2_fields_match_aggregate_json=True,source_summary_roundtrip=True,
 source_rows=source,text_outside_canvas=outside,width_mm=183,height_mm=150,bitmap_dpi=600,
 panel_a_b_limits=[-18,16],panel_c_limits=[-1.5,1.5],
 zero_length_IQR_in_panel_c=True,intervals='Empirical distribution percentiles; no uncertainty intervals',
 date_level_reads=False,random_execution=False,new_models=False,
 runtime=dict(python=sys.version.split()[0],numpy=np.__version__,matplotlib=matplotlib.__version__),
 manuscript_references_updated=False)
(H/'verification_v03.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':verification['status'],'outside_canvas':outside},ensure_ascii=False))

_verification=H/('figure_verification_v03.json' if (H/'figure_verification_v03.json').exists() else 'verification_v03.json')
_v=json.loads(_verification.read_text(encoding='utf-8'))
_v.update(status=_v['status'].replace('_V02','_V03').replace('_V01','_V03'),height_mm=_new_h/72*25.4,header_title_to_panel_a_baseline_gap_pt=_baseline_gap_pt,
 header_title_baseline_from_top_pt=_top_baseline_pt,presentation_only_revision=True)
_verification.write_text(json.dumps(_v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
