"""Initial database schema for onboarding calls

Revision ID: 001_initial_schema
Revises: 
Create Date: 2024-01-01 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create call_transcripts table
    op.create_table('call_transcripts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(255), nullable=False),
        sa.Column('facilitator_name', sa.String(255), nullable=False),
        sa.Column('facilitator_phone', sa.String(20), nullable=False),
        sa.Column('call_start_time', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('call_end_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('call_duration_seconds', sa.Integer(), nullable=True),
        sa.Column('call_status', sa.String(50), nullable=False),
        sa.Column('outcome', sa.String(100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('callback_requested', sa.Boolean(), nullable=False, default=False),
        sa.Column('callback_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_call_transcripts_session_id'), 'call_transcripts', ['session_id'], unique=True)
    op.create_index(op.f('ix_call_transcripts_facilitator_phone'), 'call_transcripts', ['facilitator_phone'])
    op.create_index(op.f('ix_call_transcripts_call_start_time'), 'call_transcripts', ['call_start_time'])

    # Create conversation_turns table
    op.create_table('conversation_turns',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('transcript_id', sa.Integer(), nullable=False),
        sa.Column('turn_number', sa.Integer(), nullable=False),
        sa.Column('speaker', sa.String(50), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['transcript_id'], ['call_transcripts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_conversation_turns_transcript_id'), 'conversation_turns', ['transcript_id'])
    op.create_index(op.f('ix_conversation_turns_timestamp'), 'conversation_turns', ['timestamp'])


def downgrade() -> None:
    op.drop_index(op.f('ix_conversation_turns_timestamp'), table_name='conversation_turns')
    op.drop_index(op.f('ix_conversation_turns_transcript_id'), table_name='conversation_turns')
    op.drop_table('conversation_turns')
    op.drop_index(op.f('ix_call_transcripts_call_start_time'), table_name='call_transcripts')
    op.drop_index(op.f('ix_call_transcripts_facilitator_phone'), table_name='call_transcripts')
    op.drop_index(op.f('ix_call_transcripts_session_id'), table_name='call_transcripts')
    op.drop_table('call_transcripts')
