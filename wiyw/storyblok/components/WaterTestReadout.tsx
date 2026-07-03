// components/WaterTestReadout.tsx — the signature block.
// Renders a hardness gauge with a marker positioned on a 0–22 GPG scale.
import { storyblokEditable } from "@storyblok/react/rsc";

export default function WaterTestReadout({ blok }: { blok: any }) {
  const gpg: number = Number(blok.hardness_gpg ?? 18);
  // Clamp to [0,22] and convert to a percent position on the gauge.
  const pct = Math.max(0, Math.min(100, (Math.min(gpg, 22) / 22) * 100));
  return (
    <div {...storyblokEditable(blok)} className="readout"
         aria-label={`Water hardness ${gpg} grains per gallon`}>
      <div className="label">{blok.label}</div>
      <div className="big">{gpg}<span className="unit"> GPG</span></div>
      <div className="gauge">
        <div className="marker" style={{ left: `${pct}%` }} />
      </div>
      <div className="gauge-scale">
        <span>0 soft</span><span>7</span><span>15</span><span>22 very hard</span>
      </div>
      {blok.note && <div className="note">{blok.note}</div>}
    </div>
  );
}
