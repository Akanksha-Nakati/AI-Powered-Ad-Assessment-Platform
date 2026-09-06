import axios from "axios";
import { AssessmentResponse } from "./types";

const client = axios.create({
  baseURL: "http://localhost:8000",
});

export async function assessAd(form: FormData): Promise<AssessmentResponse> {
  const { data } = await client.post<AssessmentResponse>("/assess", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

