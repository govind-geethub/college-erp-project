"""
Packages the exact two submission deliverables into submission.zip as specified in the brief:
1. Technical Design Document (Technical_Design_Document.docx)
2. deployment.md
"""

import os
import zipfile

def package_submission():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    zip_path = os.path.join(base_dir, "submission.zip")
    tdd_path = os.path.join(base_dir, "Technical_Design_Document.docx")
    deploy_path = os.path.join(base_dir, "deployment.md")

    if not os.path.exists(tdd_path):
        print("TDD docx not found, generating...")
        from generate_docx_tdd import build_docx_from_markdown
        build_docx_from_markdown(os.path.join(base_dir, "docs", "TDD.md"), tdd_path)

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.write(tdd_path, arcname="Technical_Design_Document.docx")
        z.write(deploy_path, arcname="deployment.md")

    size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    print(f"==================================================")
    print(f" Successfully created submission package:")
    print(f" Archive: {zip_path}")
    print(f" Size: {size_mb:.2f} MB (Limit: 25 MB)")
    print(f" Files included:")
    print(f"   1. Technical_Design_Document.docx")
    print(f"   2. deployment.md")
    print(f"==================================================")


if __name__ == "__main__":
    package_submission()
