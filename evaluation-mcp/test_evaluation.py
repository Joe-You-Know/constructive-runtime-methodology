import base64
import hashlib
import unittest
from unittest.mock import patch
import app

class EvaluationTests(unittest.TestCase):
    def test_pinned_sparse(self):
        d=bytearray(b"abc1234!"*131072)
        import random
        rng=random.Random(54)
        for j in range(0,len(d),1021): d[j]=rng.randrange(256)
        result=app._measure(bytes(d))
        self.assertEqual(result["crtg4_bytes"],3129)
        self.assertTrue(result["exact_crtg4_recovery"])
        self.assertEqual(result["gzip6_bytes"],5731)
    def test_fixtures(self):
        for k in ("repeat","sparse-defects","random","mixed"):
            with self.subTest(k=k):
                r=app.evaluate_workload(k,"",4096,54)
                self.assertTrue(r["exact_crtg4_recovery"])
                self.assertEqual(r["source_bytes"],4096)
    def test_text_and_base64(self):
        d="abcΩ".encode()
        x=base64.b64encode(d).decode()
        a=app.evaluate_workload("text","abcΩ")
        b=app.evaluate_workload("base64",x)
        self.assertEqual(a["source_sha256"],b["source_sha256"])
        self.assertTrue(app.verify_reconstruction(x,hashlib.sha256(d).hexdigest())["verified"])
        self.assertFalse(app.verify_reconstruction(x,"0"*64)["verified"])
    def test_bounds(self):
        for args in [("text","x"*65537),("base64","%%%%"),("repeat","",65537,1),("repeat","",1,-1),("bad","",1,1),("repeat","payload",1,1)]:
            with self.subTest(args=str(args)[:50]),self.assertRaises(ValueError):
                app.evaluate_workload(*args)
    def test_storage(self):
        self.assertEqual(app.calculate_storage_economics(100,50,10)["bytes_saved"],500)
        with self.assertRaises(ValueError): app.calculate_storage_economics(100,50,1,float("nan"))
    def test_purchase_fail_closed(self):
        with patch("app.get_product_status",return_value={"status":"unavailable"}):
            self.assertIsNone(app.get_purchase_link()["url"])
        with patch("app.get_product_status",return_value={"status":"retrieved","offer":{"purchase_available":False}}):
            self.assertIsNone(app.get_purchase_link()["url"])
        with patch("app.get_product_status",return_value={"status":"retrieved","offer":{"purchase_available":True}}):
            self.assertTrue(app.get_purchase_link()["url"].endswith("?src=eval-mcp"))
    def test_pinned_report(self):
        r=app.get_benchmark_results()
        self.assertEqual(len(r["rows"]),23)
        self.assertEqual(sum(x["v4Bytes"]<x["gzipBytes"] for x in r["rows"]),19)
        self.assertFalse(r["commercialRuntimeEvaluated"])

if __name__=="__main__":
    unittest.main()
