import { useState } from "react";
import { Routes, Route } from "react-router-dom";
import { uploadImage, detectPlate, generateChallan } from "./api/challanApi";
import PayPage from "./pages/PayPage";

const VIOLATIONS = [
  { label: "Overspeeding",     value: "overspeed"        },
  { label: "Triple Riding",    value: "triple_ride"      },
  { label: "No Helmet",        value: "no_helmet"        },
  { label: "No Seatbelt",      value: "no_seatbelt"      },
  { label: "Signal Violation", value: "signal_violation" },
];

function MainApp() {
  const [image,     setImage]     = useState(null);
  const [preview,   setPreview]   = useState(null);
  const [filename,  setFilename]  = useState(null);
  const [plate,     setPlate]     = useState(null);
  const [challan,   setChallan]   = useState(null);
  const [violation, setViolation] = useState("overspeed");
  const [loading,   setLoading]   = useState(null);

  const handleFile = (file) => {
    setImage(file);
    setPreview(URL.createObjectURL(file));
    setFilename(null);
    setPlate(null);
    setChallan(null);
  };

  const handleUpload = async () => {
    setLoading("upload");
    try {
      const data = await uploadImage(image);
      setFilename(data.filename);
    } catch (e) {
      alert(e?.response?.data?.detail || "Upload failed");
    }
    setLoading(null);
  };

  const handleDetect = async () => {
    setLoading("detect");
    try {
      const data = await detectPlate(filename);
      setPlate(data.plate_number);
    } catch (e) {
      alert(e?.response?.data?.detail || "Detection failed");
    }
    setLoading(null);
  };

  const handleGenerate = async () => {
    setLoading("generate");
    try {
      const data = await generateChallan(plate, violation);
      setChallan(data);
    } catch (e) {
      alert(e?.response?.data?.detail || "Challan generation failed");
    }
    setLoading(null);
  };

  const handleWhatsApp = () => {
    if (!challan) return;
    const payUrl = `https://upon-overeater-robust.ngrok-free.dev/pay?plate=${encodeURIComponent(challan.plate_number)}&fine=${challan.fine}&mobile=${challan.mobile}`;
    const msg = [
      `🚔 *Traffic Police eChallan*`,
      ``,
      `Dear *${challan.owner_name}*,`,
      `A traffic violation has been recorded against your vehicle.`,
      ``,
      `• Plate  : *${challan.plate_number}*`,
      `• Offence: *${challan.violation.replace(/_/g, " ")}*`,
      `• Fine   : *₹${challan.fine}*`,
      ``,
      `👉 Pay here:`,
      `${payUrl}`,
      `— AI Traffic Challan System`,
    ].join("\n");
    window.open(`https://wa.me/91${challan.mobile}?text=${encodeURIComponent(msg)}`, "_blank");
  };

  return (
    <div className="page-shell">
      <h1 className="app-title">AI Traffic Challan System</h1>

      <div className="main-card">
        <div className="left-panel">
          <div className="preview-section">
            <p className="section-label">IMAGE PREVIEW</p>
            <div
              className={`preview-box${preview ? " has-image" : ""}`}
              onClick={() => document.getElementById("file-input").click()}
            >
              {preview ? (
                <img src={preview} alt="Vehicle" />
              ) : (
                <div className="preview-placeholder">
                  <span className="upload-icon">⬆</span>
                  <span>Click to select image</span>
                </div>
              )}
            </div>
            <input
              id="file-input"
              type="file"
              accept="image/jpeg,image/png,image/jpg"
              style={{ display: "none" }}
              onChange={(e) => e.target.files[0] && handleFile(e.target.files[0])}
            />
          </div>

          <div className="info-row">
            <div className="info-cell">
              <span className="info-label">PLATE</span>
              <span className="info-value">{plate || "—"}</span>
            </div>
            <div className="info-cell">
              <span className="info-label">FINE</span>
              <span className="info-value fine">{challan ? `₹${challan.fine}` : "₹—"}</span>
            </div>
          </div>
        </div>

        <div className="right-panel">
          <p className="section-label">CONTROLS</p>

          <button className="btn outline" disabled={!image || !!loading} onClick={handleUpload}>
            {loading === "upload" ? "Uploading…" : "Upload"}
          </button>

          <button className="btn outline" disabled={!filename || !!loading} onClick={handleDetect}>
            {loading === "detect" ? "Detecting…" : "Detect"}
          </button>

          <div className="select-wrapper">
            <select value={violation} onChange={(e) => setViolation(e.target.value)}>
              {VIOLATIONS.map(({ label, value }) => (
                <option key={value} value={value}>{label}</option>
              ))}
            </select>
            <span className="select-chevron">▾</span>
          </div>

          <button className="btn primary" disabled={!plate || !violation || !!loading} onClick={handleGenerate}>
            {loading === "generate" ? "Generating…" : "Generate"}
          </button>

          <button className="btn whatsapp" disabled={!challan || !!loading} onClick={handleWhatsApp}>
            WhatsApp
          </button>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<MainApp />} />
      <Route path="/pay" element={<PayPage />} />
    </Routes>
  );
}