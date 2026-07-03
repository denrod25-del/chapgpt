// components/Page.tsx — root content type. Renders body blocks.
import { storyblokEditable, StoryblokServerComponent } from "@storyblok/react/rsc";

type Blok = { _uid: string; component: string; [k: string]: any };

export default function Page({ blok }: { blok: Blok }) {
  return (
    <main {...storyblokEditable(blok)}>
      {(blok.body ?? []).map((nested: Blok) => (
        <StoryblokServerComponent blok={nested} key={nested._uid} />
      ))}
    </main>
  );
}
