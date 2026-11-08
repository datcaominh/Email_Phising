export type PermissionDecision = {
  allowed: boolean;
  reason: string;
};

// Permission gate gia lap cho kien truc multi-agent.
// MVP chi cho phep tac nhan doc email upload, goi ML local va goi LLM provider da cau hinh.
export function permissionGate(action: string): PermissionDecision {
  const allowedActions = new Set([
    "parse_email",
    "run_ml_prediction",
    "call_llm_agent",
    "format_alert",
    "chat_about_email"
  ]);

  if (allowedActions.has(action)) {
    return { allowed: true, reason: "Action nam trong pipeline duoc phep." };
  }

  return { allowed: false, reason: "Action khong nam trong pham vi MVP." };
}
