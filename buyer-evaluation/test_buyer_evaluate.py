import unittest
from buyer_evaluate import evaluate,fixture
class BuyerTests(unittest.TestCase):
    def test_baseline(self):
        for kind in ('affine','ordinary','random'):
            x=evaluate(fixture(kind,2048))
            self.assertTrue(x['freeReference']['roundTripExact'])
            self.assertIsNone(x['candidate'])
            self.assertEqual(x['decision'],'FREE_REFERENCE_UNTIL_MEASURED')
    def test_mismatch(self):
        self.assertEqual(evaluate(b'hello',b'a',b'bad')['decision'],'REJECT_ROUND_TRIP_MISMATCH')
    def test_security(self):
        self.assertEqual(evaluate(b'hello',b'a',b'hello',security=True)['decision'],'REJECT_UNMET_SECURITY_REQUIREMENT')
    def test_platform(self):
        self.assertEqual(evaluate(b'hello',b'a',b'hello')['decision'],'FREE_REFERENCE_PLATFORM_NOT_CONFIRMED')
    def test_economics(self):
        x=fixture('affine',2048)
        self.assertEqual(evaluate(x,b'a',x,windows=True)['decision'],'FREE_REFERENCE_NONPOSITIVE_NET_VALUE')
        r=evaluate(x,b'a',x,windows=True,copies=1000000,months=12,storage=.025,transfers=1000000,egress=.09,overhead=10)
        self.assertEqual(r['decision'],'POSITIVE_ESTIMATE_REQUIRES_BUYER_VALIDATION')
        self.assertEqual(r['candidate']['totalCandidateBytes'],11)
        self.assertAlmostEqual(r['candidate']['netValueBeforeTaxUSD'],r['candidate']['storageSavingsUSD']+r['candidate']['transferSavingsUSD']-4.99)
        self.assertEqual(evaluate(x,b'a',x,windows=True,overhead=len(x))['decision'],'FREE_REFERENCE_NONPOSITIVE_NET_VALUE')
if __name__=='__main__':unittest.main()
