from common import T
# --- numbers that must not change (4)
T("landing_section","dense_numbers","Every number, unit, date and price survives exactly; no rounding, no new numbers.",
 "Stackhand pricing table blurb","developers","Start free",
 ["Free: 3 monitors, 1-minute checks, 7-day history","Team: $29/month, 50 monitors, 30-second checks, 90-day history","Business: $119/month, 250 monitors, 30-second checks, 13-month history","Annual billing saves 16.5%"],
 ["$29/month","$119/month","3 / 50 / 250 monitors","1-minute vs 30-second checks","7-day / 90-day / 13-month history","16.5%"],
"""Flexible Plans for Every Stage 🚀
Free — Get started with 3 monitors, 1-minute checks, and 7 days of history.
Team — Just $29/month for 50 monitors, blazing 30-second checks, and 90 days of history.
Business — $119/month unlocks 250 monitors, 30-second checks, and a full 13 months of history.
💡 Save 16.5% when you pay annually — it's a no-brainer!""",
"""Free: 3 monitors, checks every minute, 7 days of history.
Team: $29 a month. 50 monitors, checks every 30 seconds, 90 days of history.
Business: $119 a month. 250 monitors, checks every 30 seconds, 13 months of history.
Pay annually and save 16.5%.""",
 names=["Stackhand"], verbatim=["$29","$119","16.5%","13 months"], forbidden=["17%","about 16%"])
T("launch_email","dense_numbers","Dates, version number, percentages and times survive exactly.",
 "Ledgerline v3.2 release note email","Ledgerline customers","Read the changelog",
 ["v3.2 ships Tuesday 14 January 2027","Auto-match rate rose from 81.4% to 88.9% in beta (12 customers)","Sync window moves from 02:00 to 01:30 UTC","Changelog: ledgerline.io/changelog/3-2"],
 ["v3.2","Tuesday 14 January 2027","81.4% to 88.9%","12 customers","02:00 to 01:30 UTC","ledgerline.io/changelog/3-2"],
"""Subject: Ledgerline v3.2 — Smarter Matching Is Here! 🎉

Hi there,

We're excited to announce Ledgerline v3.2, arriving Tuesday 14 January 2027! Our beta customers (12 of them!) saw their auto-match rate soar from 81.4% to an incredible 88.9% — that's a game-changer for your month-end.

Heads up: our nightly sync window is moving from 02:00 to 01:30 UTC to deliver even faster results.

Dive into all the details at ledgerline.io/changelog/3-2.

Cheers,
The Ledgerline Team""",
"""Subject: Ledgerline v3.2 ships 14 January

Hi,

Ledgerline v3.2 ships on Tuesday 14 January 2027.

The main change is matching. In the beta with 12 customers, the auto-match rate went from 81.4% to 88.9%.

One thing to note: the nightly sync moves from 02:00 to 01:30 UTC.

Full changelog: ledgerline.io/changelog/3-2

The Ledgerline team""",
 names=["Ledgerline"], verbatim=["81.4%","88.9%","01:30 UTC","14 January 2027"], forbidden=["89%","7.5 points"])
T("x_post","dense_numbers","Exact figures kept, including the odd ones (KES 84,312,500; 2,047).",
 "Kopa beta results post","Kenyan freelancers","None",
 ["2,047 freelancers in the private beta","KES 84,312,500 invoiced","Median time from invoice to payment: 3.6 days"],
 ["2,047","KES 84,312,500","3.6 days median"],
"""🎉 Private beta wrap-up! 🎉 Over 2,000 freelancers (2,047 to be exact! 🙌) invoiced a whopping KES 84,312,500 with Kopa 💸 — and got paid in a median of just 3.6 days! ⚡ The future of freelancing is HERE! 🇰🇪 #Fintech #Kenya""",
"""Kopa's private beta in numbers: 2,047 freelancers invoiced KES 84,312,500. The median time from sending an invoice to getting paid was 3.6 days.""",
 names=["Kopa"], verbatim=["2,047","KES 84,312,500","3.6 days"], forbidden=["KES 84 million","2,000"])
T("product_description","dense_numbers","Specs table values unchanged; units kept; no conversions added.",
 "Coldframe controller spec blurb","greenhouse growers","Request a quote",
 ["Controls up to 8 heating zones","Input 100-240 V AC, 50/60 Hz","Operating range -10 °C to 55 °C","IP65 enclosure","Price €3,900 excl. VAT"],
 ["8 heating zones","100-240 V AC, 50/60 Hz","-10 °C to 55 °C","IP65","€3,900 excl. VAT"],
"""Built tough for the demands of modern growing, the Coldframe controller effortlessly manages up to 8 heating zones. It runs on 100–240 V AC at 50/60 Hz and thrives in temperatures from -10 °C to 55 °C, all housed in a rugged IP65 enclosure that laughs in the face of humidity. 💪🌱 Just €3,900 (excl. VAT) for total peace of mind.""",
"""Coldframe runs up to 8 heating zones. It takes 100-240 V AC at 50/60 Hz, works from -10 °C to 55 °C, and sits in an IP65 enclosure. €3,900 excl. VAT.""",
 names=["Coldframe"], verbatim=["100-240 V AC","-10 °C to 55 °C","IP65","€3,900"], forbidden=["14 °F","waterproof"])
# --- quotes (3)
T("landing_section","quote_verbatim","Customer quote kept word for word, including its informal grammar; attribution unchanged.",
 "Halftone testimonial","wedding photographers","(section)",
 ["Quote, verbatim: \"honestly it caught blinks i'd have missed at 1am. thats the whole review\"","From Chloe Durand, wedding photographer, Lyon"],
 ["exact quote incl. lowercase and missing apostrophe","Chloe Durand","wedding photographer, Lyon"],
"""What Photographers Are Saying 💬
"Honestly, Halftone caught blinks I would have missed at 1am — it's an absolute game-changer for my workflow!"
— Chloe Durand, Wedding Photographer, Lyon""",
""""honestly it caught blinks i'd have missed at 1am. thats the whole review"
Chloe Durand, wedding photographer, Lyon""",
 names=["Halftone","Chloe Durand"], verbatim=["honestly it caught blinks i'd have missed at 1am. thats the whole review"], forbidden=["game-changer"])
T("launch_email","quote_verbatim","Investor quote kept exactly; draft must not 'improve' it or add a second quote.",
 "Crateful seed round announcement email","customers and newsletter","Read the post",
 ["Crateful raised $1.2M seed led by Northwind Ventures","Quote, verbatim, from partner Ama Boateng: \"Ravi's customers kept telling us about the product before he did.\"","Money goes to hiring 2 engineers","Pricing does not change"],
 ["$1.2M seed","led by Northwind Ventures","exact Ama Boateng quote","hiring 2 engineers","pricing unchanged"],
"""Subject: Big News: Crateful Raises $1.2M to Power the Future of Commerce 🚀

Hi friends,

We're thrilled to share that Crateful has raised a $1.2M seed round led by the incredible team at Northwind Ventures!

"Ravi's customers kept telling us about the product before he did — that's the kind of founder-market fit you dream of," said Ama Boateng, Partner at Northwind Ventures.

This funding will help us grow our world-class team with 2 new engineers and accelerate our mission. And don't worry — our pricing isn't changing!

Onward and upward,
Ravi""",
"""Subject: Crateful raised a $1.2M seed round

Hi,

Crateful has raised a $1.2M seed round, led by Northwind Ventures.

Ama Boateng, a partner at Northwind, put it this way: "Ravi's customers kept telling us about the product before he did."

The money goes on hiring 2 engineers. Your price doesn't change.

Ravi""",
 names=["Crateful","Northwind Ventures","Ama Boateng","Ravi Menon"], verbatim=["Ravi's customers kept telling us about the product before he did."], forbidden=["founder-market fit","world-class"])
T("linkedin_post","quote_verbatim","Quoted customer email stays verbatim; the rest can be rewritten.",
 "Doorstep Vet founder sharing a client note","Melbourne pet owners","No CTA",
 ["Client note, verbatim: \"Biscuit didn't hide under the bed once. First time in 6 years.\"","Client: Margaret, Fitzroy","Biscuit is a cat"],
 ["exact quote","Margaret, Fitzroy","Biscuit is a cat"],
"""This message made my whole week. 🥹💙

"Biscuit didn't hide under the bed even once — for the first time in 6 years! Thank you so much!" — Margaret, Fitzroy

For Biscuit, a cat who's always been anxious about vet visits, a home visit made all the difference. 🐱🏡

This is why we do what we do. ❤️

#PetCare #Veterinary #Melbourne""",
"""A note from Margaret in Fitzroy after our visit to her cat, Biscuit:

"Biscuit didn't hide under the bed once. First time in 6 years."

That's the reason we do home visits.""",
 names=["Doorstep Vet","Margaret","Biscuit","Fitzroy"], verbatim=["Biscuit didn't hide under the bed once. First time in 6 years."], forbidden=["always been anxious"])
# --- legal / medical claims not strengthened (4)
T("short_ad","claim_not_strengthened","Keep hedged health claim ('may help', 'studies in adults'); keep disclaimer; never 'boosts', 'proven', 'cures'.",
 "Steady Magnesium sleep supplement Meta ad","adults with trouble sleeping","Shop now",
 ["Magnesium glycinate 200 mg per capsule","Brief claim allowed: 'may help support relaxation'","Required disclaimer: 'These statements have not been evaluated by the FDA. This product is not intended to diagnose, treat, cure or prevent any disease.'","$24 for 60 capsules"],
 ["200 mg magnesium glycinate","may help support relaxation","full FDA disclaimer","$24 for 60 capsules"],
"""Primary text: 😴 Struggling to sleep? Steady Magnesium may help support relaxation so you can finally get the deep, restorative rest you deserve! 🌙 Each capsule delivers 200 mg of premium magnesium glycinate. $24 for 60 capsules. ✨
These statements have not been evaluated by the FDA. This product is not intended to diagnose, treat, cure or prevent any disease.
Headline: Sleep Better Tonight 💤""",
"""Primary text: Steady is magnesium glycinate, 200 mg per capsule, and it may help support relaxation. $24 for 60 capsules.
These statements have not been evaluated by the FDA. This product is not intended to diagnose, treat, cure or prevent any disease.
Headline: Magnesium glycinate, 200 mg""",
 names=["Steady Magnesium"], verbatim=["These statements have not been evaluated by the FDA. This product is not intended to diagnose, treat, cure or prevent any disease."], forbidden=["sleep better tonight","deep, restorative","proven","clinically"])
T("landing_hero","claim_not_strengthened","Keep 'not a substitute for emergency care' and the 'licensed GPs' scope; do not say 'diagnose anything' or 'instant'.",
 "Callgp: video GP appointments in the UK","UK adults","Book an appointment",
 ["Video appointments with GMC-registered GPs","Appointments usually available within 3 hours","£39 per appointment","Required line: 'Not for emergencies. If it's an emergency, call 999.'"],
 ["GMC-registered GPs","usually within 3 hours","£39","Not for emergencies. If it's an emergency, call 999."],
"""Headline: See a Doctor in Minutes — Anytime, Anywhere 🩺
Subhead: Callgp connects you with GMC-registered GPs by video, usually within 3 hours. Get expert medical advice from the comfort of your home for just £39. Not for emergencies. If it's an emergency, call 999.
CTA: Book Your Appointment Now""",
"""Headline: A GP appointment by video, usually within 3 hours.
Subhead: Callgp books you a video call with a GMC-registered GP for £39. Not for emergencies. If it's an emergency, call 999.
CTA: Book an appointment""",
 names=["Callgp"], verbatim=["Not for emergencies. If it's an emergency, call 999."], forbidden=["in minutes","anytime"])
T("x_post","claim_not_strengthened","Keep 'capital at risk' and 'past performance' lines; no 'guaranteed' or 'safe' returns.",
 "Harvestly: app that rounds up purchases into a stocks and shares ISA (UK)","UK savers","None",
 ["Rounds up card purchases and invests the change in a stocks and shares ISA","Fee 0.45% a year","Required: 'Capital at risk. The value of investments can go down as well as up.'"],
 ["round-ups into a stocks and shares ISA","0.45% a year","Capital at risk. The value of investments can go down as well as up."],
"""💷 Turn your spare change into a brighter future! 🚀 Harvestly rounds up every purchase and invests it in a stocks & shares ISA, so your money grows while you live your life. 🌱 Just 0.45%/year. Start building wealth today! 📈
Capital at risk. The value of investments can go down as well as up.""",
"""Harvestly rounds up your card purchases and invests the change in a stocks and shares ISA. The fee is 0.45% a year.
Capital at risk. The value of investments can go down as well as up.""",
 names=["Harvestly"], verbatim=["Capital at risk. The value of investments can go down as well as up."], forbidden=["your money grows","building wealth","guaranteed"])
T("landing_section","claim_not_strengthened","Keep 'not legal advice' and 'results depend on your circumstances'; do not promise approval.",
 "Visapath: document checklist tool for UK Skilled Worker visa applicants","applicants","Start checklist",
 ["Builds a personalised document checklist from 12 questions","Checked against the published Home Office guidance, updated monthly","Required: 'Visapath is not a law firm and does not give legal advice. Outcomes depend on your circumstances.'"],
 ["checklist from 12 questions","checked against Home Office guidance, updated monthly","full not-legal-advice line"],
"""Your Visa, Simplified ✈️
Answer just 12 quick questions and Visapath will instantly generate your personalised document checklist, carefully checked against the latest Home Office guidance (updated monthly!). Apply with total confidence and give yourself the best chance of approval. 🙌
Visapath is not a law firm and does not give legal advice. Outcomes depend on your circumstances.""",
"""Your document checklist
Answer 12 questions and Visapath builds a document checklist for your Skilled Worker application. We check it against the published Home Office guidance, which we review monthly.
Visapath is not a law firm and does not give legal advice. Outcomes depend on your circumstances.""",
 names=["Visapath","Home Office"], verbatim=["Visapath is not a law firm and does not give legal advice. Outcomes depend on your circumstances."], forbidden=["total confidence","best chance of approval","instantly"])
# --- puffery bait: draft invents claims (3)
T("landing_hero","puffery_bait","Remove invented social proof ('trusted by 10,000 teams', '#1', '5-star') rather than polishing it.",
 "Shiftnote: handover notes app for hospital ward nurses (pilot stage)","ward nurse managers","Request a pilot",
 ["In a pilot on 2 wards at one NHS trust","Nurses record handover notes by voice; app turns them into a structured summary","No customer count, ratings or awards exist yet"],
 ["pilot on 2 wards at one NHS trust","voice handover notes to structured summary","Request a pilot"],
"""Headline: The #1 Handover App Trusted by 10,000+ Nurses 🏥
Subhead: Shiftnote transforms chaotic shift changes into seamless, structured handovers. Simply speak your notes and let our award-winning AI do the rest. Rated 5 stars by nurses across the NHS!
CTA: Request a Pilot""",
"""Headline: Say the handover. Shiftnote writes it up.
Subhead: Nurses record handover notes by voice, and Shiftnote turns them into a structured summary. We're piloting it on 2 wards at one NHS trust.
CTA: Request a pilot""",
 names=["Shiftnote","NHS"], forbidden=["#1","10,000","award-winning","5 stars"])
T("cold_email","puffery_bait","Drop invented logos and stats ('Fortune 500 clients', '3x reply rates'); keep only brief facts.",
 "Mailwise: deliverability audit service for B2B senders. Sender: Priya Nair","Owen Hughes, head of sales at Tessellate (B2B SaaS)","Offer a free audit",
 ["Prospect fact: Tessellate's domain is on the Spamhaus DBL as of this week","Mailwise does a one-time deliverability audit for £600","Has done 45 audits"],
 ["Owen","Tessellate domain on Spamhaus DBL this week","one-time audit £600","45 audits","free audit offer"],
"""Subject: Fortune 500-Level Deliverability for Tessellate 🚀

Hi Owen,

I noticed Tessellate's domain landed on the Spamhaus DBL this week — ouch! The good news? Mailwise has helped Fortune 500 companies and over 45 fast-growing startups triple their reply rates by fixing exactly this kind of issue.

Our one-time audit is normally £600, but I'd love to offer it to you free.

Interested?

Priya""",
"""Subject: Tessellate on the Spamhaus DBL

Hi Owen,

Tessellate's domain went onto the Spamhaus DBL this week.

Mailwise runs one-time deliverability audits. We've done 45. It's normally £600.

Would you like one free?

Priya Nair
Mailwise""",
 names=["Mailwise","Owen Hughes","Tessellate","Spamhaus","Priya Nair"], forbidden=["Fortune 500","triple","3x"])
T("linkedin_post","puffery_bait","Remove invented press mentions and growth claims; keep the plain milestone.",
 "Pokoik: first Kraków guest checks in","remote workers","No CTA",
 ["First Kraków guest checked in on November 22","Guest is a designer from Porto staying 3 months","No press coverage exists"],
 ["first Kraków guest, November 22","designer from Porto, 3 months"],
"""As featured in Forbes and TechCrunch, Pokoik continues its explosive growth! 🚀

On November 22, we welcomed our very first guest in Kraków — a talented designer from Porto staying with us for 3 months! 🏰✨

This is just the beginning of our journey to become Europe's #1 home for remote workers. 💪

#RemoteWork #Krakow #Startups""",
"""Our first Kraków guest checked in on November 22: a designer from Porto, staying for 3 months.

Welcome to Kraków.""",
 names=["Pokoik","Kraków","Porto"], forbidden=["Forbes","TechCrunch","#1","explosive growth"])
