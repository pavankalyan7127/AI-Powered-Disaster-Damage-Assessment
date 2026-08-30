// Central Configuration for API URLs and Endpoints

export const API_BASE_URL = "http://127.0.0.1:8000";

export const MOCKAPI_CONFIG = {
  USERS: "https://6a93b8d325936d5660f0c368.mockapi.io/USERS",
  HISTORY: "https://6a93b8d325936d5660f0c368.mockapi.io/HISTORY",
  ADMIN: "https://6a93bad225936d5660f0c3fd.mockapi.io/ADMIN"
};

export const getImageUrl = (path) => {
  if (!path) return "https://via.placeholder.com/128?text=No+Image";
  if (path.startsWith("http")) return path;
  
  // Clean backslashes to forward slashes for URLs
  const cleanPath = path.replace(/\\/g, "/");
  return `${API_BASE_URL}/${cleanPath}`;
};
