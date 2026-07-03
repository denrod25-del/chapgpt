// components/Hero.tsx — hero block with standard/emergency variants.
import { storyblokEditable } from "@storyblok/react/rsc";
import WaterTestReadout from "./WaterTestReadout";

export function Hero({ blok }: { blok: any }) {
  const isEmergency = blok.variant === "emergency";
  const trust = (blok.trust_items ?? "").split(",").map((s: string) => s.trim()).filter(Boolean);
  return (
    <section {...storyblokEditable(blok)} className={`hero ${isEmergency ? "hero--emergency" : ""}`}>
      <div className="wrap">
        <div>
          {blok.eyebrow && <div className="eyebrow">{blok.eyebrow}</div>}
          <h1>{blok.heading}</h1>
          {blok.subheading && <p className="sub">{blok.subheading}</p>}
          <div className="cta-row">
            {isEmergency ? (
              <a className="btn-primary btn-emergency" href="tel:+15615550100">
                {blok.secondary_cta_label || "Call Now"}
              </a>
            ) : (
              <>
                <a className="btn-primary" href={blok.primary_cta_link?.url || "#contact"}>
                  {blok.primary_cta_label}
                </a>
                <a className="btn-ghost" href="tel:+15615550100">{blok.secondary_cta_label}</a>
              </>
            )}
          </div>
          {trust.length > 0 && (
            <div className="trust">{trust.map((t: string, i: number) => <span key={i}>{t}</span>)}</div>
          )}
        </div>
        {blok.show_hardness_gauge && !isEmergency && (
          <WaterTestReadout blok={{ hardness_gpg: 18,
            label: "Palm Beach County tap · typical hardness",
            note: "National guides assume 7–10 GPG. Biscayne Aquifer water runs 15–22 — nearly double." }} />
        )}
      </div>
    </section>
  );
}
export default Hero;
