import os
import zipfile
from io import BytesIO

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Packshot Renamer",
    layout="wide"
)


st.markdown("""
<style>
.stApp {
    background-color: #fef3b3;
}

.block-container {
    padding-top: 1.5rem;
    padding-left: 3rem;
    padding-right: 3rem;
    max-width: 1100px;
}

.logo {
    margin-bottom: 40px;
}

.title {
    text-align: center;
    font-size: 46px;
    font-weight: 900;
    color: #1f1f1f;
    margin-bottom: 10px;
}

.subtitle {
    text-align: center;
    font-size: 20px;
    color: #444444;
    margin-bottom: 45px;
}

.section {
    background-color: transparent;
    padding: 0;
    margin-bottom: 30px;
}

.upload-title {
    font-size: 20px;
    font-weight: 800;
    color: black;
    margin-bottom: 6px;
}

.upload-text {
    font-size: 15px;
    color: #444444;
    margin-bottom: 12px;
}

.divider {
    height: 1px;
    background-color: rgba(0,0,0,0.18);
    margin: 30px 0;
}

/* remove white uploader areas */
[data-testid="stFileUploader"] {
    background: transparent !important;
}

[data-testid="stFileUploader"] section {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
}

[data-testid="stFileUploaderDropzone"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
}

[data-testid="stFileUploaderDropzoneInstructions"] {
    display: none !important;
}

[data-testid="stFileUploaderDropzone"] button {
    background-color: black !important;
    color: white !important;
    border-radius: 12px !important;
    border: none !important;
    padding: 10px 24px !important;
    font-weight: 700 !important;
}

.stButton>button {
    background-color: black;
    color: white;
    border-radius: 14px;
    border: none;
    padding: 14px 35px;
    font-size: 18px;
    font-weight: 800;
    width: 100%;
}

.stDownloadButton>button {
    background-color: black;
    color: white;
    border-radius: 14px;
    border: none;
    padding: 14px 35px;
    font-size: 18px;
    font-weight: 800;
    width: 100%;
}

.footer {
    text-align: center;
    margin-top: 40px;
    color: black;
    font-size: 14px;
}
            
img {
    overflow: visible !important;
}            
</style>
""", unsafe_allow_html=True)


st.markdown('<div class="logo">', unsafe_allow_html=True)

from PIL import Image

logo = Image.open("logo.png")

st.image(
    logo,
    width=300,
    output_format="PNG"
)

st.markdown('</div>', unsafe_allow_html=True)


st.markdown('<div class="title">Packshot Renamer</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Upload your files and download renamed packshots.</div>',
    unsafe_allow_html=True
)


st.markdown('<div class="section">', unsafe_allow_html=True)

st.markdown('<div class="upload-title">1. Upload Product Excel File</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="upload-text">The Excel file should include item_number, item_name and sales_list_price.</div>',
    unsafe_allow_html=True
)

excel_file = st.file_uploader(
    "Upload Product Excel File",
    type=["xlsx"],
    label_visibility="collapsed"
)

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

st.markdown('<div class="upload-title">2. Upload Packshot Folder</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="upload-text">Upload the folder containing your packshot images.</div>',
    unsafe_allow_html=True
)

packshot_files = st.file_uploader(
    "Upload Packshot Folder",
    type=["jpg", "jpeg", "png", "webp"],
    accept_multiple_files="directory",
    label_visibility="collapsed"
)

st.markdown('</div>', unsafe_allow_html=True)


def build_lookup(df):
    required_cols = ["item_number", "item_name", "sales_list_price"]

    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in Excel: {missing}")

    df["item_number"] = df["item_number"].astype(str).str.strip()
    df["item_name"] = df["item_name"].astype(str).str.strip()

    lookup = {}

    for _, row in df.iterrows():
        key = (
            row["item_number"].lower(),
            row["item_name"].lower()
        )
        lookup[key] = row["sales_list_price"]

    return lookup


def rename_packshots(files, lookup):
    renamed_files = []
    skipped_files = []
    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for uploaded_file in files:
            filename = uploaded_file.name

            if "01_packshot" not in filename:
                skipped_files.append({
                    "File": filename,
                    "Reason": "Not a packshot image"
                })
                continue

            base_name = os.path.basename(filename)
            name, ext = os.path.splitext(base_name)
            parts = name.split("_")

            if len(parts) < 3:
                skipped_files.append({
                    "File": filename,
                    "Reason": "Filename format not recognised"
                })
                continue

            item_number = parts[0].strip()
            item_name = parts[2].strip()

            key = (
                item_number.lower(),
                item_name.lower()
            )

            if key not in lookup:
                skipped_files.append({
                    "File": filename,
                    "Reason": "No matching product found"
                })
                continue

            price = lookup[key]
            price = f"{float(price):.2f}".replace(".", ",")

            new_filename = f"{name}_{price} EUR{ext}"
            folder_path = os.path.dirname(filename)
            output_path = os.path.join("RENAMED", folder_path, new_filename)

            zip_file.writestr(output_path, uploaded_file.getvalue())

            renamed_files.append({
                "Original File": filename,
                "New File": new_filename
            })

    zip_buffer.seek(0)
    return zip_buffer, renamed_files, skipped_files


if st.button("✨ Rename Packshots"):
    if not excel_file or not packshot_files:
        st.warning("Please upload both the Excel file and the packshot folder first.")
    else:
        try:
            df = pd.read_excel(excel_file)
            lookup = build_lookup(df)

            zip_buffer, renamed_files, skipped_files = rename_packshots(
                packshot_files,
                lookup
            )

            st.success(f"Done. {len(renamed_files)} files were renamed.")

            st.download_button(
                label="⬇️ Download Renamed Packshots",
                data=zip_buffer,
                file_name="renamed_packshots.zip",
                mime="application/zip"
            )

            if skipped_files:
                with st.expander("Show skipped files"):
                    st.dataframe(pd.DataFrame(skipped_files), use_container_width=True)

        except Exception as e:
            st.error(f"Something went wrong: {e}")


st.markdown('<div class="footer">© Fabienne Chapot</div>', unsafe_allow_html=True)