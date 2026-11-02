/** FeatherLM blind A/B form. Paste into script.google.com (personal Gmail), press Run, approve, then open the logged URLs. */
const PAIRS = [
 {
  "n": 1,
  "a": "Headline: Raise Responsible Kids, One Chore at a Time\n\nSubhead: Choreboard turns chores into a game your kids (ages 6–12) will actually want to play. You set the tasks, they earn points, and the habits stick. No bank card needed.\n\nFamilies love it. Kids love it more.\n\nOnly $3/month per family.\n\nCTA: Download for iOS",
  "b": "Headline: Raise Responsible Kids, One Chore at a Time\nSubhead: Choreboard helps kids ages 6 to 12 learn the value of hard work. You set the chores, they earn points for finishing them, and the routine becomes a habit they keep. No bank card needed.\nFamilies love it. Kids love it more.\nOnly $3/month per family.\nCTA: Download for iOS"
 },
 {
  "n": 2,
  "a": "Primary text: Choreboard helps you raise kids who are responsible and motivated, and it makes chores fun. You set the tasks. Your kids earn points for finishing them and save those points toward goals they actually care about. They learn what hard work is worth, and no bank card is needed. Thousands of families already use it, for $3/month.\nHeadline: Turn Chores Into Wins",
  "b": "Headline: Turn Chores Into Wins\n\nWant to raise responsible, motivated kids? Choreboard makes chores fun. You set tasks, your kids earn points, and they save toward goals they care about. It teaches the value of hard work, and no bank card is needed. Thousands of families use it for $3/month."
 },
 {
  "n": 3,
  "a": "Integrations That Work\n\nYou already use Kasirku POS. So do we. Rotaship pulls its real-time sales data straight into your scheduling, so you staff each shift based on what's actually happening, not a guess.\n\nNeed to share the schedule or run your own numbers? One click exports it to Google Sheets.\n\nFewer tools. Less friction. More time for your guests.",
  "b": "Integrations That Just Work\n\nRotaship connects to the tools you already use. The Kasirku POS integration pulls in real-time sales data, so you can staff each shift based on what's actually selling. To share or analyze a schedule, export it to Google Sheets with one click. You'll juggle fewer tools and have more time for your guests."
 },
 {
  "n": 4,
  "a": "Headline: Shift Scheduling for Restaurant Chains, Inside WhatsApp\nSubhead: Rotaship lets restaurant staff see their shifts and swap them through WhatsApp, which they already use. There is no new app to install. 140 outlets run their scheduling on it today.\nCTA: Try It Free for 30 Days",
  "b": "Headline: Smarter Scheduling for the Restaurants of Tomorrow\nSubhead: Rotaship changes how your restaurant chain manages its team. It runs on WhatsApp, so your staff can view and swap shifts without installing anything. No new apps. No missed shifts. 140 outlets already run their schedules this way.\nSimple, scalable scheduling. The future is here.\nCTA: Try It Free for 30 Days"
 },
 {
  "n": 5,
  "a": "Subject: Introducing Stackhand Status Pages\n\nHi friend,\n\nWhen something breaks, your customers should hear about it right away.\n\nStackhand Status Pages launch November 4. Each page updates in real time from the monitors you already have, so your users see what's happening during every incident without you posting updates by hand.\n\nHere's what's included:\n• Automatic updates driven by your monitors\n• Custom domain support on the Team plan\n• One free status page on a stackhand.page subdomain for Free plan users\n\nCreate your status page today so your customers know where to look when something goes wrong.\n\nBest,\nJoel Park\nFounder, Stackhand",
  "b": "Subject: Stackhand Status Pages launch November 4\n\nHi friend,\n\nYour site goes down. Your customers wonder if it's them or you. A status page answers that question before they email support.\n\nStackhand Status Pages go live November 4. They pull from the monitors you already run, so every incident shows up on your page in real time, no extra setup.\n\nWhat you get:\n• Automatic updates from your monitors\n• Custom domain support on the Team plan\n• One free status page on a stackhand.page subdomain for Free plan users\n\nSet yours up today. Your customers will notice.\n\nBest,\nJoel Park\nFounder, Stackhand"
 },
 {
  "n": 6,
  "a": "Headline: You Set the Price. Change It Anytime.\nSubhead: Shelfwise puts e-ink labels on your shelves and a pricing app in your pocket. Update a price in seconds. No paper tags, no reprinting, no mismatches at the register.\nThe battery runs 5 years. A pack of 50 labels costs $890. If you're tired of marking up tags by hand after close, start here.\nCTA: Order a Sample Pack",
  "b": "Headline: E-ink Shelf Labels for Independent Grocers\nSubhead: Shelfwise puts e-ink price labels on your shelves and connects them to a mobile app. Change a price in the app and the label updates right away. You stop printing paper tags and swapping them by hand, and fewer prices end up wrong on the shelf.\nEach label's battery lasts 5 years. Packs of 50 start at $890.\nSpend less time relabeling shelves.\nCTA: Order a Sample Pack"
 },
 {
  "n": 7,
  "a": "About Us\n\nEvery East African brand deserves a digital presence that stands with the best. That's the whole idea behind Fernway.\n\nI'm Wanjiru Kamau. I started Fernway in Nairobi in 2022, after 5 years leading e-commerce at a Kenyan fashion retailer. I watched brands struggle to move online and kept thinking there had to be a better way. So I built one.\n\nNow a team of 7 designers, developers, and strategists works with me. We've launched 31 Shopify stores, each one shaped around how East African customers actually shop.\n\nWe don't just build websites. We build futures.\n\nFixed price. 6 weeks. Unlimited potential.",
  "b": "About Us\n\nFernway Studio builds Shopify stores for East African brands.\n\nWanjiru Kamau founded the studio in Nairobi in 2022. Before that, she spent 5 years leading e-commerce at a Kenyan fashion retailer, where she saw what goes wrong when brands move online. She started Fernway to help local brands sell well on the web.\n\nThe team is now 7 people, a mix of designers, developers and strategists. Together they have launched 31 Shopify stores, built with an understanding of how the East African market works.\n\nEach project has a fixed price and takes 6 weeks."
 },
 {
  "n": 8,
  "a": "Primary text: Planning a move to Warsaw? Pokoik rents furnished apartments for stays of 1 to 6 months. You pay one all-inclusive price, with fast internet included and no hidden fees, so you can move in and get on with your life. There are 220 apartments to choose from.\nHeadline: Furnished Warsaw apartments for 1 to 6 months",
  "b": "Coming to Warsaw for a while? Pokoik rents furnished apartments for 1 to 6 months. One price covers everything, including fast internet. No hidden fees. Pick an apartment, move in, start living. There are 220 to choose from.\n\nHeadline: Your Warsaw Adventure Awaits"
 },
 {
  "n": 9,
  "a": "We hit $50K MRR.\n\n18 months. Fully bootstrapped. A team of 3.\n\nNo VC. No shortcuts. Just late nights and an obsession with our customers.\n\nIf you believed in us along the way: thank you. This is only the beginning.\n\n#IndieHackers #Bootstrapped #SaaS #BuildInPublic #MRR",
  "b": "Crateful just crossed $50K MRR.\n\nIt took 18 months, with no outside funding and a team of three. We didn't raise from VCs or take shortcuts. We kept our attention on customers and worked a lot of late nights.\n\nTo everyone who believed in us, thank you. We're only getting started.\n\n#IndieHackers #Bootstrapped #SaaS #BuildInPublic #MRR"
 },
 {
  "n": 10,
  "a": "Headline: You're Billing Fewer Hours Than You Work\nSubhead: Chasing timesheets? Stop. Tabwise pulls your team's work straight from Google Calendar and Jira, so nothing slips through. Agencies using it recover an average of 3.2 billable hours per person, every single week.\nMore accuracy. More revenue. Less admin.\nCTA: Start Free Today",
  "b": "Headline: Find the Billable Hours Your Agency Is Missing\nSubhead: Tabwise tracks time for you. It pulls your team's work straight from Google Calendar and Jira, so no one has to chase timesheets and no hours go unrecorded. Agencies using Tabwise recover an average of 3.2 billable hours per person each week.\nYour records get more accurate, you bill for more of the work, and your team spends less time on admin.\nCTA: Start Free Today"
 }
];
function createForm() {
  const form = FormApp.create('Which one would you send? (2-minute blind test)');
  form.setDescription('Two rewrites of the same marketing copy, 10 times. Pick the one you would actually send to a customer. No right answers, and you do not know which system wrote which. Thank you!');
  form.setCollectEmail(false); try { form.setRequireLogin(false); } catch (e) { Logger.log('Could not open the form to people outside the organisation: ' + e); } form.setLimitOneResponsePerUser(false); form.setShowLinkToRespondAgain(false);
  PAIRS.forEach(p => {
    form.addSectionHeaderItem().setTitle('Pair ' + p.n + ' of 10').setHelpText('A)\n' + p.a + '\n\nB)\n' + p.b);
    form.addMultipleChoiceItem().setTitle('Pair ' + p.n + ': which would you send?')
      .setChoiceValues(['A', 'B', 'Both fine', 'Neither']).setRequired(true);
  });
  form.addParagraphTextItem().setTitle('Anything that made one sound more human? (optional)');
  const sheet = SpreadsheetApp.create('FeatherLM A/B responses');
  form.setDestination(FormApp.DestinationType.SPREADSHEET, sheet.getId());
  Logger.log('SHARE THIS LINK: ' + form.getPublishedUrl());
  Logger.log('Edit form: ' + form.getEditUrl());
  Logger.log('Responses sheet: ' + sheet.getUrl());
}
