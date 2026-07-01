-- Silent rejection: store the public, masked (technical) reason alongside the
-- private internal security reason. The applicant only ever sees masked_reason
-- (surfaced via pipeline_state.rejection_note); the real security reason stays
-- in internal_reason, visible to admins only.
ALTER TABLE admission_security_decisions
  ADD COLUMN masked_reason TEXT NULL AFTER internal_reason;
