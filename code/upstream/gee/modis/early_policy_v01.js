// Fixed MODIS early two-cycle support policy; date selection never consults QA.
function e1ChooseEarly(rows) {
  var a=rows[0], b=rows[1];
  var s1=ee.Number(a.structure), s2=ee.Number(b.structure);
  function invalid(s) { return s.neq(-1).and(s.neq(0)).and(s.neq(1)); }
  var c1=s1.eq(1), c2=s2.eq(1), count=c1.add(c2);
  var n1=ee.Number(a.num), n2=ee.Number(b.num);
  var bad=ee.Number(a.technical).neq(1).or(ee.Number(b.technical).neq(1))
    .or(ee.Number(a.bad).eq(1)).or(ee.Number(b.bad).eq(1))
    .or(ee.Number(a.numValid).neq(1)).or(ee.Number(b.numValid).neq(1))
    .or(n1.neq(n2)).or(n1.gt(2)).or(n2.gt(2))
    .or(n1.eq(0).and(n2.eq(0)).and(count.gt(0)))
    .or(n1.eq(1).and(n2.eq(1)).and(c2))
    .or(invalid(s1)).or(invalid(s2)).or(s1.eq(-1)).or(s2.eq(-1)).or(count.gt(1));
  var selected=ee.Number(ee.Algorithms.If(bad,0,ee.Algorithms.If(count.eq(1),ee.Algorithms.If(c1,1,2),0)));
  var status=ee.Number(ee.Algorithms.If(bad,-1,ee.Algorithms.If(count.eq(1),1,0)));
  var main=ee.Number(ee.Algorithms.If(selected.eq(1),a.main,ee.Algorithms.If(selected.eq(2),b.main,0)));
  var strict=ee.Number(ee.Algorithms.If(selected.eq(1),a.strict,ee.Algorithms.If(selected.eq(2),b.strict,0)));
  return {status:status,selected:selected,main:main,strict:strict};
}
if (typeof module !== 'undefined' && module.exports) module.exports = {e1ChooseEarly:e1ChooseEarly};
