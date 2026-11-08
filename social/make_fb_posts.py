import json, csv, datetime, re, sys
repo = sys.argv[1]
P = json.load(open(f'{repo}/data/products.json', encoding='utf-8'))
R = json.load(open(f'{repo}/data/sales_rank.json'))['order']
rk = {i: n for n, i in enumerate(R)}
EXCLUDE = {'6.04.001'}  # add-on services listing

def key(p): return (rk.get(p['id'], 9999), p['no'])
Q = sorted([p for p in P if p['occasion'] == 'quinceanera-sweet-16'], key=key)
C = sorted([p for p in P if p['occasion'] != 'quinceanera-sweet-16' and p['no'] not in EXCLUDE], key=key)

def occasion_phrase(p):
    n = p['name'].lower(); o = p['occasion']
    if o == 'quinceanera-sweet-16' or 'quince' in n: return 'a quinceañera or sweet 16'
    if o == 'birthday-baby':
        if any(k in n for k in ('first', 'onederland', 'one', 'baby')): return 'a first birthday'
        if 'all occasions' in n: return 'any celebration'
        return 'a birthday party'
    if o == 'wedding-anniversary':
        if '50th' in n or 'anniversary' in n: return 'a 50th wedding anniversary'
        if 'all occasions' in n: return 'any celebration'
        return 'a wedding'
    if o == 'bat-bar-mitzvah': return 'a bat or bar mitzvah'
    if o == 'graduation': return 'a graduation party'
    if 'all occasions' in n: return 'any celebration'
    if 'birthday' in n: return 'a birthday party'
    if 'winter' in n: return 'a winter wonderland party'
    return 'your celebration'

HOOKS = {
 'slideshows': ["Their story, from baby photos to today, on the big screen.",
                "The moment the lights go down and the slideshow starts.",
                "A photo slideshow guests will remember long after the party.",
                "The easiest way to make a slideshow that looks professional.",
                "Every photo, every memory, set to music in one video."],
 'save-the-dates': ["Tell everyone the date first, in style.",
                    "Send the save the date before the invitations go out.",
                    "A save the date guests will actually watch.",
                    "Big day coming? Let family and friends save the date."],
 'video-invitations': ["An invitation guests open right away.",
                       "Invite everyone with a video, straight to their phone.",
                       "No printing, no postage: send the invitation by text.",
                       "A musical invitation that sets the mood for the party."],
 'website-invitations': ["One link with every party detail your guests need.",
                         "Guests open one link and see everything.",
                         "A website invitation that is easy to share and easy to read."],
 'printable-invitations': ["A classic invitation you can print or send.",
                           "Print it at home or send it by phone, your choice.",
                           "An elegant invitation you can edit in minutes."],
 'invitations-save-the-dates': ["Invitations and save the dates in one bright design.",
                                "Get guests excited from the very first message."],
 'save-the-date-teasers': ["A short video teaser to announce the big day.",
                           "Build excitement with a save the date teaser."],
 'screen-displays-banners': ["Put a welcome on the big screen at the party.",
                             "Turn the venue TV into part of the decor."],
 'signs-boards-decor': ["The finishing touch for your party setup.",
                        "Matching signs make the whole party feel planned."],
}

def body(p):
    o = occasion_phrase(p); t = p['type']
    if t == 'slideshows':
        return f"An editable photo slideshow for {o}. Add your photos, names and music in Canva, edit it yourself in minutes and download the video to play at the party."
    if t == 'save-the-dates':
        return f"An animated save the date for {o}. Add the name, date and place in Canva, then send it by text, WhatsApp or social media."
    if t == 'video-invitations':
        return f"An animated video invitation for {o}. Add all the party details in Canva, edit it yourself in minutes and send it to guests by text or WhatsApp."
    if t == 'website-invitations':
        return f"A website invitation for {o}. Guests open one link to see all the party details. Edit it yourself in Canva and share the link by text, WhatsApp or QR code."
    if t == 'printable-invitations':
        return f"An editable invitation for {o}. Add your details in Canva, then print it at home or at a print shop, or send it digitally."
    if t == 'invitations-save-the-dates':
        return f"An editable invitation design for {o}. Change the details in Canva in minutes, then print it or send it digitally."
    if t == 'save-the-date-teasers':
        return "A short animated save the date teaser. Add your name, date and photos in Canva and share it by text, WhatsApp or social media."
    if t == 'screen-displays-banners':
        return f"A screen display for {o}. Edit it in Canva and play it on the TV or projector at the venue."
    if t == 'signs-boards-decor' and 'passes' in p['name'].lower():
        return f"Editable party passes for {o}. Change the details in Canva, then print them or send them to guests."
    if t == 'signs-boards-decor':
        return f"An editable sign for {o}. Change the text in Canva, then print it for the welcome table or venue."
    return f"An editable Canva template for {o}."

FEAT = {'Add your photos': 'Add your own photos', 'QR code to share': 'QR code to share with guests',
        'Music included': 'Music included', 'Animated': 'Animated design', 'Online RSVP': 'Online RSVP for guests',
        'Download as MP4': 'Download as an MP4 video', 'English & Spanish': 'English and Spanish versions',
        'Countdown': 'Countdown to the big day'}

def tags(p):
    t = p['type']; n = p['name'].lower(); o = p['occasion']
    if o == 'quinceanera-sweet-16' or 'quince' in n:
        base = ['#Quinceanera', '#Sweet16', '#MisXV']
        extra = {'slideshows': ['#QuinceaneraSlideshow', '#PhotoSlideshow'], 'save-the-dates': ['#SaveTheDate', '#QuinceaneraInvitation'],
                 'video-invitations': ['#VideoInvitation', '#QuinceaneraInvitation'], 'website-invitations': ['#WebsiteInvitation', '#OnlineRSVP'],
                 'printable-invitations': ['#PrintableInvitation', '#QuinceaneraInvitation']}.get(t, ['#QuinceaneraParty'])
    elif o == 'birthday-baby':
        base = ['#FirstBirthday', '#OneYearOld'] if occasion_phrase(p) == 'a first birthday' else ['#BirthdayParty', '#HappyBirthday']
        extra = {'slideshows': ['#BirthdaySlideshow', '#PhotoSlideshow'], 'video-invitations': ['#BirthdayInvitation', '#VideoInvitation'],
                 'printable-invitations': ['#BirthdayInvitation', '#PrintableInvitation']}.get(t, ['#PartyIdeas'])
    elif o == 'wedding-anniversary':
        base = ['#50thAnniversary', '#GoldenAnniversary'] if 'anniversary' in occasion_phrase(p) else ['#Wedding', '#WeddingIdeas']
        extra = {'slideshows': ['#WeddingSlideshow', '#PhotoSlideshow'], 'save-the-dates': ['#SaveTheDate', '#WeddingSaveTheDate'],
                 'website-invitations': ['#WeddingWebsite', '#OnlineRSVP'], 'printable-invitations': ['#WeddingInvitation', '#PrintableInvitation'],
                 'video-invitations': ['#VideoInvitation', '#AnniversaryParty']}.get(t, ['#WeddingInvitation'])
    elif o == 'bat-bar-mitzvah':
        base = ['#BatMitzvah', '#BarMitzvah']
        extra = ['#MitzvahMontage', '#PhotoSlideshow'] if t == 'slideshows' else ['#BatMitzvahInvitation', '#NeonParty']
    elif o == 'graduation':
        base = ['#GraduationParty', '#ClassOf2027']; extra = ['#GraduationInvitation', '#WebsiteInvitation']
    else:
        base = ['#PartyDecor', '#PartyIdeas']
        extra = {'save-the-date-teasers': ['#SaveTheDate', '#VideoTeaser'], 'screen-displays-banners': ['#PartyScreen', '#EventDecor'],
                 'signs-boards-decor': ['#PartySigns', '#EventDecor']}.get(t, ['#EventDecor'])
    return ' '.join(base + extra + ['#CanvaTemplate', '#DigipodStudio'])

def caption(p, i, top):
    hooks = HOOKS.get(p['type'], ["A ready-made design you can edit yourself."])
    lines = [hooks[i % len(hooks)], '', p['name'] + (' (one of our best sellers)' if top else '')]
    lines.append(body(p)); lines.append('')
    feats = [FEAT[f] for f in p['features'] if f in FEAT]
    if p.get('slides'): feats.insert(0, f"{p['slides']} slides")
    feats += ['Edit it yourself in Canva', 'Instant digital download']
    lines += ['• ' + f for f in feats]
    lines += ['', 'Shop it on Etsy 👉 ' + f"https://digipodstudio.etsy.com/listing/{p['id']}", '', tags(p)]
    txt = '\n'.join(lines)
    assert '¿' not in txt and '¡' not in txt
    return txt

START = '2026-11-09'
alts = json.load(open(f'{repo}/data/images.json', encoding='utf-8'))
def post(p, i):
    return {'order': i + 1, 'no': p['no'], 'id': p['id'], 'name': p['name'],
            'etsy': f"https://digipodstudio.etsy.com/listing/{p['id']}", 'image': p['img_lg'],
            'alt': (alts.get(p['id'], {}).get('alt') or p['name']).replace('May include: ', ''),
            'caption': caption(p, i, rk.get(p['id'], 9999) < 30)}
out = {
  'note': 'Daily Facebook product posts (2 per Page per day), best sellers first. Rule: for date D in Asia/Manila (early morning posts so people in the Philippines see them when they wake up), k = days since start_date; slot s (0,1) posts item index (2k+s) mod N of that Page list, at times[s]. After the last item the list starts again from the top. Regenerate with: python3 social/make_fb_posts.py . (keeps start_date). English only.',
  'start_date': START, 'timezone': 'Asia/Manila',
  'pages': {
    'quince': {'name': 'DigipodStudio Quince', 'blogId': '7939713', 'times': ['06:00', '07:30'], 'posts': [post(p, i) for i, p in enumerate(Q)]},
    'celebrations': {'name': 'DigipodStudio Celebrations', 'blogId': '7939651', 'times': ['06:15', '07:45'], 'posts': [post(p, i) for i, p in enumerate(C)]},
  }}
json.dump(out, open(f'{repo}/social/facebook-daily-posts.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(Q), len(C))
