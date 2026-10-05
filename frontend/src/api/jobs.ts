import axios from "axios";
import type { JobDetail, JobListResponse, JobSummary } from "../types/jobs";

export async function fetchJobs(params: { keyword: string; city: string; page: number }) {
  const { data } = await axios.get<JobListResponse>("/api/jobs", { params: { ...params, page_size: 20 } });
  return data;
}

export async function fetchCities() {
  const { data } = await axios.get<string[]>("/api/jobs/cities");
  return data;
}

export async function fetchJobSummary() {
  const { data } = await axios.get<JobSummary>("/api/jobs/summary");
  return data;
}

export async function fetchJob(id: string) {
  const { data } = await axios.get<JobDetail>(`/api/jobs/${id}`);
  return data;
}
