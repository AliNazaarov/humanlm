from common import T
# --- already-good human copy: leave almost untouched (5)
G="Already-good human copy. A good rewrite changes little or nothing (edit distance well under 40%). Fail if voice, rhythm or meaning is lost."
T("cold_email","already_good",G,"Brewlog founder emailing a homebrew shop owner","Dave Kerr, owner of Kerr's Brew Supplies, Leeds","Ask if he'd stock 10 units",
 ["Prospect fact: Dave's shop runs a monthly brewing class","Brewlog is $79 retail; wholesale price $52","Sender Niamh Doyle"],
 ["Dave","monthly brewing class","$79 retail, $52 wholesale","10 units","Niamh Doyle"],
"""Subject: something for your Thursday class

Hi Dave,

I saw your shop runs a brewing class once a month. I make Brewlog, a hydrometer that floats in the fermenter and sends gravity readings to a phone, so a class can watch a batch ferment without anyone opening the lid.

It retails at $79. Wholesale is $52.

Would you try 10 units on the shelf and see if the class people go for it?

Niamh Doyle
Brewlog""",
"""Subject: something for your brewing class

Hi Dave,

I saw your shop runs a brewing class once a month. I make Brewlog, a hydrometer that floats in the fermenter and sends gravity readings to a phone, so a class can watch a batch ferment without anyone opening the lid.

It retails at $79. Wholesale is $52.

Would you try 10 units on the shelf and see if the class people go for it?

Niamh Doyle
Brewlog""",
 names=["Dave Kerr","Kerr's Brew Supplies","Brewlog","Niamh Doyle"], draft_is_ai=False)
T("linkedin_post","already_good",G,"Ferrous CEO on a hiring mistake","manufacturing founders","No CTA",
 ["Hired a sales head from a large automation company in 2023","He left after 4 months","Lesson: Ferrous's buyers were plant heads, not procurement"],
 ["sales head from large automation company, 2023","left after 4 months","buyers are plant heads, not procurement"],
"""In 2023 I hired a head of sales from one of the big automation companies. He left after 4 months, and it was mostly my fault.

He was used to selling to procurement teams with a budget line and a tender. Our buyers were plant heads who had a broken spindle last quarter and wanted it not to happen again. Different conversation, different pace.

I hired for the logo on the CV instead of for the buyer we actually had.

Next time I'll start by asking candidates to tell me about the last plant head they sold to.""",
"""In 2023 I hired a head of sales from one of the big automation companies. He left after 4 months, and it was mostly my fault.

He was used to selling to procurement teams with a budget line and a tender. Our buyers were plant heads who had a broken spindle last quarter and wanted it not to happen again. Different conversation, different pace.

I hired for the logo on the CV instead of for the buyer we actually had.

Next time I'll start by asking candidates to tell me about the last plant head they sold to.""",
 names=["Ferrous"], draft_is_ai=False)
T("landing_hero","already_good",G,"Tabwise hero","agency owners","Start free",
 ["Fills timesheets from Google Calendar and Jira","3.2 billable hours per person per week recovered on average (22 agencies)"],
 ["calendar and Jira","3.2 hours","22 agencies","Start free"],
"""Headline: Your team worked the hours. Now bill them.
Subhead: Tabwise fills in timesheets from Google Calendar and Jira. Across 22 agencies, that found 3.2 billable hours per person per week.
CTA: Start free""",
"""Headline: Your team worked the hours. Now bill them.
Subhead: Tabwise fills in timesheets from Google Calendar and Jira. Across 22 agencies, that found 3.2 billable hours per person per week.
CTA: Start free""",
 names=["Tabwise"], draft_is_ai=False)
T("launch_email","already_good",G,"Pebble Pantry price-change email","Pebble Pantry subscribers","None",
 ["Price goes from €4.99 to €5.99 a month on March 1","Current subscribers keep €4.99 until September 1","Reason: grocery-price data provider raised its fee","Cancel anytime in Settings"],
 ["€4.99 to €5.99 on March 1","current subscribers keep €4.99 until September 1","data provider raised fee","cancel in Settings"],
"""Subject: Pebble Pantry will cost €5.99 from March

Olá,

From March 1, Pebble Pantry will cost €5.99 a month instead of €4.99.

The company that gives us supermarket prices for Continente and Pingo Doce raised its fee, and we can't absorb it at €4.99.

You won't pay more yet. If you're subscribed today, you keep €4.99 until September 1.

If you'd rather stop, you can cancel any time in Settings. No hard feelings.

Inês""",
"""Subject: Pebble Pantry will cost €5.99 from March

Olá,

From March 1, Pebble Pantry will cost €5.99 a month instead of €4.99.

The company that gives us supermarket prices for Continente and Pingo Doce raised its fee, and we can't absorb it at €4.99.

You won't pay more yet. If you're subscribed today, you keep €4.99 until September 1.

If you'd rather stop, you can cancel any time in Settings. No hard feelings.

Inês""",
 names=["Pebble Pantry","Inês Moreira","Continente","Pingo Doce"], draft_is_ai=False)
T("x_post","already_good",G,"Patchwork CI founder joke post","developers","None",
 ["Patchwork CI flagged one of its own tests as flaky"],["flagged its own test as flaky"],
"""Patchwork CI just quarantined one of Patchwork CI's own tests as flaky.

It was right. We're fixing it. Humbling day.""",
"""Patchwork CI just quarantined one of Patchwork CI's own tests as flaky.

It was right. We're fixing it. Humbling day.""",
 names=["Patchwork CI"], draft_is_ai=False)
# --- very short inputs (3)
T("landing_hero","very_short","Output stays short (a CTA button stays a button). Do not pad into a paragraph; no new claims.",
 "Choreboard signup button","parents","Sign up",["Free 14-day trial","No card needed to start"],["free 14-day trial","no card needed"],
"""Sign Up — It's Free! 🚀""",
"""Start your free 14-day trial""",
 names=["Choreboard"], forbidden=["forever"])
T("x_post","very_short","One line in, one line out. Keep the date.",
 "Stackhand maintenance notice","users","None",["Scheduled maintenance Sunday 9 February, 02:00-02:30 UTC"],["Sunday 9 February","02:00-02:30 UTC"],
"""⚠️ Heads up! Scheduled maintenance Sunday 9 Feb, 02:00–02:30 UTC. We'll be back better than ever! 💪""",
"""Scheduled maintenance: Sunday 9 February, 02:00-02:30 UTC.""",
 names=["Stackhand"], verbatim=["02:00"], forbidden=["better than ever"])
T("product_description","very_short","Push notification stays under ~80 characters and keeps the number.",
 "Brewlog push notification","Brewlog users","Open app",["Gravity has been stable at 1.012 for 48 hours"],["1.012","48 hours"],
"""🎉 Great news, brewer! Your beer's gravity has been rock-solid at 1.012 for 48 hours — it might be time to bottle! 🍺✨""",
"""Gravity has held at 1.012 for 48 hours. Your beer may be ready to bottle.""",
 names=["Brewlog"], verbatim=["1.012"], forbidden=["rock-solid"])
# --- lists (3)
L="List input. Keep it a list, keep every item and its order unless reordering is clearly better; trim filler inside items; no new items."
T("landing_section","list",L,"Fieldnote feature list","UX researchers","(section)",
 ["Transcribes interviews in 30 languages","Speaker labels","Tags quotes by theme","Exports to Notion or Miro","Deletes recordings after 30 days unless you keep them"],
 ["30 languages","speaker labels","tags by theme","Notion or Miro","deletes recordings after 30 days unless kept"],
"""Everything You Need to Unlock Research Insights ✨
• 🌍 Powerful transcription in 30 languages
• 🗣️ Intelligent speaker labeling for crystal-clear conversations
• 🏷️ AI-powered theme tagging that surfaces what matters most
• 🔗 Seamless export to Notion or Miro
• 🔒 Privacy-first: recordings automatically deleted after 30 days (unless you choose to keep them)""",
"""What Fieldnote does
• Transcribes interviews in 30 languages
• Labels who's speaking
• Tags quotes by theme
• Exports to Notion or Miro
• Deletes recordings after 30 days, unless you choose to keep them""",
 names=["Fieldnote"], forbidden=["crystal-clear"])
T("launch_email","list",L,"Crateful changelog email (4 items)","Crateful users","None",
 ["Forecasts now account for out-of-stock days","CSV export of forecasts","Slack alerts can go to any channel, not only #inventory","Fixed: duplicate alerts for bundled products"],
 ["out-of-stock days","CSV export","Slack alerts to any channel","fixed duplicate alerts for bundles"],
"""Subject: 🚀 What's New at Crateful This Month!

Hey there! We've been busy building some amazing improvements to supercharge your inventory game:

✅ Smarter forecasts that now intelligently account for out-of-stock days
✅ Effortless CSV export of your forecasts
✅ Flexible Slack alerts — send them to any channel, not just #inventory!
✅ Squashed a pesky bug causing duplicate alerts for bundled products 🐛

Stay stocked, stay ahead! 📦
The Crateful Team""",
"""Subject: Crateful changes this month

Hi,

Four changes this month:

- Forecasts now take out-of-stock days into account.
- You can export forecasts as a CSV.
- Slack alerts can go to any channel, not only #inventory.
- Fixed: bundled products no longer trigger duplicate alerts.

The Crateful team""",
 names=["Crateful","Slack"], forbidden=["supercharge"])
T("landing_section","list",L,"Gridline Solar 'What's included' list","small-business owners","(section)",
 ["Panels and inverter","Installation within 21 days","Monitoring app","Maintenance visits twice a year","Insurance against storm damage","Lease from R$ 890 a month"],
 ["panels and inverter","install within 21 days","monitoring app","maintenance twice a year","storm-damage insurance","from R$ 890/month"],
"""What's Included — Everything You Need, Nothing You Don't ☀️
1. Premium high-efficiency panels and a state-of-the-art inverter
2. Hassle-free professional installation within 21 days
3. An intuitive monitoring app to track your savings in real time
4. Worry-free maintenance visits twice a year
5. Comprehensive insurance against storm damage
All from just R$ 890/month!""",
"""What's included
1. Panels and inverter
2. Installation within 21 days
3. A monitoring app
4. Maintenance visits twice a year
5. Insurance against storm damage
From R$ 890 a month.""",
 names=["Gridline Solar"], forbidden=["high-efficiency","track your savings"])
# --- non-native English drafts (3): fix grammar, keep voice and every fact
N="Founder's own non-native English draft (not AI). Fix grammar and word choice, keep the founder's voice, directness and every fact. Do not turn it into polished marketing."
T("cold_email","non_native",N,"Tashkent dev agency 'Ipak Code' emailing a German startup. Sender: Jasur Rakhimov","Felix Braun, CTO of Wendepunkt (logistics SaaS)","Ask for a 30-minute call",
 ["Prospect fact: Wendepunkt is hiring 3 React Native developers","Ipak Code has 18 React Native developers in Tashkent","Rate €38 per hour","Overlap with German working hours: 4 hours a day"],
 ["Felix","hiring 3 React Native developers","18 React Native devs in Tashkent","€38/hour","4 hours overlap","30-minute call"],
"""Subject: About your React Native vacancies

Dear Felix,

I see that Wendepunkt is searching 3 React Native developers. We are company Ipak Code from Tashkent, we have 18 React Native developers in our team. Our rate is 38 euro per hour. With Germany we have 4 hours overlap of working time every day, so communication is not problem.

Maybe it is interesting for you to make call 30 minutes and I will show our previous projects?

Best regards,
Jasur Rakhimov
Ipak Code""",
"""Subject: Your React Native vacancies

Dear Felix,

I saw that Wendepunkt is looking for 3 React Native developers. We're Ipak Code, a team in Tashkent with 18 React Native developers. Our rate is €38 an hour, and we overlap with German working hours for 4 hours every day, so communication isn't a problem.

Would a 30-minute call be useful? I can show you some of our previous projects.

Best regards,
Jasur Rakhimov
Ipak Code""",
 names=["Ipak Code","Jasur Rakhimov","Felix Braun","Wendepunkt","Tashkent"], draft_is_ai=False)
T("linkedin_post","non_native",N,"Rotaship founder Dewi Santoso, Indonesian, writing her own post","SEA founders","No CTA",
 ["Rotaship reached 140 outlets","Team of 9 in Jakarta","First customer was her uncle's restaurant, 3 outlets"],
 ["140 outlets","team of 9 in Jakarta","first customer: uncle's restaurant, 3 outlets"],
"""Today Rotaship is reach 140 outlets. I am still not believe it.

Our first customer was restaurant of my uncle, only 3 outlets, and honestly he use it because he is my uncle. Now we are 9 person team in Jakarta and most of our customer we never meet before.

Thank you for everyone who trust us when we are still very small. Terima kasih banyak.""",
"""Today Rotaship reached 140 outlets. I still can't believe it.

Our first customer was my uncle's restaurant, only 3 outlets, and honestly he used it because he's my uncle. Now we're a team of 9 in Jakarta, and most of our customers are people we had never met before.

Thank you to everyone who trusted us when we were still very small. Terima kasih banyak.""",
 names=["Rotaship","Dewi Santoso","Jakarta"], draft_is_ai=False)
T("product_description","non_native",N,"Brazilian leather-goods brand 'Couro Bravo' product description written by founder","online shoppers","Add to cart",
 ["Wallet made from vegetable-tanned leather from Franca, São Paulo","Hand-stitched","Holds 6 cards","R$ 290","Leather darkens with use"],
 ["vegetable-tanned leather from Franca","hand-stitched","6 cards","R$ 290","darkens with use"],
"""This wallet is make with vegetable tanned leather from Franca, in São Paulo state, the city most famous of Brazil for leather. Each one is stitched by hand in our workshop. It have space for 6 cards. With the time the leather become more dark, this is normal and is beautiful. Price R$ 290.""",
"""This wallet is made from vegetable-tanned leather from Franca, in São Paulo state, the Brazilian city most famous for leather. Each one is stitched by hand in our workshop. It holds 6 cards. Over time the leather gets darker. That's normal, and it's beautiful. R$ 290.""",
 names=["Couro Bravo","Franca","São Paulo"], draft_is_ai=False)
# --- deliberate typos (2)
Y="Human draft with deliberate typos and errors. Fix every spelling/grammar error, change nothing else of substance; names must keep their correct spelling from the brief."
T("launch_email","typos",Y,"Halftone v1.4 update email","Halftone users","None",
 ["v1.4 adds support for Canon R5 Mark II raw files","Culling is about 20% faster on Apple silicon","Sender: Leo Martins"],
 ["v1.4","Canon R5 Mark II raw files","about 20% faster on Apple silicon","Leo Martins"],
"""Subject: Halftone 1.4 is out

Hi,

Halftone 1.4 is out today. It now suports raw files from the Canon R5 Mark II, wich a lot of you have been asking for since it came out.

Culling is also about 20% faster on Apple silicone, so a full wedding should take noticably less time.

Thier is nothing you need to do, the plugin will update itself next time you open Lightroom.

Leo Martins""",
"""Subject: Halftone 1.4 is out

Hi,

Halftone 1.4 is out today. It now supports raw files from the Canon R5 Mark II, which a lot of you have been asking for since it came out.

Culling is also about 20% faster on Apple silicon, so a full wedding should take noticeably less time.

There's nothing you need to do. The plugin will update itself next time you open Lightroom.

Leo Martins""",
 names=["Halftone","Canon R5 Mark II","Leo Martins","Lightroom"], verbatim=["20%"], draft_is_ai=False)
T("landing_section","typos",Y,"Doorstep Vet FAQ answer","pet owners","(FAQ)",
 ["Doorstep Vet covers suburbs within 8 km of Melbourne CBD","Visits Monday to Saturday, 8am-6pm","After-hours emergencies: go to the nearest emergency vet"],
 ["within 8 km of Melbourne CBD","Monday to Saturday, 8am-6pm","after hours: nearest emergency vet"],
"""Where do you visit?
We cover suburbs within 8 km of the Melbourne CBD, Monday to Saturday, 8am-6pm. If your pet has an emergancy after hours, please dont wait for us, go strait to your nearest emergency vet.""",
"""Where do you visit?
We cover suburbs within 8 km of the Melbourne CBD, Monday to Saturday, 8am-6pm. If your pet has an emergency after hours, please don't wait for us. Go straight to your nearest emergency vet.""",
 names=["Doorstep Vet","Melbourne"], verbatim=["8 km"], draft_is_ai=False)
