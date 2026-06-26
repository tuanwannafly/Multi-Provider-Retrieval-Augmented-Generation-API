"""Generate sample PDFs for the examples/ folder (ML course content).

Usage:
    python scripts/generate_sample_pdfs.py

Creates: examples/intro_to_ml.pdf, examples/deep_learning_basics.pdf,
         examples/nlp_fundamentals.pdf
"""
from __future__ import annotations

import os
from pathlib import Path

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "reportlab is required to generate sample PDFs. "
        "Install it with: pip install reportlab"
    ) from exc

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"

DOCUMENTS = {
    "intro_to_ml.pdf": [
        ("Introduction to Machine Learning", "h1"),
        ("What is Machine Learning?", "h2"),
        (
            "Machine learning is a subfield of artificial intelligence that enables "
            "systems to learn patterns from data. Instead of being explicitly "
            "programmed with rules, a machine learning model improves its performance "
            "on a task as it is exposed to more data.",
            "body",
        ),
        ("Supervised Learning", "h2"),
        (
            "Supervised learning uses labeled training data. Each example in the "
            "dataset pairs an input with a known target output. The model learns a "
            "mapping from inputs to outputs and can then predict outputs for unseen "
            "inputs. Classification and regression are the two main tasks.",
            "body",
        ),
        ("Unsupervised Learning", "h2"),
        (
            "Unsupervised learning finds structure in unlabeled data. Common "
            "techniques include clustering, which groups similar examples together, "
            "and dimensionality reduction, which compresses data while preserving "
            "important structure.",
            "body",
        ),
        ("The Bias-Variance Tradeoff", "h2"),
        (
            "The bias-variance tradeoff describes the tension between a model's "
            "ability to fit the training data and its ability to generalize. High "
            "bias leads to underfitting, while high variance leads to overfitting.",
            "body",
        ),
    ],
    "deep_learning_basics.pdf": [
        ("Deep Learning Fundamentals", "h1"),
        ("Neural Networks", "h2"),
        (
            "A neural network is composed of layers of interconnected nodes called "
            "neurons. Each connection has a weight that is adjusted during training. "
            "Deep learning refers to networks with many hidden layers that can learn "
            "hierarchical representations of data.",
            "body",
        ),
        ("Gradient Descent", "h2"),
        (
            "Gradient descent is a first-order optimization algorithm. It minimizes "
            "a loss function by iteratively moving in the direction of the steepest "
            "descent, which is the negative gradient. The learning rate controls the "
            "size of each step taken during optimization.",
            "body",
        ),
        ("Backpropagation", "h2"),
        (
            "Backpropagation computes the gradient of the loss with respect to each "
            "weight by applying the chain rule from the output layer back to the "
            "input layer. This enables efficient training of deep networks.",
            "body",
        ),
    ],
    "nlp_fundamentals.pdf": [
        ("Natural Language Processing Fundamentals", "h1"),
        ("What is NLP?", "h2"),
        (
            "Natural language processing (NLP) is a field of artificial intelligence "
            "focused on enabling computers to understand, interpret, and generate "
            "human language. It combines computational linguistics with machine "
            "learning and deep learning.",
            "body",
        ),
        ("Tokenization", "h2"),
        (
            "Tokenization is the process of splitting text into smaller units called "
            "tokens, which may be words, subwords, or characters. Tokenization is "
            "usually the first preprocessing step in any NLP pipeline.",
            "body",
        ),
        ("Embeddings", "h2"),
        (
            "Word and sentence embeddings map text into dense vectors in a "
            "continuous space, where semantic similarity corresponds to geometric "
            "proximity. Embeddings allow models to reason about meaning rather than "
            "raw characters.",
            "body",
        ),
    ],
}


def build_pdf(path: Path, blocks) -> None:
    doc = SimpleDocTemplate(str(path), pagesize=letter)
    styles = getSampleStyleSheet()
    style_map = {"h1": "Title", "h2": "Heading2", "body": "Normal"}
    flow = []
    for text, style in blocks:
        flow.append(Paragraph(text, styles[style_map[style]]))
        flow.append(Spacer(1, 12))
    doc.build(flow)


def main() -> None:
    EXAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    for filename, blocks in DOCUMENTS.items():
        path = EXAMPLES_DIR / filename
        build_pdf(path, blocks)
        print(f"Generated {path}")


if __name__ == "__main__":
    main()
