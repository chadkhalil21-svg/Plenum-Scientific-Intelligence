# Weekly Laboratory Operations Checklist — Public Template

**Document ID:** PLENUM-LAB-WK-001 | **Version:** 1.0 | **Status:** Review-only operational template | **Cadence:** Weekly
**Scope:** Non-hazardous laboratory administration, recordkeeping, traceability, and escalation. Adapt to the facility's approved procedures before use. **Not a regulatory certification, calibration certificate, GLP compliance determination, or substitute for a site-specific SOP.**

## Weekly record header
- Week starting (ISO date): ______ | Facility / laboratory: ______ | Responsible coordinator: ______
- Applicable site SOP revision(s): ______ | Work order / logbook reference: ______
- Independent reviewer: ______ | Review date/time (timezone): ______
- Evidence location (controlled document store, not public GitHub): ______

**For every check:** record **PASS / HOLD / N/A**, responsible person's initials, completion date/time and timezone, evidence identifier/location, exception or deviation ID, and corrective owner + due date when HOLD. N/A requires a written justification. A HOLD affecting traceability, calibration validity, safety, sample integrity or data integrity must be escalated to the designated lab supervisor **before** affected work resumes; do not silently mark complete.

| Day / owner role | Check / action | Evidence or entry required | Acceptance criterion / escalation |
| --- | --- | --- | --- |
| Monday — Lab coordinator | Confirm current controlled SOPs, approved method versions, training/authorization roster and prior week's open actions | SOP revision list, training matrix ID, open-action register | PASS if versions/authorization current; otherwise HOLD, identify affected work and supervisor |
| Monday — Equipment custodian | Review instrument availability, preventive maintenance, calibration status, due dates and out-of-service labels | Instrument ID, calibration certificate/log ID, next due date, service status | PASS only for instruments within applicable approval/status; HOLD expired/unknown instruments and segregate from use |
| Tuesday — Sample custodian | Reconcile received, in-process, stored, transferred and disposed samples against chain-of-custody | Sample IDs, receipt/transfers, location, condition, disposition records | PASS if every movement attributable; HOLD unidentified, missing or compromised samples |
| Tuesday — Inventory steward | Reconcile consumables, reference materials, lot/expiry, storage conditions and reorder needs | Item/lot, quantity, expiry, location, condition log, reorder request | PASS if fit-for-use and traceable; HOLD expired/unidentified items; do not prescribe hazardous handling |
| Wednesday — Data steward | Check instrument/data acquisition records, timestamp/time-zone conventions, immutable raw-file identifiers and backups | Data-set/run IDs, storage URI, backup job ID, restore-test record/date per site SOP | PASS if original data retained, access controlled and backup evidence exists; HOLD missing/altered data or failed backup |
| Wednesday — Quality lead | Review blanks/controls/standards and method quality-control exceptions where required by approved SOP | Batch/run ID, QC reference, method acceptance limits, deviation ID | PASS only against **site-approved** method criteria; HOLD out-of-limit results and quarantine affected conclusions |
| Thursday — Lab coordinator | Review environmental/storage monitoring and facility housekeeping records within approved local requirements | Monitoring log IDs, alarm/deviation IDs, work-order references | PASS if records and actions complete; HOLD excursions or unreviewed alarms |
| Thursday — Quality lead | Reconcile deviations, nonconformances, corrective/preventive actions and prior HOLD items | Deviation ID, impact assessment, action owner, due date, evidence of disposition | PASS only when actions verified or formally tracked with approved containment; HOLD uncontained issues |
| Friday — Independent reviewer | Cross-check a sample of instrument, sample and data records against original evidence; verify outstanding HOLD/N/A rationales | Reviewed record IDs, exceptions, reviewer signature/date, escalation record | PASS when review is independent and exceptions tracked; HOLD unresolved critical gaps |
| Friday — Lab supervisor | Approve weekly disposition and next-week priorities; confirm no HOLD was silently overridden | Signed weekly summary, carried-forward actions, restricted-work list | PASS only after documented review; unresolved HOLD stays open and affected work remains restricted |

## Per-check entry form (repeat for each row)
- Week / check identifier: ______
- Date/time with timezone: ______ | Owner and role: ______
- Status: [ ] PASS  [ ] HOLD  [ ] N/A
- Evidence record ID / controlled storage location: ______
- Observations, units and applicable SOP acceptance criterion: ______
- N/A reason (if selected): ______
- Deviation / incident / corrective-action reference: ______
- Containment or restricted-work decision: ______
- Corrective action owner: ______ | Due date: ______
- Follow-up verification (who / when / evidence): ______
- Independent reviewer signature or approved electronic equivalent: ______

## Weekly closeout and handoff
1. Count PASS, HOLD and N/A checks; verify every N/A justification and every HOLD's containment, named owner and due date.
2. Carry unresolved items into the existing action register **without replacing original IDs**; identify affected equipment, samples, runs and deliverables.
3. Preserve raw records and review trail under existing retention, access-control and backup policies; never put private sample/personnel information in a public issue.
4. Independent reviewer checks traceability and signatures; supervisor approves weekly status or documents why approval is withheld.
5. Next week's coordinator acknowledges the open-item handoff, with timestamp and reference to this week's record.

## Provenance and limits
This is an **original administrative checklist** informed by the U.S. National Institute of Standards and Technology, Office of Weights and Measures, *Good Laboratory Practices* and *Standard Operating Procedures* resources:
- https://www.nist.gov/pml/owm/laboratory-metrology/documentary-standards-and-resources/glps
- https://www.nist.gov/pml/owm/laboratory-metrology/documentary-standards-and-resources/sops

These NIST resources provide documentary examples for laboratory metrology; this template is not represented as NIST-authored, NIST-endorsed, or universally applicable to every scientific laboratory. Facility management must approve local acceptance limits, hazards, instrument methods, record retention, electronic signatures and legal obligations. No external compliance claim follows from checking boxes.
