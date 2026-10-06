export type SavedFilter = {
  id: string;
  name: string;
  keyword: string | null;
  city: string | null;
  created_at: string;
  updated_at: string;
};

export type SavedFilterInput = {
  name: string;
  keyword?: string | null;
  city?: string | null;
};
