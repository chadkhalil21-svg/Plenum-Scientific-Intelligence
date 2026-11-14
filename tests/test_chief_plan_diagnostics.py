"""No inference: preserve safe stage evidence for original668/670 failures."""
import json
import sys
import tempfile
import types
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch
from plenum_ai import chief_contract_plan as m


SCOPE={'station_ids':['8724580'],'dois':[],'cooling':None}
ENV={'PLENUM_EPHEMERAL_RUNNER':'confirmed','PLENUM_CHIEF_MODEL_URL':m.MODEL_URL}

class PlannerFailureDiagnostics(TestCase):
    def stub(self, content):
        module=types.ModuleType('langchain_ollama')
        class StubModel:
            def __init__(self, **kwargs):pass
            def invoke(self, messages):
                return types.SimpleNamespace(content=content,response_metadata={'done_reason':'length','eval_count':600,'private':'DO_NOT_EXPORT'},usage_metadata={'input_tokens':223,'output_tokens':600})
        module.ChatOllama=StubModel
        return module

    def test_live_model_schema_allows_only_explicitly_requested_contracts(self):
        # Original #679 returned six tools including unrequested cooling;
        # the structured schema itself must not offer those extras.
        captured=[]
        class FakeModel:
            def __init__(self,**kw):
                captured.append(kw)
            def invoke(self,messages):
                return types.SimpleNamespace(content=json.dumps({'steps':[
                    {'tool':'noaa_metadata'},
                    {'tool':'station_validation','input_from':'noaa_metadata'},
                    {'tool':'crossref_metadata'},
                    {'tool':'bibliography_readback','input_from':'crossref_metadata'}]}),
                    response_metadata={'done_reason':'stop'})
        module=types.ModuleType('langchain_ollama')
        module.ChatOllama=FakeModel
        scope={'station_ids':['8723214'],'dois':['10.1029/2022jc018496'],'cooling':None}
        with patch.dict(sys.modules,{'langchain_ollama':module}),patch.dict('os.environ',ENV):
            plan=m.model_plan('Inspect NOAA 8723214 and DOI 10.1029/2022JC018496 metadata',scope)
        self.assertEqual(len(plan['steps']),4)
        fmt=captured[0]['format']['properties']['steps']
        self.assertEqual((fmt['minItems'],fmt['maxItems']),(4,4))
        allowed=set()
        for option in fmt['items']['anyOf']:
            allowed.update(option['properties']['tool']['enum'])
        self.assertEqual(allowed,{'noaa_metadata','station_validation',
                                  'crossref_metadata','bibliography_readback'})
        self.assertNotIn('cooling_solution',json.dumps(fmt))
        self.assertNotIn('cooling_readback',json.dumps(fmt))

    def test_invalid_json_reports_stage_and_length_without_raw_output(self):
        with patch.dict(sys.modules,{'langchain_ollama':self.stub('DO_NOT_EXPORT invalid JSON')}),patch.dict('os.environ',ENV):
            with self.assertRaises(ValueError) as caught:
                m.model_plan('Review NOAA station metadata',SCOPE)
        diagnostic=caught.exception.diagnostic
        self.assertEqual(diagnostic['stage'],'MODEL_JSON')
        self.assertEqual(diagnostic['code'],'INVALID_JSON')
        self.assertEqual(diagnostic['response']['done_reason'],'length')
        self.assertEqual(diagnostic['response']['output_tokens'],600)
        self.assertNotIn('DO_NOT_EXPORT',json.dumps(diagnostic))

    def test_unknown_tool_is_redacted_while_validation_stays_strict(self):
        output=json.dumps({'steps':[{'tool':'DO_NOT_EXPORT private action'},{'tool':'station_validation','input_from':'noaa_metadata'}]})
        with patch.dict(sys.modules,{'langchain_ollama':self.stub(output)}),patch.dict('os.environ',ENV):
            with self.assertRaises(ValueError) as caught:m.model_plan('Review NOAA station metadata',SCOPE)
        d=caught.exception.diagnostic
        self.assertEqual(d['stage'],'MODEL_CONTRACT_VALIDATION')
        self.assertEqual(d['code'],'CONTRACT_SET_MISMATCH')
        self.assertEqual(d['response']['tool_names'],['UNKNOWN','station_validation'])
        self.assertNotIn('DO_NOT_EXPORT',json.dumps(d))

    def test_original_failure_report_keeps_only_safe_diagnostic(self):
        from plenum_ai.chief_team_mission import execute
        event={'action':'opened','repository':{'full_name':'chadkhalil21-svg/Plenum-Scientific-Intelligence'},'issue':{'number':668,'title':'[Plenum Chief] public mission','user':{'login':'chadkhalil21-svg'},'body':m.MAGIC+'\nobjective: Review NOAA 8724580 and DOI 10.1038/nature14539 metadata quality'}}
        with tempfile.TemporaryDirectory() as d,patch.dict(sys.modules,{'langchain_ollama':self.stub('DO_NOT_EXPORT bad')}),patch.dict('os.environ',ENV):
            result=execute(event,output_dir=Path(d))
        self.assertEqual(result['planning_failure']['stage'],'MODEL_JSON')
        self.assertFalse(result['independent_verified'])
        self.assertNotIn('DO_NOT_EXPORT',json.dumps(result))

    def test_provider_exception_and_bad_provenance_have_fixed_codes(self):
        module=self.stub('{}')
        module.ChatOllama=lambda **kw: types.SimpleNamespace(invoke=lambda _: (_ for _ in ()).throw(RuntimeError('DO_NOT_EXPORT provider detail')))
        with patch.dict(sys.modules,{'langchain_ollama':module}),patch.dict('os.environ',ENV):
            with self.assertRaises(ValueError) as caught:m.model_plan('Review NOAA metadata',SCOPE)
        self.assertEqual(caught.exception.diagnostic['stage'],'MODEL_INVOCATION')
        self.assertNotIn('DO_NOT_EXPORT',json.dumps(caught.exception.diagnostic))
        with self.assertRaises(ValueError) as caught:m.validate_inference_receipt({'provider':'DO_NOT_EXPORT'})
        self.assertEqual(caught.exception.diagnostic['stage'],'PLAN_PROVENANCE')

    def test_nonstring_model_tool_name_is_safely_classified(self):
        output=json.dumps({'steps':[{'tool':['DO_NOT_EXPORT']},{'tool':'station_validation','input_from':'noaa_metadata'}]})
        with patch.dict(sys.modules,{'langchain_ollama':self.stub(output)}),patch.dict('os.environ',ENV):
            with self.assertRaises(ValueError) as caught:m.model_plan('Review NOAA metadata',SCOPE)
        self.assertEqual(caught.exception.diagnostic['code'],'INVALID_TOOL_TYPE')
        self.assertNotIn('DO_NOT_EXPORT',json.dumps(caught.exception.diagnostic))
