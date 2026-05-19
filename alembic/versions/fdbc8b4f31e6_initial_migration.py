"""initial migration - create all tables

Revision ID: fdbc8b4f31e6
Revises:
Create Date: 2026-05-19 11:04:55

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fdbc8b4f31e6'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建所有表"""
    # device_memory 表
    op.create_table('device_memory',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('device_id', sa.String(length=50), nullable=False),
        sa.Column('device_type', sa.String(length=50), nullable=True),
        sa.Column('device_model', sa.String(length=100), nullable=True),
        sa.Column('manufacturer', sa.String(length=100), nullable=True),
        sa.Column('install_date', sa.DateTime(), nullable=True),
        sa.Column('install_location', sa.String(length=200), nullable=True),
        sa.Column('last_service_date', sa.DateTime(), nullable=True),
        sa.Column('total_error_count', sa.Integer(), nullable=True),
        sa.Column('common_errors', sa.JSON(), nullable=True),
        sa.Column('last_error_time', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('metadata_ext', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('device_id')
    )
    op.create_index(op.f('ix_device_memory_device_id'), 'device_memory', ['device_id'], unique=True)

    # solution_history 表
    op.create_table('solution_history',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('session_id', sa.String(length=50), nullable=True),
        sa.Column('device_id', sa.String(length=50), nullable=True),
        sa.Column('error_code', sa.String(length=20), nullable=True),
        sa.Column('symptoms', sa.JSON(), nullable=True),
        sa.Column('root_cause', sa.Text(), nullable=True),
        sa.Column('solution', sa.Text(), nullable=True),
        sa.Column('steps_taken', sa.JSON(), nullable=True),
        sa.Column('success', sa.Integer(), nullable=True),
        sa.Column('confidence', sa.Integer(), nullable=True),
        sa.Column('repair_duration', sa.Integer(), nullable=True),
        sa.Column('repair_cost', sa.Float(), nullable=True),
        sa.Column('technician', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_solution_history_created_at'), 'solution_history', ['created_at'], unique=False)
    op.create_index(op.f('ix_solution_history_device_id'), 'solution_history', ['device_id'], unique=False)
    op.create_index(op.f('ix_solution_history_error_code'), 'solution_history', ['error_code'], unique=False)
    op.create_index(op.f('ix_solution_history_session_id'), 'solution_history', ['session_id'], unique=False)

    # diagnosis_session 表
    op.create_table('diagnosis_session',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('session_id', sa.String(length=50), nullable=False),
        sa.Column('device_id', sa.String(length=50), nullable=True),
        sa.Column('user_id', sa.String(length=50), nullable=True),
        sa.Column('current_state', sa.JSON(), nullable=True),
        sa.Column('conversation_history', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('last_active', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id')
    )
    op.create_index(op.f('ix_diagnosis_session_session_id'), 'diagnosis_session', ['session_id'], unique=True)

    # error_report 表
    op.create_table('error_report',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('report_id', sa.String(length=50), nullable=False),
        sa.Column('device_id', sa.String(length=50), nullable=False),
        sa.Column('error_code', sa.String(length=20), nullable=True),
        sa.Column('error_type', sa.String(length=50), nullable=True),
        sa.Column('severity', sa.String(length=20), nullable=True),
        sa.Column('symptoms', sa.JSON(), nullable=True),
        sa.Column('context', sa.JSON(), nullable=True),
        sa.Column('source', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('assigned_to', sa.String(length=50), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('resolution', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('report_id')
    )
    op.create_index(op.f('ix_error_report_created_at'), 'error_report', ['created_at'], unique=False)
    op.create_index(op.f('ix_error_report_device_id'), 'error_report', ['device_id'], unique=False)
    op.create_index(op.f('ix_error_report_error_code'), 'error_report', ['error_code'], unique=False)


def downgrade() -> None:
    """删除所有表"""
    op.drop_index(op.f('ix_error_report_error_code'), table_name='error_report')
    op.drop_index(op.f('ix_error_report_device_id'), table_name='error_report')
    op.drop_index(op.f('ix_error_report_created_at'), table_name='error_report')
    op.drop_table('error_report')

    op.drop_index(op.f('ix_diagnosis_session_session_id'), table_name='diagnosis_session')
    op.drop_table('diagnosis_session')

    op.drop_index(op.f('ix_solution_history_session_id'), table_name='solution_history')
    op.drop_index(op.f('ix_solution_history_error_code'), table_name='solution_history')
    op.drop_index(op.f('ix_solution_history_device_id'), table_name='solution_history')
    op.drop_index(op.f('ix_solution_history_created_at'), table_name='solution_history')
    op.drop_table('solution_history')

    op.drop_index(op.f('ix_device_memory_device_id'), table_name='device_memory')
    op.drop_table('device_memory')
