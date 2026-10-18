from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)

    full_name = Column(String, nullable=True)

    created_at = Column(DateTime, nullable=False)

    # Relationships
    refresh_tokens = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )
    predictions = relationship("Prediction", back_populates="user", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="user", cascade="all, delete-orphan")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token_hash = Column(String, nullable=False, unique=True, index=True)
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, nullable=False)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="refresh_tokens")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    label = Column(String, nullable=False)  # "spam" or "ham"
    created_at = Column(DateTime, nullable=False)

    # For tracking which model made the prediction
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user = relationship("User", back_populates="messages")
    predictions = relationship("Prediction", back_populates="message", cascade="all, delete-orphan")


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    message = relationship("Message", back_populates="predictions")

    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user = relationship("User", back_populates="predictions")

    # Model output
    predicted_label = Column(String, nullable=False)  # "spam" or "ham"
    confidence = Column(Float, nullable=False)  # probability score
    probability_spam = Column(Float, nullable=False)  # P(spam | text)
    probability_ham = Column(Float, nullable=False)  # P(ham | text)

    # Metadata
    created_at = Column(DateTime, nullable=False, default=func.now())

    # Model version info
    model_version = Column(String, nullable=False, default="v1")
    model_type = Column(String, nullable=False, default="multinomial_naive_bayes")


class TrainingRun(Base):
    __tablename__ = "training_runs"

    id = Column(Integer, primary_key=True, index=True)
    version = Column(String, nullable=False)  # e.g. "v1", "v2"

    # Metrics
    accuracy = Column(Float, nullable=False)
    precision_spam = Column(Float, nullable=False)
    recall_spam = Column(Float, nullable=False)
    f1_spam = Column(Float, nullable=False)
    precision_ham = Column(Float, nullable=True)
    recall_ham = Column(Float, nullable=True)

    # Confusion matrix: [[TN, FP], [FN, TP]]
    confusion_tn = Column(Integer, nullable=False, default=0)
    confusion_fp = Column(Integer, nullable=False, default=0)
    confusion_fn = Column(Integer, nullable=False, default=0)
    confusion_tp = Column(Integer, nullable=False, default=0)

    # Configuration
    vectorizer_config = Column(Text, nullable=False)  # JSON string
    classifier_config = Column(Text, nullable=False)  # JSON string

    # Artifact paths (relative to project root)
    vectorizer_path = Column(String, nullable=False)
    classifier_path = Column(String, nullable=False)

    # Dataset info
    dataset_size = Column(Integer, nullable=False)
    spam_count = Column(Integer, nullable=False)
    ham_count = Column(Integer, nullable=False)
    train_test_split = Column(Float, nullable=False)  # e.g. 0.2

    created_at = Column(DateTime, nullable=False)

    # Indexes
    __table_args__ = (Index("ix_training_runs_version", "version"),)
