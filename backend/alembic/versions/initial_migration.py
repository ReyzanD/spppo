"""Initial migration: create all core tables.

Tables:
- users: authentication and profile data
- refresh_tokens: JWT refresh token storage
- messages: SMS messages with spam/ham labels
- predictions: model prediction results
- training_runs: history of model training runs
"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
        sa.Column("email", sa.String(), nullable=False, unique=True, index=True),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("is_superuser", sa.Boolean(), nullable=False, default=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False, default=False),
        sa.Column("full_name", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
        sa.Column("token_hash", sa.String(), nullable=False, unique=True, index=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("is_revoked", sa.Boolean(), nullable=False, default=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("label", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "predictions",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
        sa.Column("message_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("predicted_label", sa.String(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("probability_spam", sa.Float(), nullable=False),
        sa.Column("probability_ham", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("model_version", sa.String(), nullable=False, default="v1"),
        sa.Column("model_type", sa.String(), nullable=False, default="multinomial_naive_bayes"),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "training_runs",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
        sa.Column("version", sa.String(), nullable=False),
        sa.Column("accuracy", sa.Float(), nullable=False),
        sa.Column("precision_spam", sa.Float(), nullable=False),
        sa.Column("recall_spam", sa.Float(), nullable=False),
        sa.Column("f1_spam", sa.Float(), nullable=False),
        sa.Column("precision_ham", sa.Float(), nullable=True),
        sa.Column("recall_ham", sa.Float(), nullable=True),
        sa.Column("confusion_tn", sa.Integer(), nullable=False, default=0),
        sa.Column("confusion_fp", sa.Integer(), nullable=False, default=0),
        sa.Column("confusion_fn", sa.Integer(), nullable=False, default=0),
        sa.Column("confusion_tp", sa.Integer(), nullable=False, default=0),
        sa.Column("vectorizer_config", sa.Text(), nullable=False),
        sa.Column("classifier_config", sa.Text(), nullable=False),
        sa.Column("vectorizer_path", sa.String(), nullable=False),
        sa.Column("classifier_path", sa.String(), nullable=False),
        sa.Column("dataset_size", sa.Integer(), nullable=False),
        sa.Column("spam_count", sa.Integer(), nullable=False),
        sa.Column("ham_count", sa.Integer(), nullable=False),
        sa.Column("train_test_split", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Index("ix_training_runs_version", "version"),
    )


def downgrade() -> None:
    op.drop_table("training_runs")
    op.drop_table("predictions")
    op.drop_table("messages")
    op.drop_table("refresh_tokens")
    op.drop_table("users")