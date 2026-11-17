// Paste into Earth Engine Code Editor. Run the PILOT export before FULL.
var MODE = 'PILOT'; // 'PILOT' or 'FULL'
var FULL_PARTS = [0, 1, 2, 3, 4, 5, 6, 7];
var VERSION = 'E1_UA_pixel_overlap_v01';
var UA_ASSET = 'projects/ee-liangxianfan0/assets/pheno/UA_2000_north_buf_1000m';
var POINT_ASSET = 'projects/ee-liangxianfan0/assets/pheno/E1_boundary_frozen_UA_v04';
var SHA = 'a0bdb8e20b57eac13b3efd21cfa6cefbc9905c92381da0c3ea975f5d8a862469';
var N = 18862;
var UA_FEATURES = 34967;
var CRS = 'SR-ORG:6974';
var GRID = ee.Projection(CRS);
// Frozen MCD12Q1 native membership grid, in CRS metres. The affine is
// applied explicitly below, so GRID itself has no pixel-scale transform.
var DX = 463.3127165279165;
var DY = -463.3127165279167;
var X0 = -20015109.354;
var Y0 = 10007554.677003;
var ERROR_M = 0.1;
var ERROR = ee.ErrorMargin(ERROR_M, 'meters');
var PILOT_IDS = [
  'R1-VF05_pair_00000947', 'R1-VF05_pair_00000001', 'R1-VF05_pair_00000002',
  'R1-VF05_pair_00005618', 'R1-VF05_pair_00011172', 'R1-VF05_pair_00009775',
  'R1-VF05_pair_00005804', 'R1-VF05_pair_00006451'
];
var BREAKS = [1, 2359, 4717, 7075, 9433, 11791, 14149, 16507, 18863];
var raw = ee.FeatureCollection(POINT_ASSET);
var ua = ee.FeatureCollection(UA_ASSET);
var points = raw
  .filter(ee.Filter.notNull(['pair_id', 'support_unit_id', 'frozen_ua_lon', 'frozen_ua_lat']))
  .filter(ee.Filter.eq('source_pairs_sha256', SHA))
  .filter(ee.Filter.eq('coordinate_schema', 'E1_frozen_UA_coordinates_v04'))
  .filter(ee.Filter.gte('frozen_ua_lon', -180))
  .filter(ee.Filter.lte('frozen_ua_lon', 180))
  .filter(ee.Filter.gte('frozen_ua_lat', 23.44))
  .filter(ee.Filter.lt('frozen_ua_lat', 66.56))
  .map(function (f) {
    var id = ee.String(f.get('pair_id')).match('^R1-VF05_pair_[0-9]{8}$');
    var grid = ee.String(f.get('support_unit_id')).match('^UA_T[12]_x[0-9]+_y[0-9]+$');
    return f.set('id_ok', id.size().eq(1).and(grid.size().eq(1)));
  }).filter(ee.Filter.eq('id_ok', 1))
  .map(function (f) {
    return f.set('serial', ee.Number.parse(ee.String(f.get('pair_id')).slice(-8)));
  });

function measure(f) {
  var xy = ee.String(f.get('support_unit_id')).split('_x');
  var ij = ee.String(xy.get(1)).split('_y');
  var col = ee.Number.parse(ij.get(0));
  var row = ee.Number.parse(ij.get(1));
  var x = col.multiply(DX).add(X0);
  var y = row.multiply(DY).add(Y0);
  var cell = ee.Geometry.Rectangle([x, y.add(DY), x.add(DX), y], GRID, false);
  var lon = ee.Number(f.get('frozen_ua_lon'));
  var lat = ee.Number(f.get('frozen_ua_lat'));
  var point = ee.Geometry.Point([lon, lat]);
  var centre = ee.Geometry.Point([x.add(DX / 2), y.add(DY / 2)], GRID);
  var candidates = ua.filterBounds(cell);
  // Clip each feature first, then union its clipped parts before measuring.
  var clips = candidates.map(function (candidate) {
    var clipped = candidate.geometry().intersection(cell, ERROR, GRID);
    return ee.Feature(clipped.transform(GRID, ERROR));
  });
  var overlap = ee.Number(ee.Algorithms.If(candidates.size().gt(0),
    clips.geometry(ERROR).dissolve(ERROR, GRID).area(ERROR, GRID), 0));
  var cellArea = cell.area(ERROR, GRID);
  return ee.Feature(null, {
    pair_id: f.get('pair_id'), support_unit_id: f.get('support_unit_id'),
    native_col: col, native_row: row, longitude: lon, latitude: lat,
    center_offset_m: point.distance(centre, ERROR, GRID),
    point_inside_buffered: ua.filterBounds(point).limit(1).size().gt(0),
    candidate_features: candidates.size(), cell_area_m2: cellArea,
    intersection_area_m2: overlap, f_ua: overlap.divide(cellArea),
    ua_asset: UA_ASSET, coordinate_asset: POINT_ASSET, source_pairs_sha256: SHA,
    native_crs: CRS, tolerance_m: ERROR_M, version: VERSION
  });
}

function createTask(pointsForTask, suffix, expected) {
  var task = VERSION + '_' + suffix;
  Export.table.toDrive({
    collection: pointsForTask.map(measure).map(function (f) {
      return f.set('part', suffix);
    }),
    description: task, folder: VERSION, fileNamePrefix: task, fileFormat: 'CSV',
    selectors: ['pair_id', 'support_unit_id', 'part', 'native_col', 'native_row',
      'longitude', 'latitude', 'center_offset_m', 'point_inside_buffered',
      'candidate_features', 'cell_area_m2', 'intersection_area_m2', 'f_ua',
      'ua_asset', 'coordinate_asset', 'source_pairs_sha256',
      'native_crs', 'tolerance_m', 'version']
  });
  print('Task ready', task, 'expected rows', expected);
}

if (MODE !== 'PILOT' && MODE !== 'FULL') throw Error('Unknown MODE');
var pilot = points.filter(ee.Filter.inList('pair_id', PILOT_IDS));
var batches = FULL_PARTS.map(function (i) {
  if (i !== Math.floor(i) || i < 0 || i > 7) throw Error('Invalid part index');
  return points.filter(ee.Filter.gte('serial', BREAKS[i]))
    .filter(ee.Filter.lt('serial', BREAKS[i + 1]));
});
ee.Dictionary({
  rows: raw.size(), usable: points.size(),
  unique_ids: points.aggregate_count_distinct('pair_id'),
  unique_cells_with_tier: points.aggregate_count_distinct('support_unit_id'),
  pilot: pilot.size(), ua_features: ua.size(),
  batches: ee.List(batches.map(function (b) { return b.size(); }))
}).evaluate(function (info, error) {
  if (error || !info || info.rows !== N || info.usable !== N ||
      info.unique_ids !== N || info.unique_cells_with_tier !== N ||
      info.pilot !== PILOT_IDS.length || info.ua_features !== UA_FEATURES ||
      !info.batches.every(function (n, k) {
        var i = FULL_PARTS[k];
        return n === BREAKS[i + 1] - BREAKS[i];
      })) {
    print('STOP_INPUT_CHECK', error || info);
    return;
  }
  print('INPUT_PASS', info);
  if (MODE === 'PILOT') {
    createTask(pilot, 'PILOT', PILOT_IDS.length);
  } else {
    FULL_PARTS.forEach(function (i, k) {
      createTask(batches[k], 'B0' + i, BREAKS[i + 1] - BREAKS[i]);
    });
  }
});
