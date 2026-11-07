# Publication Verification Form

Each Google Form asks for the respondent's name, followed by three questions per publication:

1. **Usage:** Yes / No / Unsure
2. **Equipment:** Select machines and/or Other (not listed)
3. **Criticality:** Critical / Significant / Minor

## Sync Rules

| Response | Publication Status | Resource Attribution |
|---|---|---|
| No | `REJECTED` | None |
| Unsure | `UNSURE` | None |
| Yes + Machines | `CONFIRMED` | Create relations with the selected criticality |
| Yes + Other only | `NEEDS_REVIEW` | No relations |
| Yes + Machines + Other | `CONFIRMED` | Create relations for listed machines only |

- For **Yes**, both equipment and criticality are required. Missing answers make the submission invalid.
- For **No / Unsure**, equipment and criticality must be left blank.
- All selected machines receive the same criticality.
- **Other** is a fixed checkbox without free-text input. Its selection is saved in `FormQuestion.other_resource_text`, but no resource relation is created for it.
- The respondent's name remains in Google Forms only and is ignored during sync.
- Invalid submissions do not update publications or create attributions.

## Attribution Data

Confirmed machine usage is stored in `PublicationResource` with `publication_id`, `resource_id`, and `criticality`.

View confirmed equipment and criticality with:

`GET /publications/{id}/attributions`