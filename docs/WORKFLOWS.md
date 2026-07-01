# Workflows

A narrated video, end to end, with only local tools. Run these from inside your
Remotion project directory (so `public/` resolves), with the venv activated.

## Order of operations
Script first, because voice timing drives scene lengths and captions.

1. Write the narration to `script.txt`.
2. Voiceover:
   ```
   rls tts --text-file script.txt --out public/audio/vo.wav
   ```
3. Captions from that audio (word-level JSON):
   ```
   rls transcribe --input public/audio/vo.wav --out public/captions/vo --model base
   ```
4. Visuals per scene, cheapest reliable path first:
   - real footage you already have, or
   - a generated still animated with Ken Burns:
     ```
     rls image --prompt "..." --out public/images/s1.png
     rls ff kenburns public/images/s1.png public/clips/s1.mp4 6
     ```
   - experimental text-to-video only if you have a CUDA GPU:
     ```
     rls video --prompt "..." --out public/clips/s1.mp4
     ```
5. Music sized to the final length, mixed low:
   ```
   rls music --prompt "ambient pad" --duration 30 --out public/music/bed.wav
   ```
6. Compose in Remotion (React). Reference assets with `staticFile()`.
7. Preview: `npm run dev`.
8. Render: `npx remotion render`.
9. Review locally and iterate:
   ```
   rls analyze --input out/video.mp4 --outdir .rls/review
   ```
   Open `.rls/review/frames/` and judge pacing, framing, caption readability.

## Captions component (sketch)
Load `public/captions/vo.json` and feed `createTikTokStyleCaptions`:
```tsx
import { useCurrentFrame, useVideoConfig, staticFile } from "remotion";
import { createTikTokStyleCaptions } from "@remotion/captions";
// fetch the json at build time, map tokens to {text, startMs, endMs},
// then render the active page based on (frame / fps) * 1000 ms.
```

## When you have no GPU
Steps 1, 2, 3, 7, 8, 9 and all `rls ff` assembly work fine. Replace step 4's
image generation with real footage. Skip step 5 or supply your own music file.
