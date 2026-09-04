import os
import tempfile
import unittest

fd, path = tempfile.mkstemp(); os.close(fd)
os.environ['DATABASE_PATH'] = path
import app

class PipelineRuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): app.init_db()
    @classmethod
    def tearDownClass(cls): os.unlink(path)
    def test_advance_moves_exactly_one_stage(self):
        with app.db() as con:
            user=con.execute("SELECT * FROM users WHERE role='recruiter'").fetchone()
            candidate=con.execute("SELECT * FROM applications WHERE stage='Applied' LIMIT 1").fetchone()
            ok, _ = app.advance(con,candidate,user)
            self.assertTrue(ok)
            self.assertEqual(con.execute("SELECT stage FROM applications WHERE id=?",(candidate['id'],)).fetchone()[0], 'Screening')
    def test_rejected_cannot_advance(self):
        with app.db() as con:
            user=con.execute("SELECT * FROM users WHERE role='recruiter'").fetchone()
            candidate=con.execute("SELECT * FROM applications WHERE stage='Rejected' LIMIT 1").fetchone()
            ok, message = app.advance(con,candidate,user)
            self.assertFalse(ok); self.assertIn('reinstated', message)
