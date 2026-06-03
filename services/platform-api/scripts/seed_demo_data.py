"""
Robust demo seed script for careOS.
Creates realistic but completely fictional clinical data for testing the full governance stack.
"""

import asyncio
import json
import uuid
from datetime import date

from sqlalchemy import text

from app.db.session import async_session
from app.core.security import DEMO_USERS
from app.providers.embedding_provider import embedding_provider


async def seed():
    print("🌱 Seeding careOS demo environment...")

    async with async_session() as session:
        tenant_id = "tenant_hospital_a"

        # Ensure tenant exists
        await session.execute(text("""
            INSERT INTO tenants (id, name, slug) 
            VALUES (:id, 'Metropolitan Health System', 'metropolitan')
            ON CONFLICT (id) DO NOTHING
        """), {"id": tenant_id})

        await session.execute(text("""
            INSERT INTO hospitals (id, tenant_id, name)
            VALUES ('hosp_001', :tenant, 'Metropolitan General Hospital')
            ON CONFLICT (id) DO NOTHING
        """), {"tenant": tenant_id})

        # Users
        for email, data in DEMO_USERS.items():
            await session.execute(text("""
                INSERT INTO users (id, tenant_id, email, full_name, role)
                VALUES (:id, :tenant, :email, :name, :role)
                ON CONFLICT (id) DO NOTHING
            """), {
                "id": data["user_id"], "tenant": tenant_id, "email": email,
                "name": data["name"], "role": data["role"]
            })

        # Patients
        for pid, name, mrn, dob in [
            ("pat_001", "Maria Gonzalez", "MRN-784291", "1985-03-12"),
            ("pat_002", "Robert Thompson", "MRN-903112", "1958-11-04"),
        ]:
            await session.execute(text("""
                INSERT INTO patients (id, tenant_id, mrn, full_name, date_of_birth)
                VALUES (:id, :tenant, :mrn, :name, :dob)
                ON CONFLICT (id) DO NOTHING
            """), {"id": pid, "tenant": tenant_id, "mrn": mrn, "name": name, "dob": dob})

        # Encounter
        await session.execute(text("""
            INSERT INTO encounters (id, tenant_id, patient_id, encounter_type, status, started_at)
            VALUES ('enc_784291_001', :tenant, 'pat_001', 'inpatient', 'discharged', now() - interval '4 days')
            ON CONFLICT (id) DO NOTHING
        """), {"tenant": tenant_id})

        # High-quality synthetic documents (completely fictional, safe for demos)
        synthetic_docs = [
            {
                "doc_type": "lab_report",
                "title": "Comprehensive Metabolic Panel - May 22 2026",
                "content": "Sodium 138 mmol/L (normal), Potassium 4.1 mmol/L, Creatinine 0.9 mg/dL, Glucose 112 mg/dL (slightly elevated), HbA1c 6.8%. Liver function tests within normal limits. No critical or panic values reported.",
            },
            {
                "doc_type": "progress_note",
                "title": "Hospitalist Progress Note - May 23 07:15",
                "content": "Patient reports improved dyspnea overnight. BP 128/82, HR 88, RR 18, SpO2 96% on room air. Lungs clear. Continue current medications. PT/OT evaluation completed with recommendation for home health. Plan: possible discharge tomorrow if home O2 authorization obtained and transportation confirmed.",
            },
            {
                "doc_type": "nursing_note",
                "title": "Night Shift Note - May 22/23",
                "content": "Slept intermittently for ~5 hours. No falls or safety events. Pain 3/10, controlled with acetaminophen. Family (daughter) at bedside this morning inquiring about discharge timeline and home care needs. Will continue to monitor.",
            },
            {
                "doc_type": "discharge_summary",
                "title": "Discharge Summary Draft",
                "content": "Primary: Acute decompensated heart failure, improved. Medications reconciled. Follow-up: Cardiology in 7 days, PCP in 14 days. Home health nursing + PT ordered. O2 at 2L/min continuous pending insurance authorization. Transportation: daughter will provide. Outstanding: final PT clearance note and oxygen prior auth.",
            },
            {
                "doc_type": "insurance_prior_auth",
                "title": "Prior Authorization Request - Home Oxygen",
                "content": "Requesting 12-month authorization for continuous oxygen 2L/min. Diagnosis: CHF with chronic hypoxia. Supporting documentation (ABG, oximetry, progress notes) attached. Patient is stable on current regimen.",
            },
            {
                "doc_type": "patient_message",
                "title": "Patient Portal Message - May 20",
                "content": "Hi team, I've been having some swelling in my legs again the last two days and feel more tired than usual. Should I be concerned or wait until my follow-up?",
            },
        ]

        for doc in synthetic_docs:
            doc_id = str(uuid.uuid4())
            await session.execute(text("""
                INSERT INTO documents (id, tenant_id, patient_id, doc_type, title, sensitivity_level, consent_scope, source_system)
                VALUES (:id, :tenant, 'pat_001', :dtype, :title, 'phi', 'treatment', 'ehr_demo')
                ON CONFLICT (id) DO NOTHING
            """), {
                "id": doc_id, "tenant": tenant_id, "dtype": doc["doc_type"], "title": doc["title"]
            })

            # Create real embeddings for high-quality vector search
            for idx, content in enumerate([doc["content"], doc["content"][:450]]):
                real_emb = embedding_provider.embed(content)
                await session.execute(text("""
                    INSERT INTO document_chunks 
                    (id, tenant_id, document_id, patient_id, chunk_index, content, doc_type, sensitivity_level, consent_scope, embedding, metadata_json)
                    VALUES 
                    (:id, :tenant, :doc_id, 'pat_001', :idx, :content, :dtype, 'phi', 'treatment', :emb, :meta)
                """), {
                    "id": str(uuid.uuid4()),
                    "tenant": tenant_id,
                    "doc_id": doc_id,
                    "idx": idx,
                    "content": content,
                    "dtype": doc["doc_type"],
                    "emb": real_emb,
                    "meta": json.dumps({"title": doc["title"]}),
                })

        await session.commit()

    print("✅ Demo data seeded successfully.")
    print("   Login emails: patient@hospital-a.demo | clinician@hospital-a.demo | nurse@hospital-a.demo")
    print("   care_coordinator@hospital-a.demo | admin@hospital-a.demo | compliance@hospital-a.demo")
    print("   Patient: pat_001 (Maria Gonzalez) with rich clinical context")


if __name__ == "__main__":
    asyncio.run(seed())
