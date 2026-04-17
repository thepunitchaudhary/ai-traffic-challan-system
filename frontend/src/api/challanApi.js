import axios from "axios";

const API = axios.create({
  baseURL: "http://localhost:8000",
  timeout: 30000,
});

export const uploadImage = async (file) => {
  const formData = new FormData();
  formData.append("file", file);
  const res = await API.post("/upload-image", formData);
  return res.data;
};

export const detectPlate = async (filename) => {
  const res = await API.post("/detect-plate", { filename });
  return res.data;
};

export const generateChallan = async (plateNumber, violation) => {
  const res = await API.post("/generate-challan", {
    plate_number: plateNumber,
    violation,
  });
  return res.data;
};

export const markPaid = async (plate) => {
  const res = await API.post("/mark-paid", { plate });
  return res.data;
};
