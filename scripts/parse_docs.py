from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
from pathlib import Path

sources = [
    Path("data/raw/frameworks/nist_ai_rmf_001.pdf"),
    Path("data/raw/frameworks/nist_genai_profile_001.pdf"),
    Path("data/raw/regulations/eu_ai_act_001.pdf"),
    Path("data/raw/security_guidance/ncsc_secure_ai_001.pdf")
]

output_dir = Path("data/processed")
output_dir.mkdir(parents=True, exist_ok=True)

pdf_options = PdfPipelineOptions()
pdf_options.do_ocr = False
pdf_options.do_table_structure = False

converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(
            pipeline_options=pdf_options,
            backend=PyPdfiumDocumentBackend,
        )
    }
)

for source in sources:
    result = converter.convert(source)
    doc = result.document

    file_output_dir = output_dir / source.stem
    file_output_dir.mkdir(parents=True, exist_ok=True)

    markdown = doc.export_to_markdown()
    (file_output_dir / "parsed.md").write_text(markdown, encoding="utf-8")

    try:
        text = doc.export_to_text()
    except AttributeError:
        text = markdown

    (file_output_dir / "parsed.txt").write_text(text, encoding="utf-8")

    print(f"Done: {source.name}")