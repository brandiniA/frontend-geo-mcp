"""Initial schema: projects and components.

Revision ID: 001
Revises: 
Create Date: 2025-10-26 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create projects table
    op.create_table(
        'projects',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('repository_url', sa.String(), nullable=False),
        sa.Column('branch', sa.String(), server_default='main'),
        sa.Column('type', sa.String(), server_default='application'),
        sa.Column('is_active', sa.String(), server_default='true'),
        sa.Column('last_sync', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )

    # Create components table
    op.create_table(
        'components',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('project_id', sa.String(), nullable=False),
        sa.Column('file_path', sa.String(), nullable=False),
        sa.Column('props', postgresql.JSON(), server_default='[]'),
        sa.Column('hooks', postgresql.JSON(), server_default='[]'),
        sa.Column('imports', postgresql.JSON(), server_default='[]'),
        sa.Column('exports', postgresql.JSON(), server_default='[]'),
        sa.Column('component_type', sa.String(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('jsdoc', postgresql.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', 'project_id', 'file_path', name='idx_components_unique')
    )

    # Create indexes
    op.create_index('idx_components_name', 'components', ['name'])
    op.create_index('idx_components_project', 'components', ['project_id'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_components_project', table_name='components')
    op.drop_index('idx_components_name', table_name='components')

    # Drop tables
    op.drop_table('components')
    op.drop_table('projects')
