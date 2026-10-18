"""Usunięcie starych dat urodzenia: migracja idempotentna, flaga 18+ zachowana, eksport CSV bez kolumny daty urodzenia."""
import os, sys, tempfile, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.pop("DATABASE_URL", None)
import store
store.FILE = os.path.join(tempfile.mkdtemp(), "kv.json"); store._mem = None
import dob_purge, testers, join, accounts, age

class T(unittest.TestCase):
    def setUp(self):
        store._mem = {}
        store.put("testers", {"A1": {"code": "A1", "name": "x", "email": "a@b.c", "reason": "r", "ring": "", "android": False, "t": 1, "until": 0,
                                     "granted": False, "consent": "tak", "dob": "1990-01-02", "adult": True, "adult_text": "ok", "adult_at": 5}})
        store.put("join_msgs", [{"id": "j1", "dob": "2000-05-05"}, {"id": "j2"}])            # tylko data, bez flagi
        store.put("team_apps", [{"id": "t1", "dob": "2015-01-01"}])                           # tylko data, niepełnoletni
        store.put("accounts", {"u1": {"uid": "u1", "dob": "1985-03-03", "adult": True}})
        store.put("age_decl", {"v1": {"vid": "v1", "dob": "1999-09-09", "adult": True, "adult_at": 3}})
        store.put("misc", {"deep": [{"birthdate": "1980-01-01", "adult_confirmed": True}]})
        store.put(dob_purge.MARK, None)
        self.log = []

    def test_purge(self):
        r = dob_purge.run(audit=lambda a, ip, d: self.log.append((a, d)))
        self.assertEqual(r["records"], 6)
        dump = repr(store._file())
        self.assertNotIn("1990-01-02", dump); self.assertNotIn("'dob'", dump); self.assertNotIn("birthdate", dump)
        self.assertTrue(store.get("join_msgs")[0]["adult_confirmed"])
        self.assertFalse(store.get("team_apps")[0]["adult_confirmed"])
        self.assertTrue(store.get("accounts")["u1"]["adult_confirmed"])
        self.assertTrue(store.get("testers")["A1"]["adult"])
        self.assertEqual(self.log, [("dob_purge", "records=6 keys=6")])
        self.assertNotIn("19", self.log[0][1].replace("records=6", ""))  # tylko liczby, bez dat
        # idempotentnie
        r2 = dob_purge.run(audit=lambda a, ip, d: self.log.append((a, d)))
        self.assertEqual(r2["records"], 0); self.assertEqual(len(self.log), 1)

    def test_csv_and_admin(self):
        csv = testers.csv_export()
        self.assertNotIn("data urodzenia", csv); self.assertNotIn("1990-01-02", csv)
        self.assertNotIn("dob", testers.admin_list()[0])
        self.assertTrue(all("dob" not in m for m in join.admin_list()))
        self.assertTrue(all("age" not in d for d in age.admin_list()))

    def test_backup_clean(self):
        b = {"testers": {"Z": {"dob": "1991-01-01", "adult": True}}}
        self.assertEqual(dob_purge.clean_value(b), 1); self.assertNotIn("dob", b["testers"]["Z"])

if __name__ == "__main__": unittest.main()
