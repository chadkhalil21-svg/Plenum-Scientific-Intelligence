"""USGS adapter tests: synthetic fixtures never imply real river observations."""
import copy
import json
import math
import unittest
from datetime import date, timedelta
from urllib.parse import parse_qs, urlsplit
from plenum_ai import usgs_hydrology as h


def synthetic_series():
    days={}
    for i in range(47):
        day=h.FIRST+timedelta(days=i)
        days[day]=1000+80*math.sin(i/5)+2*i
    return days


def payload(site,include_holdout=False):
    values=synthetic_series()
    end=h.HOLDOUT_LAST if include_holdout else h.DEVELOPMENT_LAST
    return {"type":"FeatureCollection","features":[{
        "type":"Feature","properties":{
            "monitoring_location_id":"USGS-"+site,"parameter_code":"00060",
            "statistic_id":"00003","unit_of_measure":"ft^3/s",
            "time":day.isoformat(),"value":str(value),
            "approval_status":"Provisional",
        }} for day,value in sorted(values.items()) if day<=end],
        "links":[]}


class FakeHttp:
    def __init__(self,p):
        self.content=json.dumps(p).encode()
    def read(self,n):
        return self.content[:n]
    def __enter__(self): return self
    def __exit__(self,*args): return False


def fake_opener(request,timeout=None):
    query=parse_qs(urlsplit(request.full_url).query)
    site=query["monitoring_location_id"][0][5:]
    assert "time" not in query, "USGS OGC time property is not the datetime range filter"
    reveal=query["datetime"][0].endswith(h.HOLDOUT_LAST.isoformat())
    return FakeHttp(payload(site,reveal))


class USGSDomainTests(unittest.TestCase):
    def test_modern_public_api_and_no_hidden_dates(self):
        for site in h.SITES:
            url=h.query_url(site,False)
            self.assertIn("/ogcapi/v1/collections/daily/items?",url)
            self.assertIn("datetime=2026-10-01%2F2026-11-04",url)
            self.assertNotIn("&time=",url)
            self.assertNotIn("2026-11-13",url)
            self.assertIn("statistic_id=00003",url)
            self.assertIn("parameter_code=00060",url)
            self.assertIn("monitoring_location_id=USGS-",url)

    def test_strict_source_validation_and_metadata(self):
        obs,source=h.fetch_daily("01646500",opener=fake_opener)
        self.assertEqual(len(obs),35)
        self.assertEqual(max(obs),h.DEVELOPMENT_LAST)
        self.assertEqual(source["unit"],"ft^3/s")
        self.assertIn("Provisional",source["statuses"])
        self.assertTrue(h.development_digest(obs))
        future,_=h.fetch_daily("01646500",True,opener=fake_opener)
        self.assertEqual(max(future),h.HOLDOUT_LAST)

    def test_reject_duplicate_or_wrong_units(self):
        site="01491000"
        x=payload(site)
        x["features"].append(copy.deepcopy(x["features"][0]))
        with self.assertRaisesRegex(ValueError,"duplicate"):
            h.parse_daily(x,site)
        x=payload(site)
        x["features"][0]["properties"]["unit_of_measure"]="m^3/s"
        with self.assertRaisesRegex(ValueError,"units"):
            h.parse_daily(x,site)

    def test_reject_unbounded_or_paged_source(self):
        p=payload("01646500")
        p["links"]=[{"rel":"next","href":"untrusted"}]
        with self.assertRaisesRegex(ValueError,"paginated"):
            h.parse_daily(p,"01646500")
        with self.assertRaises(ValueError):
            h.query_url("00000000")
        p=payload("01646500")
        p["features"][0]["properties"]["value"]="-100"
        with self.assertRaises(ValueError):
            h.parse_daily(p,"01646500")

    def test_all_hydrology_baselines_on_both_folds(self):
        obs=synthetic_series()
        baselines=h.baseline_scores(obs)
        self.assertEqual(set(baselines),set(h.BASELINES))
        for errors in baselines.values():
            self.assertEqual(len(errors),2)
            self.assertTrue(all(x>=0 and math.isfinite(x) for x in errors))
        self.assertEqual(len(h.fold_scores(obs,{"alpha":0.65,"beta":0.0})),2)

    def test_forecasts_only_use_training_observations(self):
        obs=synthetic_series()
        fit_end=h.DEVELOPMENT_LAST
        restricted={d:v for d,v in obs.items() if d<=fit_end}
        day=date(2026,11,12)
        for kind in h.BASELINES+({"alpha":0.3,"beta":0.01},):
            predicted=h.predict(restricted,fit_end,day,kind)
            self.assertTrue(math.isfinite(predicted))
            self.assertGreater(predicted,0)

    def test_development_rule_avoids_one_fold_overfitting(self):
        b={name:[.10,.11] for name in h.BASELINES}
        model={"alpha":.5,"beta":0.0}
        selected=h.select(model,None,b,[.05,.15],[None,None])
        self.assertEqual(selected["source"],"baseline")
        selected=h.select(model,None,b,[.05,.07],[None,None])
        self.assertEqual(selected["source"],"qwen")
        candidate={"alpha":.6,"beta":-.01}
        selected=h.select(model,candidate,b,[.05,.07],[.04,.06])
        self.assertEqual(selected["source"],"critic")

    def test_missing_approved_series_fails_instead_of_fabricating(self):
        obs=synthetic_series()
        del obs[h.FIRST+timedelta(days=23)]
        with self.assertRaises(ValueError):
            h.baseline_scores(obs)
        with self.assertRaises(ValueError):
            h.predict(obs,h.DEVELOPMENT_LAST,date(2026,11,12),{"alpha":-.5,"beta":0.0})


if __name__=="__main__":
    unittest.main()
