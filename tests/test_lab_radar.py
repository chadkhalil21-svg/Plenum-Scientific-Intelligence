import unittest
from plenum_ai.lab_radar import summarize,update_seen

def fixture():
    a={"category":"universities","publisher":"MIT","source":"mit_labs",
       "title":"University new experimental system","url":"https://news.mit.edu/a",
       "untrusted_external_content":True}
    b={"category":"journals","publisher":"Nature","source":"nature",
       "title":"New research article","url":"https://nature.com/b",
       "untrusted_external_content":True}
    c={"category":"business","publisher":"World Bank","source":"bank",
       "title":"GDP","url":"https://worldbank.org/c",
       "untrusted_external_content":True}
    return {"schema":"plenum-public-horizon-snapshot-v1","records":[a,b,c],
       "providers":[{"source":"mit_labs","status":"retrieved_metadata","records":[a]},
                    {"source":"nature","status":"retrieved_metadata","records":[b]},
                    {"source":"offline","status":"unavailable","records":[]}]}
class RadarTests(unittest.TestCase):
    def test_first_scan_and_failed_provider(self):
        x=summarize(fixture())
        self.assertTrue(x["first_scan_baseline"])
        self.assertEqual(x["sources_returning_records"],2)
        self.assertEqual(x["source_outages"],["offline"])
        self.assertEqual(x["new_public_links_before_limit"],2)
        self.assertFalse(x["independent_laboratory_breakthrough_verified"])
        self.assertFalse(x["AGI_demonstrated"])
        self.assertEqual(len(x["signals"]),2)
    def test_followup_dedup_and_new_link(self):
        old=update_seen(None,fixture())
        self.assertEqual(len(old),2)
        self.assertEqual(summarize(fixture(),old)["signals"],[])
        nxt=fixture()
        nxt["records"][0]["url"]="https://news.mit.edu/new"
        self.assertEqual(len(summarize(nxt,old)["signals"]),1)
        self.assertEqual(len(update_seen(old,nxt)),3)
    def test_malformed_content_fail_closed(self):
        with self.assertRaises(ValueError): summarize(fixture(),["https://x.com","https://x.com"])
        with self.assertRaises(ValueError): summarize(fixture(),["https://bad.com:abc"])
        with self.assertRaises(ValueError): summarize({"schema":"other"})
        wrong=fixture();wrong["records"]=wrong["records"]*45
        with self.assertRaises(ValueError): summarize(wrong)
if __name__=="__main__": unittest.main()
