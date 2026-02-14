# Semantic Search Demo

This repo includes a minimal semantic search example using ChromaDB and
sentence-transformers.

It now also includes a small ML text-classification example for detecting
whether an email is likely **faulty/suspicious** (spam or phishing-like).

## Requirements

Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the semantic search example:

```bash
python semantic_search.py
```

Run the Flask UI:

```bash
python app.py
```

Run the email fault detector ML example:

```bash
python email_fault_detector.py
```
