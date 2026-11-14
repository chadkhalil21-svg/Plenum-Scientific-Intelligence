"""Obvious authorized contract pairs execute without any model inference."""
import json
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch
from plenum_ai import chief_contract_plan as m
from plenum_ai.chief_team_mission import preflight


def event(objective):
    return {'action':'opened','repository':{'full_name':'chadkhalil21-svg/Plenum-Scientific-Intelligence'},'issue':{'number':102,'title':'[Plenum Chief] public mission','user':{'login':'chadkhalil21-svg'},'body':m.MAGIC+'\nobjective: '+objective}}


class ObviousContractEfficiencyTests(TestCase):
    def test_single_pair_preflight_never_requests_model_dependencies_or_start(self):
        for objective in ('Review DOI 10.1038/nature14539 deposited title year and publisher', 'Inspect NOAA 8724580 station names and coordinates', 'Estimate cooling initial 358 K ambient 299 K rate 0.045 time 25'):
            with self.subTest(objective=objective):
                report=preflight(event(objective))
                self.assertTrue(report['planned_contract_mission'])
                self.assertFalse(report['planned_data_mission'])
                self.assertFalse(report['model_called'])
        report=preflight(event('Review NOAA 8724580 and DOI 10.1038/nature14539 metadata quality'))
        self.assertTrue(report['planned_data_mission'])

    def test_scholarly_pair_executes_actual_contracts_without_model_and_resumes(self):
        objective='Review DOI 10.1038/nature14539 deposited title year and publisher'
        record={'doi':'10.1038/nature14539','title':'Public deposited paper metadata','year':2015,'publisher':'Publisher'}
        calls=[]
        def read(doi,**kwargs):
            calls.append(doi)
            return record
        with tempfile.TemporaryDirectory() as d, patch.object(m,'model_plan',side_effect=AssertionError('unnecessary model')), patch.object(m,'read_crossref',side_effect=read):
            root=Path(d)
            result=m.execute_contract_mission(event(objective),output_dir=root)
            self.assertTrue(result['bounded_contracts_verified'])
            self.assertFalse(result['model_called'])
            self.assertFalse(result['chief_model_delegated'])
            self.assertEqual(result['dispatcher'],'original_chief_deterministic_public_contract_pair')
            self.assertEqual(result['inference_provenance']['provider'],'deterministic_contract_router')
            self.assertIsNone(result['inference_provenance']['model'])
            saved=json.loads((root/'chief-contract-plan-102.json').read_text())
            self.assertEqual(saved['inference']['provider'],'deterministic_contract_router')
            result=m.execute_contract_mission(event(objective),output_dir=root)
            self.assertEqual(result['new_worker_invocations'],0)
            self.assertEqual(len(calls),2)

    def test_composite_still_requires_existing_model_and_retains_failure(self):
        task=event('Review NOAA 8724580 and DOI 10.1038/nature14539 metadata quality')
        with tempfile.TemporaryDirectory() as d, patch.object(m,'model_plan',side_effect=RuntimeError('model unavailable')):
            with self.assertRaises(RuntimeError):m.execute_contract_mission(task,output_dir=Path(d))
            self.assertFalse((Path(d)/'chief-contract-plan-102.json').exists())
