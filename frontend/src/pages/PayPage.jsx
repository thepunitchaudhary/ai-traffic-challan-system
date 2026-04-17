import { useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { markPaid } from "../api/challanApi";

const METHODS = ["UPI", "Card", "Net Banking"];

export default function PayPage() {
  const [params]  = useSearchParams();
  const navigate  = useNavigate();
  const [method,  setMethod]  = useState(null);
  const [paid,    setPaid]    = useState(false);
  const [loading, setLoading] = useState(false);

  const plate  = params.get("plate")  || "—";
  const fine   = params.get("fine")   || "0";
  const mobile = params.get("mobile") || "";

  const handlePay = async () => {
    if (!method) { alert("Please select a payment method"); return; }
    setLoading(true);
    try { await markPaid(plate); } catch (_) {}
    await new Promise((r) => setTimeout(r, 700));
    setLoading(false);
    setPaid(true);
  };

  return (
    <div className="pay-shell">
      <div className="pay-card">
        {paid ? (
          <div className="pay-success">
            <div className="success-icon">✓</div>
            <h2>Payment Successful</h2>
            <p>Challan for <strong>{plate}</strong> has been cleared.</p>
            <button className="btn primary" style={{ marginTop: "1.5rem" }} onClick={() => navigate("/")}>
              ← Back to System
            </button>
          </div>
        ) : (
          <>
            <h1 className="pay-title">Pay Challan</h1>

            <div className="pay-details">
              <div className="pay-row">
                <span className="pay-label">Plate Number</span>
                <span className="pay-val mono">{plate}</span>
              </div>
              <div className="pay-row">
                <span className="pay-label">Mobile</span>
                <span className="pay-val mono">{mobile ? `+91 ${mobile}` : "—"}</span>
              </div>
              <div className="pay-row pay-fine-row">
                <span className="pay-label">Fine Amount</span>
                <span className="pay-val fine">₹{fine}</span>
              </div>
            </div>

            <p className="pay-method-label">Payment Method</p>
            <div className="pay-methods">
              {METHODS.map((m) => (
                <button
                  key={m}
                  className={`method-btn${method === m ? " selected" : ""}`}
                  onClick={() => setMethod(m)}
                >
                  {m}
                </button>
              ))}
            </div>

            <button className="btn primary pay-now" disabled={loading} onClick={handlePay}>
              {loading ? "Processing…" : `Pay ₹${fine} Now`}
            </button>
          </>
        )}
      </div>
    </div>
  );
}
