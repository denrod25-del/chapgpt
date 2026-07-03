// storyblok.ts — SDK init + component registry (Next.js App Router)
// npm i @storyblok/react
import { storyblokInit, apiPlugin } from "@storyblok/react/rsc";

import Page from "./components/Page";
import Hero from "./components/Hero";
import WaterTestReadout from "./components/WaterTestReadout";
import ContactForm from "./components/ContactForm";
// Presentational blocks are consolidated in blocks.tsx (split per-file in production).
import {
  ServiceGrid, ServiceGridItem, ServiceBlock, PriceBand, PriceTier, WhyTest,
  TestimonialRow, Testimonial, Faq, FaqItem, ServiceArea, CtaBand, TrustStrip,
} from "./components/blocks";

// Component name (Storyblok block "name") -> React component.
export const components = {
  page: Page,
  hero: Hero,
  water_test_readout: WaterTestReadout,
  service_grid: ServiceGrid,
  service_grid_item: ServiceGridItem,
  service_block: ServiceBlock,
  price_band: PriceBand,
  price_tier: PriceTier,
  why_test: WhyTest,
  testimonial_row: TestimonialRow,
  testimonial: Testimonial,
  faq: Faq,
  faq_item: FaqItem,
  service_area: ServiceArea,
  cta_band: CtaBand,
  trust_strip: TrustStrip,
  contact_form: ContactForm,
};

export const getStoryblok = () =>
  storyblokInit({
    accessToken: process.env.STORYBLOK_TOKEN,   // read-only Content Delivery token
    use: [apiPlugin],
    components,
    apiOptions: { region: "us" },               // set to your space region
  });
