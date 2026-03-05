import type { RunEvalRequest, ConversationTurn, EvalResult } from "./types";

export interface SSECallbacks {
  onStart: (evalId: string) => void;
  onTurn: (turn: ConversationTurn) => void;
  onJudging: () => void;
  onResult: (result: EvalResult) => void;
  onError: (error: string) => void;
  onDone: () => void;
}

export async function startEvaluation(
  request: RunEvalRequest,
  callbacks: SSECallbacks,
): Promise<void> {
  const response = await fetch("/api/eval/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    callbacks.onError(`Server returned ${response.status}: ${response.statusText}`);
    return;
  }

  const reader = response.body?.getReader();
  if (!reader) {
    callbacks.onError("No response stream available");
    return;
  }

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    let currentEvent = "";

    for (const line of lines) {
      if (line.startsWith("event:")) {
        currentEvent = line.slice(6).trim();
      } else if (line.startsWith("data:")) {
        const data = line.slice(5).trim();
        if (!data) continue;

        try {
          const parsed = JSON.parse(data);
          switch (currentEvent) {
            case "start":
              callbacks.onStart(parsed.eval_id);
              break;
            case "turn":
              callbacks.onTurn({
                turn_number: parsed.turn_number,
                speaker: parsed.speaker,
                message: parsed.message,
                latency_ms: parsed.latency_ms,
              });
              break;
            case "judging":
              callbacks.onJudging();
              break;
            case "result":
              callbacks.onResult(parsed.result);
              break;
            case "error":
              callbacks.onError(parsed.error || "Unknown error");
              break;
            case "done":
              callbacks.onDone();
              break;
          }
        } catch {
          // skip malformed JSON
        }
        currentEvent = "";
      }
    }
  }

  callbacks.onDone();
}
