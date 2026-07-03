// components/ContactForm.tsx — posts to the WiYW backend /leads endpoint.
// NOTE: no HTML <form> submit; controlled state + fetch, per conversion plan.
"use client";
import { useState } from "react";
import { storyblokEditable } from "@storyblok/react";

const API = process.env.NEXT_PUBLIC_API_BASE ?? "";

export default function ContactForm({ blok }: { blok: any }) {
  const services = (blok.service_options ?? "water_softener\nwell water treatment\nwater_heater\ndrain\nemergency")
    .split("\n").map((s: string) => s.trim()).filter(Boolean);
  const [state, setState] = useState({ full_name: "", phone: "", email: "", service_type: services[0] });
  const [status, setStatus] = useState<"idle" | "sending" | "done" | "error">("idle");

  async function submit() {
    // Boundary check mirrors backend E.164 rule; better UX than a 422 round-trip.
    if (!state.full_name.trim() || !/^\+?[1-9]\d{7,14}$/.test(state.phone.replace(/[^\d+]/g, ""))) {
      setStatus("error"); return;
    }
    setStatus("sending");
    try {
      const phone = state.phone.startsWith("+") ? state.phone : `+1${state.phone.replace(/\D/g, "")}`;
      const res = await fetch(`${API}/leads`, {
        method: "POST", headers: { "content-type": "application/json" },
        body: JSON.stringify({
          ...state, phone,
          urgency: blok.urgency_default === "emergency" ? "emergency" : "standard",
          source: "website",
          landing_page: typeof window !== "undefined" ? window.location.pathname : "/",
        }),
      });
      setStatus(res.ok ? "done" : "error");
    } catch {
      setStatus("error");
    }
  }

  if (status === "done") {
    return (
      <div {...storyblokEditable(blok)} className="contact-done">
        <h2>Got it — we'll call you shortly.</h2>
        <p>Need us now? Call <a href="tel:+15615550100">(561) 555-0100</a>.</p>
      </div>
    );
  }

  return (
    <div {...storyblokEditable(blok)} className="contact" id="contact">
      <h2>{blok.heading || "Get a free water test"}</h2>
      <div className="fields">
        <input placeholder="Your name" value={state.full_name}
               onChange={(e) => setState({ ...state, full_name: e.target.value })} />
        <input placeholder="Phone" inputMode="tel" value={state.phone}
               onChange={(e) => setState({ ...state, phone: e.target.value })} />
        <input placeholder="Email (optional)" value={state.email}
               onChange={(e) => setState({ ...state, email: e.target.value })} />
        <select value={state.service_type}
                onChange={(e) => setState({ ...state, service_type: e.target.value })}>
          {services.map((s: string) => <option key={s} value={s}>{s.replace(/_/g, " ")}</option>)}
        </select>
      </div>
      {status === "error" && <p className="err">Please enter your name and a valid phone number.</p>}
      <button className="btn-primary" onClick={submit} disabled={status === "sending"}>
        {status === "sending" ? "Sending…" : "Request my free test"}
      </button>
    </div>
  );
}
