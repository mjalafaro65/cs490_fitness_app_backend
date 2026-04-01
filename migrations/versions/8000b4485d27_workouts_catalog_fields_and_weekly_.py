"""workouts catalog fields and weekly scheduling

Revision ID: 8000b4485d27
Revises: 
Create Date: 2026-04-01 02:35:03.854409

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8000b4485d27'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Exercises: support catalog + user-created publishing
    with op.batch_alter_table('exercises') as batch_op:
        batch_op.add_column(sa.Column('created_by_user_id', sa.Integer(), nullable=True))
        batch_op.add_column(
            sa.Column('is_public', sa.Boolean(), nullable=False, server_default=sa.text('0'))
        )
        # NOTE: We intentionally do NOT create a FK constraint here.
        # Existing deployments may have users.user_id defined as a different integer type
        # (e.g., BIGINT/UNSIGNED), causing MySQL error 3780 when adding the FK.

    # WorkoutPlans: track copy lineage
    with op.batch_alter_table('workout_plans') as batch_op:
        batch_op.add_column(sa.Column('copied_from_plan_id', sa.Integer(), nullable=True))
        # Same rationale as above: avoid FK type incompatibilities on existing DBs.

    # WorkoutPlanDays: optional weekday + preferred time within the week
    with op.batch_alter_table('workout_plan_days') as batch_op:
        batch_op.add_column(sa.Column('weekday', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('session_time', sa.Time(), nullable=True))


def downgrade():
    with op.batch_alter_table('workout_plan_days') as batch_op:
        batch_op.drop_column('session_time')
        batch_op.drop_column('weekday')

    with op.batch_alter_table('workout_plans') as batch_op:
        batch_op.drop_column('copied_from_plan_id')

    with op.batch_alter_table('exercises') as batch_op:
        batch_op.drop_column('is_public')
        batch_op.drop_column('created_by_user_id')
