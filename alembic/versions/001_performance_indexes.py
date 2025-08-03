"""Add performance indexes for search optimization

Revision ID: 001_performance_indexes
Revises: 90cf37214ad1
Create Date: 2025-08-03 07:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '001_performance_indexes'
down_revision = '90cf37214ad1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add performance indexes for search optimization"""
    
    # Candidates table indexes
    op.execute('CREATE INDEX IF NOT EXISTS idx_candidates_active ON candidates(is_active) WHERE is_active = true')
    op.execute('CREATE INDEX IF NOT EXISTS idx_candidates_company ON candidates(current_company)')
    op.execute('CREATE INDEX IF NOT EXISTS idx_candidates_experience ON candidates(total_experience_years)')
    op.execute('CREATE INDEX IF NOT EXISTS idx_candidates_location ON candidates(location)')
    
    # Resumes table indexes
    op.execute('CREATE INDEX IF NOT EXISTS idx_resumes_status ON resumes(parsing_status)')
    op.execute('CREATE INDEX IF NOT EXISTS idx_resumes_candidate ON resumes(candidate_id)')
    # Cast JSON to JSONB for GIN indexes
    op.execute('CREATE INDEX IF NOT EXISTS idx_resumes_skills_gin ON resumes USING gin((skills::jsonb))')
    op.execute('CREATE INDEX IF NOT EXISTS idx_resumes_education_gin ON resumes USING gin((education::jsonb))')
    # Skip search_vector index for now as it may not exist yet
    # op.execute('CREATE INDEX IF NOT EXISTS idx_resumes_search_vector ON resumes USING gin(to_tsvector(\'english\', search_vector))')
    
    # Work experiences table indexes  
    op.execute('CREATE INDEX IF NOT EXISTS idx_work_exp_candidate ON work_experiences(candidate_id)')
    op.execute('CREATE INDEX IF NOT EXISTS idx_work_exp_company_dept ON work_experiences(company, department)')
    op.execute('CREATE INDEX IF NOT EXISTS idx_work_exp_dates ON work_experiences(start_date, end_date)')
    op.execute('CREATE INDEX IF NOT EXISTS idx_work_exp_current ON work_experiences(is_current) WHERE is_current = true')
    # Check if colleagues column exists before creating index
    # op.execute('CREATE INDEX IF NOT EXISTS idx_work_exp_colleagues_gin ON work_experiences USING gin((colleagues::jsonb))')
    
    # Composite indexes for common search patterns
    op.execute('CREATE INDEX IF NOT EXISTS idx_candidates_resume_active ON candidates(id) INCLUDE (current_company, total_experience_years) WHERE is_active = true')
    op.execute('CREATE INDEX IF NOT EXISTS idx_work_exp_overlap ON work_experiences(company, start_date, end_date, candidate_id)')
    
    # Search history indexes for analytics
    op.execute('CREATE INDEX IF NOT EXISTS idx_search_history_user ON search_history(user_id)')
    op.execute('CREATE INDEX IF NOT EXISTS idx_search_history_type ON search_history(search_type)')
    op.execute('CREATE INDEX IF NOT EXISTS idx_search_history_time ON search_history(searched_at)')
    
    # Users table indexes
    op.execute('CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active) WHERE is_active = true')


def downgrade() -> None:
    """Remove performance indexes"""
    
    # Drop all the indexes we created
    op.execute('DROP INDEX IF EXISTS idx_candidates_active')
    op.execute('DROP INDEX IF EXISTS idx_candidates_company') 
    op.execute('DROP INDEX IF EXISTS idx_candidates_experience')
    op.execute('DROP INDEX IF EXISTS idx_candidates_location')
    
    op.execute('DROP INDEX IF EXISTS idx_resumes_status')
    op.execute('DROP INDEX IF EXISTS idx_resumes_candidate')
    op.execute('DROP INDEX IF EXISTS idx_resumes_skills_gin')
    op.execute('DROP INDEX IF EXISTS idx_resumes_education_gin')
    # op.execute('DROP INDEX IF EXISTS idx_resumes_search_vector')
    
    op.execute('DROP INDEX IF EXISTS idx_work_exp_candidate')
    op.execute('DROP INDEX IF EXISTS idx_work_exp_company_dept')
    op.execute('DROP INDEX IF EXISTS idx_work_exp_dates')
    op.execute('DROP INDEX IF EXISTS idx_work_exp_current')
    # op.execute('DROP INDEX IF EXISTS idx_work_exp_colleagues_gin')
    
    op.execute('DROP INDEX IF EXISTS idx_candidates_resume_active')
    op.execute('DROP INDEX IF EXISTS idx_work_exp_overlap')
    
    op.execute('DROP INDEX IF EXISTS idx_search_history_user')
    op.execute('DROP INDEX IF EXISTS idx_search_history_type')
    op.execute('DROP INDEX IF EXISTS idx_search_history_time')
    
    op.execute('DROP INDEX IF EXISTS idx_users_active')