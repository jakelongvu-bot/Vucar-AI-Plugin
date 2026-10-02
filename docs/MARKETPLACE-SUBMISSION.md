# Marketplace submission checklist

The `2.0.0` owner/seller package is prepared for review. Backend rollout, live review execution, an accessible video walkthrough, submission, approval, and publication are pending.

- Repository: <https://github.com/jakelongvu-bot/Vucar-AI-Plugin>
- Public MCP endpoint: <https://api.vucar.vn/mcp>
- Authentication: none; no reviewer credentials belong in the ZIP.
- Market: used cars in Vietnam; initial availability `VN`.
- Category: `Data & Analytics`.
- Website: <https://vucar.vn/>
- Support: <https://vucar.vn/contact>
- Privacy: <https://vucar.vn/policy/chinh-sach-bao-mat-thong-tin>
- Terms: <https://vucar.vn/policy/quy-che-hoat-dong>

The listing, five positive cases, three negative cases, commerce declaration, and release notes are maintained in `.codex-plugin/plugin.json`. Cases cover valuation/comparison/source reports, offer net proceeds with unknown deductions, upgrade gaps with unknown costs, selling preparation, and catalog names/aliases. Negative cases cover foreign-market values, live/private records, and bookings or financial actions.

Run each case through a client connected to the deployed `2.0.0` service. Record the actual tool calls and observable result without personal data. A syntactically valid case is not an executed review result. Verify low/unknown confidence, unverified ranges, source attribution, and no invented fees or promotions.

Record a walkthrough using the same review cases and upload it to a reviewer-accessible location. `review.demo_recording_url` is intentionally omitted until a real URL exists. Its omission is allowed at upload but leaves required MCP review evidence incomplete. Do not use a placeholder, local path, or invented recording URL.

Build the OpenAI review ZIP with `scripts/build_review_zip.py`. It contains the Codex manifest, the upload-specific `mcpServers` wrapper, four skills, their shared boundary reference, legal/support documents, and square logo/icon assets. It excludes Claude metadata, scripts, private operations skills, credentials, and application references. The client marketplace retains its direct server map and separate Claude manifest.

Follow the current official [OpenAI submission instructions](https://developers.openai.com/plugins/deploy/submission). Upload, resolve automated findings, complete the missing review evidence, and submit only after the deployed service gate passes and the user authorizes submission. Upload or scan success is not approval or publication. Verify the resulting draft's six discovered tools and imported cases before claiming it is ready for review.
