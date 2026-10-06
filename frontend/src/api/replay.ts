import axios from "axios";
import type { ReplayRun, ReplayScenario } from "../types/replay";

export async function fetchReplayScenarios() {
  const { data } = await axios.get<ReplayScenario[]>("/api/replay/scenarios");
  return data;
}

export async function runReplayScenario(id: string) {
  const { data } = await axios.post<ReplayRun>(`/api/replay/scenarios/${encodeURIComponent(id)}/runs`);
  return data;
}
