/* HibAI Studio — dashboard questions.
 *
 * Every screen of the dashboard comes from this list, in this order.
 * To add a question, copy one block and change it. Nothing else to edit.
 *
 *   key      where the answer is saved in brief.json ("colors.main" = nested)
 *   type     choice | text | longtext | toggle | colors
 *   dr / en  Darija and English wording (title, help, option labels)
 *   default  used when the user skips
 *
 * A new key also needs a line in DEFAULT_BRIEF inside scripts/hibai.py
 * if the video engine should use it. Unknown keys are still saved and
 * Claude reads them from brief.json (handy for wishes the engine can't do yet).
 */
window.HIBAI_QUESTIONS = [
  {
    key: "goal", type: "longtext",
    dr: { title: "على شنو كتهضر ف هاد الفيديو؟", help: "جملة ولا جوج — باش نفهم الفكرة" },
    en: { title: "What's this video about?", help: "One or two lines so I get the idea" },
    placeholder: "مثلا: 3 ديال الحيل ف ChatGPT باش تتعلم أي حاجة دغيا",
    default: ""
  },
  {
    key: "language", type: "choice",
    dr: { title: "بأي لغة كتهضر؟", help: "باش نكتب كلامك صحيح" },
    en: { title: "What language do you speak in it?", help: "So the captions come out right" },
    options: [
      { value: "ar", dr: "الدارجة / العربية", en: "Darija / Arabic" },
      { value: "en", dr: "الإنجليزية", en: "English" },
      { value: "fr", dr: "الفرنسية", en: "French" },
      { value: "auto", dr: "مخلّط", en: "A mix" }
    ],
    default: "ar"
  },
  {
    key: "hook", type: "text",
    dr: { title: "عنوان الفوق (الهوك)", help: "كيبان ف أول 3 ثواني فوق راسك. خليه قصير — ولا خليه خاوي" },
    en: { title: "Top headline (the hook)", help: "Shows for the first 3 seconds above your head. Keep it short, or leave empty" },
    placeholder: "3 codes f ChatGPT",
    max: 40,
    default: ""
  },
  {
    key: "caption_style", type: "choice", look: "captions",
    dr: { title: "كيفاش بغيتي الكابشن؟", help: "الكلمة اللي كتقولها كتشعل بلون HibAI" },
    en: { title: "Caption style", help: "The word you're saying lights up in HibAI colour" },
    options: [
      { value: "pop", dr: "كتنط", en: "Pop", demo: "pop" },
      { value: "clean", dr: "نقي", en: "Clean", demo: "clean" },
      { value: "box", dr: "ف بلوك", en: "Boxed", demo: "box" },
      { value: "none", dr: "بلا كابشن", en: "No captions", demo: "none" }
    ],
    default: "pop"
  },
  {
    key: "words_per_card", type: "choice",
    dr: { title: "شحال من كلمة ف المرة؟", help: "قليل = سريع وكيشد العين، كثير = مريح للقراية" },
    en: { title: "Words on screen at once", help: "Fewer feels fast and punchy, more is easier to read" },
    options: [
      { value: 1, dr: "1", en: "one" },
      { value: 2, dr: "2", en: "two" },
      { value: 3, dr: "3", en: "three" },
      { value: 4, dr: "4", en: "four" }
    ],
    default: 3
  },
  {
    key: "caption_size", type: "choice",
    dr: { title: "قدّ الكتابة", help: "" },
    en: { title: "Caption size", help: "" },
    options: [
      { value: "medium", dr: "متوسط", en: "Medium" },
      { value: "big", dr: "كبير", en: "Big" },
      { value: "huge", dr: "كبير بزاف", en: "Huge" }
    ],
    default: "big"
  },
  {
    key: "pace", type: "choice",
    dr: { title: "الإيقاع", help: "شحال نقطع من السكتات" },
    en: { title: "Pace", help: "How tight I cut the pauses" },
    options: [
      { value: "fast", dr: "سريع — بلا تنفس", en: "Fast, no breathing room" },
      { value: "normal", dr: "عادي", en: "Normal" },
      { value: "calm", dr: "هادي — نخلي السكتات", en: "Calm, keep the pauses" }
    ],
    default: "normal"
  },
  {
    key: "zoom", type: "toggle",
    dr: { title: "زوم خفيف بين اللقطات؟", help: "كيخبي القطعات وكيعطي حركة" },
    en: { title: "Light zoom between cuts?", help: "Hides the jump cuts and adds energy" },
    default: true
  },
  {
    key: "progress_bar", type: "toggle",
    dr: { title: "خط التقدم تحت الكابشن؟", help: "كيبين شحال باقي ف الفيديو" },
    en: { title: "Progress line under the captions?", help: "Shows how much of the video is left" },
    default: true
  },
  {
    key: "colors", type: "colors",
    dr: { title: "الألوان", help: "ألوان HibAI واجدين — بدّلهم إلا بغيتي" },
    en: { title: "Colours", help: "HibAI colours are ready, change them if you like" },
    fields: [
      { key: "main", dr: "الكلمة الحالية", en: "Current word" },
      { key: "accent", dr: "الكلمات المهمة", en: "Key words" },
      { key: "text", dr: "باقي الكتابة", en: "Other text" }
    ],
    presets: [
      { name: "HibAI", main: "#8eff01", accent: "#8b53fe", text: "#ffffff" },
      { name: "Purple", main: "#b48cff", accent: "#8eff01", text: "#ffffff" },
      { name: "Gold", main: "#ffd23f", accent: "#ff5e5b", text: "#ffffff" },
      { name: "Mono", main: "#ffffff", accent: "#8eff01", text: "#d6d9e0" }
    ],
    default: { main: "#8eff01", accent: "#8b53fe", text: "#ffffff" }
  },
  {
    key: "font", type: "choice", look: "fonts",
    dr: { title: "الخط", help: "خطوط موجودين ف أي ويندوز" },
    en: { title: "Font", help: "Fonts every Windows computer already has" },
    options: [
      { value: "Segoe UI", dr: "عصري", en: "Modern" },
      { value: "Tahoma", dr: "واضح", en: "Clear" },
      { value: "Sakkal Majalla", dr: "كلاسيكي", en: "Classic" },
      { value: "Arial", dr: "بسيط", en: "Simple" }
    ],
    default: "Segoe UI"
  },
  {
    key: "handle", type: "text",
    dr: { title: "الحساب ديالك", help: "كيبان صغير فوق — خليه خاوي إلا ما بغيتيهش" },
    en: { title: "Your handle", help: "Shows small at the top, leave empty to skip" },
    placeholder: "@hibssssi",
    max: 30,
    default: ""
  },
  {
    key: "cta", type: "text",
    dr: { title: "جملة الختام", help: "كتبان ف آخر ثانيتين — مثلا: كتب CODE ف الكومنت" },
    en: { title: "Closing line", help: "Shows in the last 2 seconds, e.g. comment CODE" },
    placeholder: "كتب CODE ف الكومنت",
    max: 40,
    default: ""
  },
  {
    key: "notes", type: "longtext",
    dr: { title: "شي حاجة أخرى؟", help: "أي فكرة ولا طلب — Claude غادي يقراها" },
    en: { title: "Anything else?", help: "Any idea or wish, Claude will read it" },
    placeholder: "",
    default: ""
  }
];
