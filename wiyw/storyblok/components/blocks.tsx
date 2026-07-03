// components/blocks.tsx — remaining presentational blocks.
// Split into individual files in production; grouped here for delivery brevity.
import { storyblokEditable, StoryblokServerComponent } from "@storyblok/react/rsc";
import { render } from "storyblok-rich-text-react-renderer";

const lines = (s?: string) => (s ?? "").split("\n").map((x) => x.trim()).filter(Boolean);

export function ServiceGrid({ blok }: { blok: any }) {
  return (
    <section {...storyblokEditable(blok)} className="block wrap">
      {blok.heading && <h2>{blok.heading}</h2>}
      <div className="grid">
        {(blok.items ?? []).map((it: any) => <StoryblokServerComponent blok={it} key={it._uid} />)}
      </div>
    </section>
  );
}

export function ServiceGridItem({ blok }: { blok: any }) {
  const code = (blok.icon ?? "").slice(0, 2).toUpperCase();
  return (
    <a {...storyblokEditable(blok)} className="card" href={blok.link?.url || "#"}>
      <div className="ic">{code}</div>
      <h3>{blok.title}</h3>
      {blok.blurb && <p>{blok.blurb}</p>}
    </a>
  );
}

export function ServiceBlock({ blok }: { blok: any }) {
  return (
    <section {...storyblokEditable(blok)} className={`block wrap sblock sblock--${blok.kind}`}>
      <h2>{blok.heading}</h2>
      {blok.body && <div className="rt">{render(blok.body)}</div>}
      {blok.kind === "process" && lines(blok.steps).length > 0 && (
        <ol className="steps">{lines(blok.steps).map((s, i) => <li key={i}>{s}</li>)}</ol>
      )}
    </section>
  );
}

export function PriceBand({ blok }: { blok: any }) {
  return (
    <section {...storyblokEditable(blok)} className="block wrap">
      <h2>{blok.heading}</h2>
      <div className="prices">
        {(blok.tiers ?? []).map((t: any) => <StoryblokServerComponent blok={t} key={t._uid} />)}
      </div>
      {blok.disclaimer && <p className="disc">{blok.disclaimer}</p>}
    </section>
  );
}

export function PriceTier({ blok }: { blok: any }) {
  return (
    <div {...storyblokEditable(blok)} className="ptier">
      <div className="plabel">{blok.label}</div>
      <div className="prange">{blok.range}</div>
      {blok.note && <div className="pnote">{blok.note}</div>}
    </div>
  );
}

export function WhyTest({ blok }: { blok: any }) {
  return (
    <section {...storyblokEditable(blok)} className="block why">
      <div className="wrap">
        <h2>{blok.heading}</h2>
        {blok.body && <div className="rt">{render(blok.body)}</div>}
        <div className="contam">
          {lines(blok.contaminants).map((c, i) => (
            <span key={i} className={`chip ${/hard/i.test(c) ? "warn" : ""}`}>{c}</span>
          ))}
        </div>
      </div>
    </section>
  );
}

export function TestimonialRow({ blok }: { blok: any }) {
  return (
    <section {...storyblokEditable(blok)} className="block wrap">
      {blok.heading && <h2>{blok.heading}</h2>}
      <div className="reviews">
        {(blok.items ?? []).map((t: any) => <StoryblokServerComponent blok={t} key={t._uid} />)}
      </div>
    </section>
  );
}

export function Testimonial({ blok }: { blok: any }) {
  const stars = "★".repeat(Math.max(1, Math.min(5, Number(blok.rating ?? 5))));
  return (
    <div {...storyblokEditable(blok)} className="review">
      <div className="stars" aria-label={`${blok.rating} out of 5 stars`}>{stars}</div>
      <p className="q">{blok.quote}</p>
      <p className="who"><b>{blok.author}</b>{blok.location ? ` · ${blok.location}` : ""}</p>
    </div>
  );
}

// FAQ emits FAQPage JSON-LD — SEO-critical for local service queries.
export function Faq({ blok }: { blok: any }) {
  const items = (blok.items ?? []);
  const jsonLd = {
    "@context": "https://schema.org", "@type": "FAQPage",
    mainEntity: items.map((it: any) => ({
      "@type": "Question", name: it.question,
      acceptedAnswer: { "@type": "Answer", text: richToText(it.answer) },
    })),
  };
  return (
    <section {...storyblokEditable(blok)} className="block wrap">
      <h2>{blok.heading}</h2>
      <dl className="faq">
        {items.map((it: any) => (
          <div key={it._uid} className="faq-item">
            <dt>{it.question}</dt>
            <dd>{render(it.answer)}</dd>
          </div>
        ))}
      </dl>
      <script type="application/ld+json"
              dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />
    </section>
  );
}
export function FaqItem() { return null; } // rendered by Faq parent

export function ServiceArea({ blok }: { blok: any }) {
  return (
    <section {...storyblokEditable(blok)} className="block wrap">
      <h2>{blok.heading}</h2>
      <ul className="cities">{lines(blok.cities).map((c, i) => <li key={i}>{c}</li>)}</ul>
      {blok.note && <p className="disc">{blok.note}</p>}
    </section>
  );
}

export function CtaBand({ blok }: { blok: any }) {
  return (
    <section {...storyblokEditable(blok)} className="block wrap">
      <div className="ctaband">
        <h2>{blok.heading}</h2>
        <a className="btn-dark" href={blok.cta_link?.url || "#contact"}>{blok.cta_label}</a>
      </div>
    </section>
  );
}

export function TrustStrip({ blok }: { blok: any }) {
  return (
    <div {...storyblokEditable(blok)} className="trust-strip wrap">
      {lines(blok.items).map((t, i) => <span key={i}>{t}</span>)}
    </div>
  );
}

// Minimal richtext->text for JSON-LD (schema needs plain strings).
function richToText(rt: any): string {
  if (!rt || !rt.content) return "";
  const walk = (nodes: any[]): string =>
    nodes.map((n) => n.text ?? (n.content ? walk(n.content) : "")).join("");
  return walk(rt.content).slice(0, 900);
}
