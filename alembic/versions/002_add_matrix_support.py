"""Add matrix assessment support

Revision ID: 002_matrix
Revises: 001_initial
Create Date: 2025-10-23

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_matrix'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to items table
    with op.batch_alter_table('items', schema=None) as batch_op:
        batch_op.add_column(sa.Column('block', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('progressive_levels', sa.Boolean(), nullable=True, server_default='0'))
        batch_op.add_column(sa.Column('metadata_json', sa.Text(), nullable=True))
        batch_op.create_index(batch_op.f('ix_items_block'), ['block'], unique=False)
    
    # Make competency nullable (for new matrix questions)
    with op.batch_alter_table('items', schema=None) as batch_op:
        batch_op.alter_column('competency', nullable=True)
    
    # Add new columns to responses table
    with op.batch_alter_table('responses', schema=None) as batch_op:
        batch_op.add_column(sa.Column('matrix_points', sa.Integer(), nullable=True))
    
    # Add new columns to proficiency_snapshots table
    with op.batch_alter_table('proficiency_snapshots', schema=None) as batch_op:
        batch_op.add_column(sa.Column('block', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('raw_points', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('max_points', sa.Integer(), nullable=True))
        batch_op.create_index(batch_op.f('ix_proficiency_snapshots_block'), ['block'], unique=False)
    
    # Make competency nullable in proficiency_snapshots
    with op.batch_alter_table('proficiency_snapshots', schema=None) as batch_op:
        batch_op.alter_column('competency', nullable=True)


def downgrade():
    # Remove columns from proficiency_snapshots
    with op.batch_alter_table('proficiency_snapshots', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_proficiency_snapshots_block'))
        batch_op.drop_column('max_points')
        batch_op.drop_column('raw_points')
        batch_op.drop_column('block')
        batch_op.alter_column('competency', nullable=False)
    
    # Remove columns from responses
    with op.batch_alter_table('responses', schema=None) as batch_op:
        batch_op.drop_column('matrix_points')
    
    # Remove columns from items
    with op.batch_alter_table('items', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_items_block'))
        batch_op.drop_column('metadata_json')
        batch_op.drop_column('progressive_levels')
        batch_op.drop_column('block')
        batch_op.alter_column('competency', nullable=False)
