import json
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch
from plenum_ai import chief_team_mission as m


def event(actor='chadkhalil21-svg', objective='Check NOAA locations 8724580 and 9414290 for malformed coordinate records'):
    return {'action':'opened','repository':{'full_name':'chadkhalil21-svg/Plenum-Scientific-Intelligence'},'issue':{'number':101,'title':m.MISSION_TITLE,'user':{'login':actor},'body':'PLENUM_CHIEF_PUBLIC_DATA_MISSION_V1\nobjective: '+objective}}


def plan(ids):
    return {'steps':[{'tool':'noaa_metadata','station_ids':ids},{'tool':'station_validation','input_from':'noaa_metadata'}]}


class DataMissionTests(TestCase):
    def test_new_envelope_no_keyword_role_gate(self):
        self.assertEqual(m.parse_mission(event())['team'], ('public_research','public_program'))
        with self.assertRaises(PermissionError): m.parse_mission(event(actor='intruder'))
        with self.assertRaises(ValueError): m.parse_mission(event(objective='Check NOAA records without an explicit station'))

    def test_plan_cannot_expand_input_or_tools(self):
        for p in (plan(['1234567']), {'steps':list(reversed(plan(['8724580','9414290'])['steps']))}, {**plan(['8724580','9414290']), 'url':'https://evil.test'}):
            with self.assertRaises(ValueError): m.validate_data_plan(p, ('8724580','9414290'))

    def test_real_payload_dependency_and_resume(self):
        calls=[]
        def fetch(station):
            calls.append(station)
            return json.dumps({'stations':[{'id':station,'name':'Public gauge','lat':25.1,'lng':-80.2}]}).encode()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            with patch.object(m,'fetch_noaa_metadata',side_effect=fetch):
                r=m.execute_data_mission(event(),output_dir=root,planner=lambda ids:plan(list(ids)))
                self.assertTrue(r['bounded_metadata_contract_verified'])
                self.assertFalse(r['founder_objective_verified'])
                r=m.execute_data_mission(event(),output_dir=root,planner=lambda ids: self.fail('replanned'))
                self.assertEqual(r['new_worker_invocations'],0)
                self.assertEqual(calls,['8724580','9414290'])
                p=root/'workers/public_research/noaa.json'
                p.write_text('{}')
                with self.assertRaises(ValueError): m.execute_data_mission(event(),output_dir=root,planner=lambda ids:plan(list(ids)))

    def test_provider_identity_mismatch_never_success(self):
        with tempfile.TemporaryDirectory() as d, patch.object(m,'fetch_noaa_metadata',return_value=b'{"stations":[{"id":"1234567","name":"x","lat":1,"lng":2}]}'):
            with self.assertRaises(ValueError): m.execute_data_mission(event(),output_dir=Path(d),planner=lambda ids:plan(list(ids)))

    def test_plan_and_objective_binding_refuse_tamper(self):
        def fetch(station):
            return json.dumps({'stations':[{'id':station,'name':'Gauge','lat':1,'lng':2}]}).encode()
        with tempfile.TemporaryDirectory() as d, patch.object(m,'fetch_noaa_metadata',side_effect=fetch):
            root=Path(d)
            m.execute_data_mission(event(),output_dir=root,planner=lambda ids:plan(list(ids)))
            p=root/'chief-data-plan-101.json'
            data=json.loads(p.read_text())
            data['plan']['steps'][0]['station_ids'].reverse()
            p.write_text(json.dumps(data))
            with self.assertRaises(ValueError): m.execute_data_mission(event(),output_dir=root)

    def test_bad_coordinates_fail_before_validation(self):
        for value in (True, 999, float('nan')):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as d, patch.object(m,'fetch_noaa_metadata',side_effect=lambda station:json.dumps({'stations':[{'id':station,'name':'Gauge','lat':value,'lng':2}]}).encode()):
                with self.assertRaises(ValueError): m.execute_data_mission(event(),output_dir=Path(d),planner=lambda ids:plan(list(ids)))

    def test_fetch_refuses_redirect_and_oversize(self):
        class Response:
            status=200
            def __init__(self,url,raw): self.url=url; self.raw=raw
            def __enter__(self): return self
            def __exit__(self,*args): return False
            def geturl(self): return self.url
            def read(self,limit): return self.raw[:limit]
        from unittest.mock import Mock
        for response in (Response('https://evil.test',b'{}'), Response('https://api.tidesandcurrents.noaa.gov/mdapi/prod/webapi/stations/8724580.json',b'x'*500001)):
            opener=Mock()
            opener.open.return_value=response
            with patch('urllib.request.build_opener',return_value=opener):
                with self.assertRaises(ValueError): m.fetch_noaa_metadata('8724580')
        with self.assertRaises(ValueError): m.fetch_noaa_metadata('../8724580')

    def test_model_requires_real_loopback_runner(self):
        with patch.dict('os.environ',{},clear=True):
            with self.assertRaises(PermissionError): m.plan_data_mission('Check a public station',('8724580',))

    def test_interrupted_validation_reuses_research_without_refetch(self):
        def fetch(station):
            return json.dumps({'stations':[{'id':station,'name':'Gauge','lat':1,'lng':2}]}).encode()
        with tempfile.TemporaryDirectory() as d, patch.object(m,'fetch_noaa_metadata',side_effect=fetch):
            root=Path(d)
            m.execute_data_mission(event(),output_dir=root,planner=lambda ids:plan(list(ids)))
            cp=root/'chief-checkpoint-101.json'
            data=json.loads(cp.read_text())
            entry=data['results']['public_program']
            data['results']['public_program']={k:entry[k] for k in ('attempt','plan_sha256')}
            data['results']['public_program'].update(status='RUNNING',verified=False)
            cp.write_text(json.dumps(data))
            with patch.object(m,'fetch_noaa_metadata',side_effect=AssertionError('research repeated')):
                r=m.execute_data_mission(event(),output_dir=root)
            self.assertTrue(r['bounded_metadata_contract_verified'])
            self.assertFalse(r['founder_objective_verified'])
            self.assertEqual(r['new_worker_invocations'],1)
            self.assertEqual(json.loads(cp.read_text())['results']['public_program']['attempt'],2)

    def test_checkpoint_cannot_hash_decoy_instead_of_consumed_artifact(self):
        from plenum_ai.mission_checkpoint import artifact_digest
        def fetch(station):
            return json.dumps({'stations':[{'id':station,'name':'Gauge','lat':1,'lng':2}]}).encode()
        with tempfile.TemporaryDirectory() as d, patch.object(m,'fetch_noaa_metadata',side_effect=fetch):
            root=Path(d)
            m.execute_data_mission(event(),output_dir=root,planner=lambda ids:plan(list(ids)))
            cp=root/'chief-checkpoint-101.json'
            data=json.loads(cp.read_text())
            decoy=root/'workers/public_research/decoy.json'
            decoy.write_text('{}')
            entry=data['results']['public_research']
            entry.update(artifact_path='workers/public_research/decoy.json',output_artifact='workers/public_research/decoy.json',sha256=artifact_digest(root,'workers/public_research/decoy.json'))
            cp.write_text(json.dumps(data))
            with self.assertRaises(ValueError): m.execute_data_mission(event(),output_dir=root)

    def test_malformed_metadata_is_completed_review_with_explicit_warning(self):
        def fetch(station):
            return json.dumps({'stations':[{'id':station,'name':'','lat':1,'lng':2}]}).encode()
        with tempfile.TemporaryDirectory() as d, patch.object(m,'fetch_noaa_metadata',side_effect=fetch):
            r=m.execute_data_mission(event(),output_dir=Path(d),planner=lambda ids:plan(list(ids)))
            self.assertTrue(r['bounded_metadata_contract_verified'])
            self.assertFalse(r['founder_objective_verified'])
            self.assertEqual(r['metadata_review']['invalid_rows'],2)
            self.assertFalse(r['metadata_review']['all_metadata_structurally_valid'])
            self.assertEqual(len(r['metadata_review']['warnings']),2)
