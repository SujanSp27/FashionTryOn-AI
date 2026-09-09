import json
from pathlib import Path

nb_path = Path("Flow_Style_VTON_Colab_Inference.ipynb")
with open(nb_path, "r", encoding="utf-8") as f:
    nb = json.load(f)

runner_code = Path("Flow-Style-VTON-main/test/run_colab_quality_verification.py").read_text(encoding="utf-8")

md_cell = {
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "---\n",
        "# Quality Verification & Robust Preprocessing Suite (Prompt Quality)\n",
        "Directly verifies and executes the quality test matrix in the current Colab runtime:\n",
        "- Inspects `tryon_engine.py`, `tryon_single.py`, `garment_preprocessor.py`\n",
        "- Creates `test/VTO_QUALITY_DIAGNOSIS.md`\n",
        "- Runs `test/compare_preprocessing.py`\n",
        "- Prepares `test/setup_quality_fixtures.py`\n",
        "- Executes `test/tryon_quality_test.py` across Tests A through E\n",
        "- Saves `quality_results/`, `master_quality_matrix_summary.jpg`, and comparison strips"
    ]
}

code_cell = {
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        runner_code + "\n\n" +
        "# Display Master Summary Strip in Colab\n" +
        "import matplotlib.pyplot as plt\n" +
        "from PIL import Image\n" +
        "sum_path = TEST_DIR / 'master_quality_matrix_summary.jpg'\n" +
        "if sum_path.exists():\n" +
        "    plt.figure(figsize=(12, 16))\n" +
        "    plt.imshow(Image.open(sum_path))\n" +
        "    plt.axis('off')\n" +
        "    plt.title('Flow-Style-VTON Quality Test Matrix (Tests A - E)', fontsize=14, fontweight='bold')\n" +
        "    plt.show()\n"
    ]
}

nb["cells"].append(md_cell)
nb["cells"].append(code_cell)

with open(nb_path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1)

print("[+] Added Quality Verification cells to Flow_Style_VTON_Colab_Inference.ipynb")
