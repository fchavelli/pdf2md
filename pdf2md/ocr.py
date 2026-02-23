"""Core OCR processing module using Mistral OCR API."""

from __future__ import annotations

import base64
import os
import re
from pathlib import Path
from typing import Optional

from mistralai import Mistral


def _get_client(api_key: Optional[str] = None) -> Mistral:
    """Instantiate and return a Mistral client."""
    key = api_key or os.getenv("MISTRAL_API_KEY")
    if not key:
        raise EnvironmentError(
            "MISTRAL_API_KEY is not set. "
            "Pass it explicitly or define it in your .env file."
        )
    return Mistral(api_key=key)


def process_pdf(
    pdf_path: str | Path,
    *,
    include_images: bool = False,
    output_path: Optional[str | Path] = None,
    api_key: Optional[str] = None,
) -> Path:
    """Convert a PDF file to Markdown via Mistral OCR.

    Parameters
    ----------
    pdf_path:
        Path to the source PDF file.
    include_images:
        If *True*, embedded images are saved alongside the Markdown file
        and referenced with standard ``![](...)`` tags.
        If *False* (default), image placeholders are stripped for a
        text-only output.
    output_path:
        Destination ``.md`` file.  When *None*, the output is written next
        to the source PDF with the same stem.
    api_key:
        Mistral API key override.  Falls back to the ``MISTRAL_API_KEY``
        environment variable.

    Returns
    -------
    Path
        Absolute path to the generated Markdown file.
    """
    pdf_path = Path(pdf_path).expanduser().resolve()
    if not pdf_path.is_file():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    if output_path is None:
        output_path = pdf_path.with_suffix(".md")
    else:
        output_path = Path(output_path).expanduser().resolve()

    client = _get_client(api_key)

    # Upload the PDF to Mistral
    with open(pdf_path, "rb") as fh:
        uploaded = client.files.upload(
            file={"file_name": pdf_path.name, "content": fh},
            purpose="ocr",
        )

    signed_url = client.files.get_signed_url(file_id=uploaded.id)

    # Run OCR
    ocr_response = client.ocr.process(
        model="mistral-ocr-latest",
        document={
            "type": "document_url",
            "document_url": signed_url.url,
        },
        include_image_base64=include_images,
    )

    # Gather Markdown content from all pages
    md_parts: list[str] = []
    images_dir: Optional[Path] = None

    if include_images:
        images_dir = output_path.parent / f"{output_path.stem}_images"
        images_dir.mkdir(parents=True, exist_ok=True)

    for page in ocr_response.pages:
        page_md = page.markdown

        if include_images and page.images:
            for img in page.images:
                if not img.image_base64:
                    continue
                # Determine image file name
                img_name = _sanitize_filename(img.id) + ".png"
                img_path = images_dir / img_name  # type: ignore[operator]
                # Decode and save
                _save_base64_image(img.image_base64, img_path)
                # Rewrite the reference in the markdown
                rel_path = os.path.relpath(img_path, output_path.parent)
                page_md = page_md.replace(
                    f"![{img.id}]({img.id})",
                    f"![{img.id}]({rel_path})",
                )
        elif not include_images:
            # Strip image tags
            page_md = _strip_images(page_md)

        md_parts.append(page_md)

    full_md = "\n\n---\n\n".join(md_parts)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(full_md, encoding="utf-8")

    # Cleanup: delete the uploaded file from Mistral
    try:
        client.files.delete(file_id=uploaded.id)
    except Exception:
        pass  # best-effort cleanup

    return output_path.resolve()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^)]+\)\s*", re.MULTILINE)


def _strip_images(md: str) -> str:
    """Remove Markdown image references."""
    return _IMAGE_RE.sub("", md)


def _sanitize_filename(name: str) -> str:
    """Produce a safe filename from an arbitrary string."""
    return re.sub(r"[^\w\-.]", "_", name)


def _save_base64_image(b64_data: str, dest: Path) -> None:
    """Decode a base64 string and write it as a binary file."""
    # Handle data-URI prefix if present
    if "," in b64_data[:80]:
        b64_data = b64_data.split(",", 1)[1]
    dest.write_bytes(base64.b64decode(b64_data))
