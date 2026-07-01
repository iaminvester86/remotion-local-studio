# The Remotion side

`rls` produces assets (audio, captions, images, clips) and does FFmpeg assembly.
Remotion is what composes them into a final video. They are separate pieces; this
folder explains how they meet.

## Create a Remotion project
From wherever you want the video project to live:
```
npx create-video@latest
cd <your-project>
npm install
npx remotion add @remotion/captions @remotion/transitions
```

## Where assets go
Run `rls` commands from inside the Remotion project so relative `public/` paths line
up. The tools write to:
```
public/audio/     voiceovers (wav)
public/music/     music beds (wav)
public/images/    stills
public/clips/     moving clips (mp4)
public/captions/  srt + word-level json
```
Reference them in components with `staticFile("audio/vo.wav")`, etc.

## Render
```
npm run dev            # live preview
npx remotion render    # final MP4 into out/
```

## Two ways to lay out the repos
- Simple: keep `rls` (this repo) and your Remotion project as separate folders;
  activate the venv, then `cd` into the Remotion project to run `rls` commands.
- Combined: scaffold the Remotion project at the root of a copy of this repo so
  `public/` and `rls` share one tree. Either works; the tools only care about the
  current working directory when resolving `public/`.
