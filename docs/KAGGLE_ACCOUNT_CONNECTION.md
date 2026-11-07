# Prometheus Kaggle notebook connection (owner-controlled)

## What this connects

The **official Kaggle CLI 2.2.4** is the existing read/write notebook engine.
No Kaggle client or REST stack is being reinvented.

The repository includes `scripts/kaggle_bridge.py` and the manually invoked
GitHub Actions workflow **Prometheus Kaggle Owner-Approved Notebook Access**.

Supported operations:
- `verify`: confirm API authorization without publishing private notebook names
- `list`: check notebook listing without showing names on public runner logs
- `read`: authenticated pull of a requested notebook, compute a SHA256; contents
  remain solely in the ephemeral runner and are not made public
- `status`: query a requested notebook's status
- `write-draft`: save a **private** copy of only the approved Prometheus 27B
  notebook to `owner/plenum-prometheus-qwen-trial`, with `--no-run`

No delete operation, arbitrary source editor, GPU launch, private-to-public
export or self-modification operation is implemented. These would require
separate authorization and review. **Read/write code infrastructure is not
evidence that the user has authenticated or that this ChatGPT chat can
directly operate a Kaggle website.**

## To enable the connection securely

1. In Kaggle, open https://www.kaggle.com/settings/api and generate an
   **API token** for automation. Do not paste it into chat or any public file.
2. In GitHub, open repository Settings → Environments → create
   **`kaggle-access`**. Prefer required manual approval for that environment.
   Add **environment secret `KAGGLE_API_TOKEN`**, value = your Kaggle token.
   It must be an **environment secret**, not a workflow input. Only the
   owner can establish this authentication.
3. In GitHub Actions, open **Prometheus Kaggle Owner-Approved Notebook Access**
   → **Run workflow** → choose `verify`. Review success/failure.
4. To save the official trial notebook to Kaggle, choose `write-draft`,
   provide `owner/plenum-prometheus-qwen-trial`, and approve the protected
   environment gate. The command uses **`--no-run`** and never starts GPU
   inference. It creates or updates **that specific notebook only**.
5. To run the large model, visit Kaggle and explicitly approve the
   `APPROVE_FREE_GPU_RUN` notebook flag after checking disk, GPU and free
   quota. The workflow does **not** grant that approval.
6. Rotate/revoke the Kaggle token and delete the environment secret to
   disconnect. A public repo with write-capable collaborators carries
   heightened secret-exposure risk; use protected environments and do not
   commit unpublished Plenum data or private notebook exports.

If you prefer to avoid tokens and GitHub Secrets, ChatGPT Work Cloud Browser
can be used to navigate Kaggle under an owner-controlled browser sign-in,
where available. Work is a separate user-selected mode, not direct control
from the current chat.

## Limits of other free hosts

- **Kaggle GPU T4×2**: two 15 GiB GPUs actually verified by owner screenshots
  Nov 7, 2026; `/tmp` showed 966.9 GiB reported free and host RAM 30.1 GiB.
  Free quota and transient storage are not permanent. The 19.1 GB Qwen3.6-27B
  GGUF has **not** yet run.
- **Google Colab free**: use as alternate manual short-lived GPU environment if
  Kaggle quotas fail; GPU model and session duration are dynamic, not guaranteed.
- **Hugging Face ZeroGPU Spaces**: on-demand Gradio inference demos.
  Typical daily free-user compute quota is very short and not suitable as a
  long-running private general-purpose worker; may be valuable for a short
  interactive voice/vision/model demonstration when packaging is ready.

No pay-as-you-go service, Kaggle billing, model execution or third-party
account connection was activated by merging this documentation.
