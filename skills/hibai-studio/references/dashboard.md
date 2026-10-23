# Changing the HibAI dashboard

The dashboard is `dashboard/index.html` (look and flow) + `dashboard/questions.js` (the questions).
To add, remove or reorder questions you only touch `questions.js`.

## Add a question

Copy a block in `questions.js` and change it:

```js
{
  key: "music", type: "choice",
  dr: { title: "بغيتي موسيقى ف اللور؟", help: "" },
  en: { title: "Background music?", help: "" },
  options: [
    { value: "none", dr: "لا", en: "No" },
    { value: "soft", dr: "خفيفة", en: "Soft" }
  ],
  default: "none"
}
```

Types: `choice` (buttons), `text` (one line, `max` = length), `longtext` (a box),
`toggle` (yes/no), `colors` (colour pickers + presets).
Add `look: "captions"` or `look: "fonts"` on a choice to get the little previews.

## Make the video engine use it

1. Add the key with its default to `DEFAULT_BRIEF` in `scripts/hibai.py`.
2. Use `b["music"]` where it matters (e.g. inside `cmd_render`).
3. Note it in `SKILL.md` so Claude knows what it does.

Until step 2 is done, the answer still lands in `brief.json` and Claude reads it as a wish.

## Change the look

Colours and fonts are CSS variables at the top of `index.html` (`--lime`, `--purple`,
`--ground`…). The wordmark is text ("Hib" + "AI"), not an image. The footer photo is
`dashboard/assets/pfp.png`.

## Test it

```bash
python scripts/hibai.py dashboard ./test-work --keep
```

Opens the page; every save rewrites `./test-work/brief.json`. Stop it with Ctrl+C.
