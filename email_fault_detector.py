"""Simple ML-based email fault detector.

Interprets "fault" emails as suspicious messages (spam/phishing).
The model is trained on a small in-code dataset for demonstration purposes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report


@dataclass
class EmailExample:
    text: str
    is_fault: int  # 1 = suspicious/fault, 0 = normal


TRAINING_DATA: List[EmailExample] = [
    EmailExample("Urgent: verify your bank password now to avoid suspension", 1),
    EmailExample("You won a free iPhone, click this link immediately", 1),
    EmailExample("Final notice: invoice overdue, pay with gift cards", 1),
    EmailExample("Security alert: unusual sign in, confirm account details", 1),
    EmailExample("Limited-time crypto investment guaranteed 200% return", 1),
    EmailExample("Account locked: provide OTP to restore access", 1),
    EmailExample("Congratulations, claim your tax refund by sharing SSN", 1),
    EmailExample("Your mailbox is full, login here to keep messages", 1),
    EmailExample("Immediate action required: update payroll banking info", 1),
    EmailExample("Wire transfer needed today, keep this confidential", 1),
    EmailExample("Can we move tomorrow's project sync to 3 PM?", 0),
    EmailExample("Please review the attached quarterly report", 0),
    EmailExample("Team lunch this Friday at noon", 0),
    EmailExample("Reminder to submit your timesheet today", 0),
    EmailExample("Happy birthday! Wishing you a great year ahead", 0),
    EmailExample("Here are the meeting notes from today's client call", 0),
    EmailExample("The deployment completed successfully last night", 0),
    EmailExample("Please approve the PTO request in HR portal", 0),
    EmailExample("Invoice #1032 has been paid, thank you", 0),
    EmailExample("Weekly status update: all milestones are on track", 0),
]


def build_model() -> Pipeline:
    """Build and return a text-classification pipeline."""
    return Pipeline(
        [
            ("tfidf", TfidfVectorizer(stop_words="english", ngram_range=(1, 2))),
            ("clf", LogisticRegression(max_iter=1000)),
        ]
    )


def train_model(data: Iterable[EmailExample]) -> Pipeline:
    examples = list(data)
    texts = [x.text for x in examples]
    labels = [x.is_fault for x in examples]

    x_train, x_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.3, random_state=42, stratify=labels
    )

    model = build_model()
    model.fit(x_train, y_train)

    preds = model.predict(x_test)
    print("Validation report:\n")
    print(classification_report(y_test, preds, target_names=["normal", "fault"], zero_division=0))

    return model


def predict_email(model: Pipeline, email_text: str) -> str:
    label = model.predict([email_text])[0]
    return "fault" if label == 1 else "normal"


if __name__ == "__main__":
    model = train_model(TRAINING_DATA)

    sample_email = "Action required: reset your payroll account password using this link"
    prediction = predict_email(model, sample_email)

    print(f"Email: {sample_email}")
    print(f"Prediction: {prediction}")
