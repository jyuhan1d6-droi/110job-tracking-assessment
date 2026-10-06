import axios from "axios";
import type { ArtifactList, CollectionRun, CollectionSource, RunList } from "../types/collection";

export async function fetchCollectionSources() {
  return (await axios.get<CollectionSource[]>("/api/collection/sources")).data;
}
export async function startCollection(sourceCode: string) {
  return (await axios.post<CollectionRun>(`/api/collection/sources/${encodeURIComponent(sourceCode)}/runs`)).data;
}
export async function fetchCollectionRuns(params: { page: number; source_code?: string; status?: string }) {
  return (await axios.get<RunList>("/api/collection/runs", { params: { ...params, mode: "live", page_size: 20 } })).data;
}
export async function fetchCollectionRun(id: string) {
  return (await axios.get<CollectionRun>(`/api/collection/runs/${id}`)).data;
}
export async function fetchRunArtifacts(id: string, page = 1) {
  return (await axios.get<ArtifactList>(`/api/collection/runs/${id}/artifacts`, { params: { page, page_size: 50 } })).data;
}
