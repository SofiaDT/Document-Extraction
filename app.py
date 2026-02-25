import json
from pathlib import Path

import streamlit as st

from src.config import get_openai_settings
from src.llm_extract import extract_key_values
from src.main import extract_document_text, format_markdown

SUPPORTED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}


def list_supported_files(directory: Path) -> list[Path]:
    return sorted(
        [
            path
            for path in directory.iterdir()
            if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
        ]
    )


def save_outputs(output_dir: Path, input_path: Path, result: dict, markdown: str) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"{input_path.name}.json"
    md_path = output_dir / f"{input_path.name}.md"
    json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(markdown, encoding="utf-8")
    return json_path, md_path


st.set_page_config(page_title="Document Extraction", layout="wide")

st.title("Document Extraction App")
st.write("Batch-extract documents with OCR + LLM and review JSON/Markdown outputs.")

if st.button("Reset"):
    for key in ["results", "errors", "last_directory"]:
        if key in st.session_state:
            del st.session_state[key]

st.header("Document Selection")

default_directory = st.session_state.get("last_directory", "data/input")
directory_input = st.text_input("Documents directory path", value=default_directory)
use_schema = st.checkbox(
    "Use schema (pay_stub, bank_statement, investment_statement)",
    value=True,
)

if directory_input:
    directory = Path(directory_input)
    st.session_state["last_directory"] = str(directory)

    if directory.is_dir():
        files = list_supported_files(directory)
        st.caption(f"Found {len(files)} supported file(s).")

        if files:
            for path in files[:10]:
                st.write(f"- {path.name}")

        if st.button("Begin Extraction"):
            try:
                api_key, model = get_openai_settings()
            except RuntimeError as exc:
                st.error(str(exc))
            else:
                st.session_state["results"] = []
                st.session_state["errors"] = []

                output_dir = Path("data/output")
                progress = st.progress(0.0)

                for index, path in enumerate(files, start=1):
                    try:
                        text = extract_document_text(path)
                        if not text:
                            raise RuntimeError("No text extracted from document.")

                        result = extract_key_values(
                            api_key,
                            model,
                            text,
                            enforce_schema=use_schema,
                        )
                        markdown = format_markdown(result)
                        json_path, md_path = save_outputs(output_dir, path, result, markdown)

                        st.session_state["results"].append(
                            {
                                "name": path.name,
                                "path": path,
                                "result": result,
                                "markdown": markdown,
                                "raw_text": text,
                                "json_path": json_path,
                                "md_path": md_path,
                            }
                        )
                    except Exception as exc:
                        st.session_state["errors"].append({"name": path.name, "error": str(exc)})

                    progress.progress(index / max(len(files), 1))

                st.success("Extraction complete.")
    else:
        st.warning("Directory not found.")

st.header("Results")

errors = st.session_state.get("errors", [])
if errors:
    st.subheader("Errors")
    for item in errors:
        st.write(f"- {item['name']}: {item['error']}")

results = st.session_state.get("results", [])
if not results:
    st.info("No results yet. Run extraction above.")
else:
    result_tabs = st.tabs([item["name"] for item in results])

    for tab, item in zip(result_tabs, results):
        with tab:
            st.subheader(item["name"])
            st.caption(f"Saved JSON: {item['json_path']}")
            st.caption(f"Saved Markdown: {item['md_path']}")

            # Two-column layout: Image on left, tabs on right
            col1, col2 = st.columns(2)
            
            with col1:
                if item["path"].suffix.lower() in {".jpg", ".jpeg", ".png"}:
                    st.image(str(item["path"]), caption="Original Document", use_container_width=True)
                else:
                    st.info("PDF preview not available")
            
            with col2:
                output_tabs = st.tabs(["Markdown", "JSON", "Raw OCR Output"])
                
                with output_tabs[0]:
                    st.markdown(item["markdown"])
                
                with output_tabs[1]:
                    st.json(item["result"])
                
                with output_tabs[2]:
                    # Display raw OCR output as a table with line numbers
                    lines = item["raw_text"].split('\n')
                    ocr_table = [{"Line": i+1, "Text": line} for i, line in enumerate(lines)]
                    st.dataframe(ocr_table, use_container_width=True, hide_index=True)
