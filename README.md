# ZapFormat · test preview

This repository publishes a **read-only frontend preview** from `KorRestConsult/ZapFormat` branch `dev` via GitHub Actions.

- It does not deploy to `zapformat.ru` or the backend.
- It does not import production credentials, databases, or server files.
- It intentionally blocks network API calls, so sign-in, search, supplier operations and real order submission do not work in this preview.
- Real fixes happen in the original `dev` branch; after testing they can be reviewed before merging into `main`.
- The preview URL is publicly accessible; never enter real customer details here.

Updates: automatic scheduled sync plus on-demand GitHub Actions `workflow_dispatch`. To stop, disable the workflow.
