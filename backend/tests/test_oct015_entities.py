"""OCT-015: Company, Program, Audit models and schemas."""
import uuid
from datetime import datetime, timezone

import pytest


class TestCompanyModel:
    def test_company_importable(self):
        from app.models.company import Company
        assert Company.__tablename__ == "companies"

    def test_company_has_columns(self):
        from app.models.company import Company
        cols = {c.name for c in Company.__table__.columns}
        assert {"id", "name_legal", "name_commercial", "description"} <= cols


class TestProgramModel:
    def test_program_importable(self):
        from app.models.program import Program, ProgramType, ProgramPlatform, ProgramStatus
        assert Program.__tablename__ == "programs"

    def test_program_type_values(self):
        from app.models.program import ProgramType
        assert ProgramType.EXTERNAL_AUDIT == "external_audit"
        assert ProgramType.BUG_BOUNTY == "bug_bounty"

    def test_program_has_company_fk(self):
        from app.models.program import Program
        fks = {fk.column.table.name for fk in Program.__table__.foreign_keys}
        assert "companies" in fks

    def test_program_has_scope_raw(self):
        from app.models.program import Program
        assert "scope_raw" in {c.name for c in Program.__table__.columns}


class TestAuditModel:
    def test_audit_importable(self):
        from app.models.audit import Audit, AuditStatus
        assert Audit.__tablename__ == "audits"

    def test_audit_status_values(self):
        from app.models.audit import AuditStatus
        assert set(AuditStatus) == {"draft", "active", "completed", "archived"}

    def test_audit_has_program_fk(self):
        from app.models.audit import Audit
        fks = {fk.column.table.name for fk in Audit.__table__.foreign_keys}
        assert "programs" in fks


class TestSchemas:
    def test_company_create(self):
        from app.schemas.company import CompanyCreate
        c = CompanyCreate(name_legal="ACME Corp")
        assert c.name_legal == "ACME Corp"

    def test_company_read_from_orm(self):
        from app.schemas.company import CompanyRead
        class FakeCompany:
            id = uuid.uuid4()
            name_legal = "ACME"
            name_commercial = None
            description = None
            created_at = datetime.now(timezone.utc)
        r = CompanyRead.model_validate(FakeCompany())
        assert r.name_legal == "ACME"

    def test_program_create(self):
        from app.schemas.program import ProgramCreate
        from app.models.program import ProgramType
        p = ProgramCreate(name="Bug Bounty 2026", program_type=ProgramType.BUG_BOUNTY)
        assert p.program_type == ProgramType.BUG_BOUNTY

    def test_audit_create(self):
        from app.schemas.audit import AuditCreate
        a = AuditCreate(title="Q1 Review")
        assert a.title == "Q1 Review"

    def test_migration_file_exists(self):
        from pathlib import Path
        p = Path(__file__).parent.parent / "app" / "database" / "migrations" / "versions" / "0004_company_program_audit.py"
        assert p.exists()
