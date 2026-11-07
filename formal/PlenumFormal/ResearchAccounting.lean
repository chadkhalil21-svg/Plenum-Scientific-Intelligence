/-!
Plenum Scientific Intelligence: formally checked elementary research accounting.

This demonstrates core Lean 4 kernel proof checking, not independent physical
discovery, general mathematics ability or a self-improving agent. No external
LLM-authored tactics or unknown source code is executed.
-/

namespace PlenumFormal

theorem accepted_count_le_total (accepted rejected : Nat) :
    accepted ≤ accepted + rejected := by
  exact Nat.le_add_right accepted rejected

theorem audit_total_order_independent (accepted rejected : Nat) :
    accepted + rejected = rejected + accepted := by
  exact Nat.add_comm accepted rejected

theorem accepted_count_monotone_under_new_tests
    (accepted rejected additional : Nat) :
    accepted ≤ (accepted + rejected) + additional := by
  calc
    accepted ≤ accepted + rejected := Nat.le_add_right accepted rejected
    _ ≤ (accepted + rejected) + additional :=
      Nat.le_add_right (accepted + rejected) additional

end PlenumFormal
