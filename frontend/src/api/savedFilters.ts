import axios from "axios";
import type { SavedFilter, SavedFilterInput } from "../types/savedFilters";

export async function fetchSavedFilters() {
  const { data } = await axios.get<SavedFilter[]>("/api/saved-filters");
  return data;
}

export async function createSavedFilter(payload: SavedFilterInput) {
  const { data } = await axios.post<SavedFilter>("/api/saved-filters", payload);
  return data;
}

export async function updateSavedFilter(id: string, payload: SavedFilterInput) {
  const { data } = await axios.put<SavedFilter>(`/api/saved-filters/${id}`, payload);
  return data;
}

export async function deleteSavedFilter(id: string) {
  await axios.delete(`/api/saved-filters/${id}`);
}
