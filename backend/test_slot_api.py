import sqlite3
import unittest
import json
import os
from app import app, init_db, get_db

class SlotApiTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.context = app.app_context()
        self.context.push()
        init_db()
        self.client = app.test_client()

        # Create a dummy doctor for testing
        db = get_db()
        # Check if doctor exists, if not create one
        cur = db.execute("INSERT INTO doctors (firstname, lastname, department, doctor_id) VALUES (?, ?, ?, ?)", 
                         ('Test', 'Doc', 'med', 'T001'))
        self.doctor_id = cur.lastrowid
        db.commit()

    def tearDown(self):
        # Clean up
        db = get_db()
        db.execute("DELETE FROM doctors WHERE id_doctor = ?", (self.doctor_id,))
        db.execute("DELETE FROM appointment_slots WHERE doctor_id = ?", (self.doctor_id,))
        db.commit()
        self.context.pop()

    def test_create_and_list_slots(self):
        # 1. Create Slot
        res = self.client.post(f'/api/doctors/{self.doctor_id}/slots', json={
            'date': '2026-03-01',
            'start_time': '09:00',
            'end_time': '10:00',
            'capacity': 5
        })
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        slot_id = data['slot_id']
        print(f"\n[TEST] Created slot_id: {slot_id}")

        # 2. List Slots
        res = self.client.get(f'/api/doctors/{self.doctor_id}/slots')
        self.assertEqual(res.status_code, 200)
        slots = res.get_json()
        self.assertEqual(len(slots), 1)
        self.assertEqual(slots[0]['slot_id'], slot_id)
        print(f"[TEST] Slots found: {slots}")

        # 3. Delete Slot
        res = self.client.delete(f'/api/slots/{slot_id}')
        self.assertEqual(res.status_code, 200)
        
        # Verify deletion
        res = self.client.get(f'/api/doctors/{self.doctor_id}/slots')
        slots = res.get_json()
        self.assertEqual(len(slots), 0)
        print("[TEST] Slot deleted successfully")

if __name__ == '__main__':
    unittest.main()
