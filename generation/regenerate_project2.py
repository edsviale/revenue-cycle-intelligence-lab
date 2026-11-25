#!/usr/bin/env python3
from __future__ import annotations
import csv, random, math, statistics, zlib, json
from pathlib import Path
from datetime import date, timedelta
from collections import Counter, defaultdict

SEED = 20260915
REPORT_DATE = date(2026,9,15)
DOS_START = date(2025,9,1)
DOS_END = date(2026,8,31)
N_CLAIMS = 3000
SRC = Path('/mnt/data/project2_source_package')
OUT = Path('/mnt/data/project2_regenerated')
OUT.mkdir(parents=True, exist_ok=True)
rng = random.Random(SEED)

# ---------- utilities ----------
def read_csv(path):
    with open(path, encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def write_csv(path, rows, fieldnames):
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        w=csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        w.writeheader(); w.writerows(rows)

def dstr(d): return d.isoformat() if isinstance(d,date) else (d or '')
def money(x): return round(max(0.0,float(x)),2)
def weighted_choice(items, weights): return rng.choices(items, weights=weights, k=1)[0]
def stable_rng(key): return random.Random(SEED + zlib.crc32(str(key).encode()))
def clamp(x,a,b): return max(a,min(b,x))
def yes(p): return rng.random() < p

def sample_bounded_lognormal(median, mn, mx):
    # right-skewed, bounded, whole-minute duration
    sigma=.42
    val=rng.lognormvariate(math.log(median), sigma)
    return int(round(clamp(val,mn,mx)))

def month_weight(d):
    # mild operational seasonality; modest December elective dip, not a denial multiplier
    w={1:1.00,2:.98,3:1.02,4:1.02,5:1.03,6:1.01,7:.98,8:.99,9:1.02,10:1.03,11:.99,12:.86}
    return w[d.month]

def random_service_date():
    days=(DOS_END-DOS_START).days+1
    # rejection sample against monthly weights
    while True:
        d=DOS_START+timedelta(days=rng.randrange(days))
        if rng.random() <= month_weight(d)/1.03:
            return d

# ---------- source scaffolding ----------
src_claims=read_csv(SRC/'Claims.csv')
src_lines=read_csv(SRC/'Claim_Lines.csv')

# Provider/facility/payer universes and empirical conditional distributions from original synthetic package.
providers={r['Provider Code']:{'name':r['Provider Name'],'type':r['Provider Type']} for r in src_claims}
locations={r['Location Code']:{'name':r['Location Name'],'setting':r['Setting'],'county':r['County'],'locality':r['Medicare Locality']} for r in src_claims}

# provider affiliations by location from original design
prov_by_loc=defaultdict(Counter)
proc_by_loc=defaultdict(Counter)
payer_by_loc_proc=defaultdict(Counter)
payer_by_loc=defaultdict(Counter)
payers={}
for r in src_claims:
    prov_by_loc[r['Location Code']][r['Provider Code']]+=1
    proc_by_loc[r['Location Code']][r['Procedure Group']]+=1
    payer_by_loc_proc[(r['Location Code'],r['Procedure Group'])][r['Payer Code']]+=1
    payer_by_loc[r['Location Code']][r['Payer Code']]+=1
    payers[r['Payer Code']]={'name':r['Payer Name'],'ar':r['AR Type'],'arch':r['Payer Archetype'],'basis':r['Reimbursement Basis'],'filing':int(float(r['Modeled Filing Limit Days']))}

loc_weights=Counter(r['Location Code'] for r in src_claims)

# CPT empirical weights by procedure group and canonical base units
cpt_by_proc=defaultdict(Counter)
base_units={}
for r in src_claims:
    cpt_by_proc[r['Procedure Group']][r['Primary CPT']]+=1
    base_units[r['Primary CPT']]=int(float(r['CMS Base Units']))

DUR={
'00100':(75,30,180),'00142':(45,20,90),'00145':(90,45,180),'00160':(75,30,150),'00170':(60,25,120),
'00300':(90,35,240),'00400':(100,40,240),'00520':(75,30,180),'00532':(45,20,90),'00630':(120,60,240),
'00670':(240,120,480),'00731':(35,15,75),'00732':(75,30,180),'00811':(40,20,90),'00812':(35,20,75),
'00813':(55,25,120),'00910':(45,20,90),'00912':(70,30,150),'00914':(120,60,240),'00918':(75,30,150),
'01210':(90,45,180),'01214':(150,90,300),'01380':(90,45,180),'01400':(90,45,180),'01402':(150,90,300),
'01464':(75,35,150),'01470':(90,40,180),'01480':(110,50,240),'01610':(75,35,150),'01620':(90,40,180),
'01630':(110,50,240),'01710':(75,30,150),'01810':(60,25,120),'01820':(75,30,150),'01830':(100,45,210),
'01991':(45,20,90),'01992':(60,30,120)}

SECONDARY_ALLOWED={'64415':900,'64447':950,'64450':650,'64483':1100,'76942':300}
SECONDARY_MOD={'64415':'XU','64447':'XU','64450':'XU','64483':'XU','76942':'26'}

# Payer admin profile: auth %, filing, eligibility mult, bundling mult, COB mult, docs mult
ADMIN={
'Commercial PPO/POS':(.25,180,1.00,1.00,1.00,1.00),'HMO/EPO':(.45,120,1.15,1.10,1.05,1.05),
'Exchange':(.35,120,1.25,1.00,1.15,1.00),'Medicare FFS':(.05,365,.80,1.20,1.30,1.15),
'Medicare Advantage':(.35,120,1.00,1.20,1.15,1.15),'Medi-Cal FFS':(.20,180,1.25,1.00,1.10,1.10),
'Medi-Cal Managed':(.45,120,1.35,1.05,1.20,1.15),'Workers Compensation':(.60,365,1.10,.90,.70,1.30),
'Other Eligible':(.25,180,1.10,1.00,1.00,1.00),'Other Medicaid':(.25,180,1.10,1.00,1.00,1.00)}

# Fixed seeded synthetic reimbursement profile per payer.
payer_contract={}
for code,p in payers.items():
    rr=stable_rng(code)
    a=p['arch']
    if a=='Commercial PPO/POS': payer_contract[code]=('cf',rr.uniform(58,72))
    elif a=='HMO/EPO': payer_contract[code]=('cf',rr.uniform(48,62))
    elif a=='Exchange': payer_contract[code]=('cf',rr.uniform(46,58))
    elif a=='Medicare Advantage': payer_contract[code]=('medicare_pct',rr.uniform(1.05,1.20))
    elif a=='Medi-Cal Managed': payer_contract[code]=('medicaid_pct',rr.uniform(1.05,1.25))
    elif a=='Other Medicaid': payer_contract[code]=('medicaid_pct',rr.uniform(.90,1.10))
    elif a=='Other Eligible': payer_contract[code]=('cf',rr.uniform(45,58))

MEDICARE_CF={2025:{'Area 18':21.22,'Area 17':20.88,'Area 62':20.71},2026:{'Area 18':21.26,'Area 17':20.99,'Area 62':20.88}}
WC_CF={2025:{'Area 18':31.27,'Area 17':30.77,'Area 62':30.51},2026:{'Area 18':32.09,'Area 17':31.68,'Area 62':31.52}}

# Diagnosis categories/codes are synthetic but formatted and procedure-sensitive.
DX={
'GI':[('K21.9','GERD'),('K63.5','Colon polyp'),('R10.9','Abdominal pain')],
'Ortho':[('M17.10','Knee osteoarthritis'),('M16.10','Hip osteoarthritis'),('S83.209A','Meniscal injury')],
'Spine':[('M54.16','Lumbar radiculopathy'),('M48.061','Lumbar stenosis')],
'Urology':[('N20.0','Kidney stone'),('N40.1','BPH'),('N32.89','Bladder disorder')],
'ENT':[('J34.2','Deviated septum'),('J35.01','Chronic tonsillitis')],
'Ophth':[('H25.10','Cataract'),('H33.20','Retinal detachment')],
'Plastic':[('L98.9','Skin disorder'),('C44.90','Skin cancer')],
'General':[('K40.90','Inguinal hernia'),('K80.20','Cholelithiasis'),('R22.9','Localized swelling')],
'Hand':[('G56.00','Carpal tunnel syndrome'),('M65.30','Trigger finger')],
'Foot':[('M20.10','Hallux valgus'),('M72.2','Plantar fascial disorder')],
'Pain':[('M54.16','Lumbar radiculopathy'),('M54.12','Cervical radiculopathy')]}
DX['Orthopedic']=DX['Ortho']
DX['Ophthalmology']=DX['Ophth']
DX['Hospital/General']=DX['General']

SCEN={
'DEN01':('PR','26','','Eligibility / Coverage','Coverage effective after DOS','Patient Access / Eligibility','Yes','Coverage_COB'),
'DEN02':('PR','27','','Eligibility / Coverage','Coverage terminated before DOS','Patient Access / Eligibility','Yes','Coverage_COB'),
'DEN03':('PR','31','','Eligibility / Coverage','Member information mismatch','Patient Access / Eligibility','Yes','Coverage_COB'),
'DEN04':('PR','31','','Payer / Processing Issue','Payer eligibility file incorrect or delayed','Payer','No','Coverage_COB'),
'DEN05':('CO','197','','Authorization / Precertification','Required authorization not obtained','Authorization','Yes','Authorizations'),
'DEN06':('CO','198','N54','Authorization / Precertification','Authorized CPT/service mismatch','Authorization','Yes','Authorizations'),
'DEN07':('CO','210','','Authorization / Precertification','Authorization outside valid timeframe','Authorization','Yes','Authorizations'),
'DEN08':('CO','16','N54','Authorization / Precertification','Authorized provider/location mismatch','Authorization','Yes','Authorizations'),
'DEN09':('CO','4','','Coding / Modifier','Incorrect or missing modifier','Coding / Billing','Yes','Claim_Lines'),
'DEN10':('CO','5','','Coding / Modifier','Procedure/place-of-service mismatch','Coding / Billing','Yes','Claim_Lines'),
'DEN11':('CO','11','','Coding / Modifier','Diagnosis inconsistent with procedure','Coding','Yes','Claims'),
'DEN12':('CO','16','M76','Missing Information / Documentation','Missing/incomplete/invalid diagnosis','Coding / Billing','Yes','Claims'),
'DEN13':('CO','16','M53','Missing Information / Documentation','Missing/invalid units','Coding / Billing','Yes','Claim_Lines'),
'DEN14':('CO','16','N286','Missing Information / Documentation','Referring provider identifier missing or invalid','Billing / Claims','Yes','Claims'),
'DEN15':('CO','252','M127','Missing Information / Documentation','Required records not submitted','Documentation / Billing','Context-dependent','Claims'),
'DEN16':('CO','50','','Medical Necessity','Service not medically necessary under modeled rule','Clinical Documentation / Coding','Context-dependent','Claims'),
'DEN17':('CO','151','','Medical Necessity','Frequency/number of services not supported','Clinical Documentation / Utilization Review','Context-dependent','Claims'),
'DEN18':('PR','22','','COB / Wrong Payer','Other insurance primary','Patient Access / Eligibility / COB','Yes','Coverage_COB'),
'DEN19':('PR','109','','COB / Wrong Payer','Claim submitted to wrong payer','Billing / Claims','Yes','Coverage_COB'),
'DEN20':('CO','18','','Duplicate Claim','Unnecessary duplicate resubmission','Billing / Claims','Yes','Claim_Submissions'),
'DEN21':('CO','18','','Payer / Processing Issue','Payer incorrectly classified legitimate submission as duplicate','Payer','No','Claim_Submissions'),
'DEN22':('CO','29','','Timely Filing','Filing limit exceeded','Billing / Claims','Yes','Claims'),
'DEN23':('CO','97','','Bundling','Correctly bundled secondary service','Contractual Payment Logic','No','Claim_Lines'),
'DEN24':('CO','97','','Payer / Processing Issue','Payer incorrectly bundled separately payable service','Payer','No','Claim_Lines'),
'DEN25':('CO','96','N130','Non-Covered Service','Modeled benefit exclusion','Coverage / Benefit Design','No','Claims'),
'DEN26':('CO','204','','Non-Covered Service','Member-specific benefit exclusion','Coverage / Benefit Design','No','Claims')}
REC={
'DEN01':(.55,30),'DEN02':(.45,35),'DEN03':(.90,18),'DEN04':(.90,28),'DEN05':(.55,35),'DEN06':(.65,28),'DEN07':(.45,40),'DEN08':(.85,20),
'DEN09':(.93,14),'DEN10':(.85,18),'DEN11':(.75,24),'DEN12':(.90,18),'DEN13':(.92,16),'DEN14':(.88,18),'DEN15':(.82,25),
'DEN16':(.55,42),'DEN17':(.45,45),'DEN18':(.80,35),'DEN19':(.88,30),'DEN20':(0,7),'DEN21':(.90,22),'DEN22':(.20,60),'DEN23':(0,10),'DEN24':(.65,35),'DEN25':(.35,40),'DEN26':(.10,20)}

CATEGORY_WEIGHTS={
'Eligibility':18.0,'Authorization':9.4,'Coding':15.3,'Missing':17.5,'MedNec':1.9,'COB':11.6,'Duplicate':4.8,'Timely':1.3,'Bundling':3.8,'NonCovered':8.3,'Payer':8.1}
SCEN_BY_CAT={
'Eligibility':(['DEN01','DEN02','DEN03'],[.25,.35,.40]),
'Authorization':(['DEN05','DEN06','DEN07','DEN08'],[.45,.20,.15,.20]),
'Coding':(['DEN09','DEN10','DEN11'],[.50,.25,.25]),
'Missing':(['DEN12','DEN13','DEN14','DEN15'],[.30,.35,.20,.15]),
'MedNec':(['DEN16','DEN17'],[.70,.30]),'COB':(['DEN18','DEN19'],[.65,.35]),
'Duplicate':(['DEN20'],[1]),'Timely':(['DEN22'],[1]),'Bundling':(['DEN23'],[1]),
'NonCovered':(['DEN25','DEN26'],[.60,.40]),'Payer':(['DEN04','DEN21','DEN24'],[.35,.30,.35])}

# ---------- reimbursement ----------
def medicaid_time_units(minutes):
    full=minutes//15; rem=minutes%15
    return full + (1 if rem>=5 else 0)

def expected_allowed(payer_code, provider_type, base, minutes, locality, dos, gross):
    p=payers[payer_code]; arch=p['arch']
    if arch=='Medicare FFS':
        val=(base+minutes/15.0)*MEDICARE_CF[dos.year][locality]
    elif arch=='Medi-Cal FFS':
        tu=medicaid_time_units(minutes)
        val=(base+tu)*14.01 if provider_type=='Anesthesiologist' else ((base-1)+tu)*11.02
    elif arch=='Workers Compensation':
        yr=2025 if dos < date(2026,3,1) else 2026
        tu=round(minutes/15.0,1)
        val=(base+tu)*WC_CF[yr][locality]
    else:
        mode,x=payer_contract[payer_code]
        if mode=='cf': val=(base+minutes/15.0)*x
        elif mode=='medicare_pct': val=(base+minutes/15.0)*MEDICARE_CF[dos.year][locality]*x
        else:
            tu=medicaid_time_units(minutes)
            baseline=(base+tu)*14.01 if provider_type=='Anesthesiologist' else ((base-1)+tu)*11.02
            val=baseline*x
    return money(min(gross,val))

def secondary_allowed(cpt,payer_code):
    # synthetic but deterministic payer factor for secondary lines; preserve billed >= allowed
    base=SECONDARY_ALLOWED[cpt]
    rr=stable_rng('sec-'+payer_code)
    factor=rr.uniform(.35,.62)
    if payers[payer_code]['arch'] in ('Medicare FFS','Medi-Cal FFS','Workers Compensation'): factor=rr.uniform(.28,.48)
    return money(base*factor)

# ---------- generation ----------
claims=[]; lines=[]; submissions=[]; authorizations=[]; coverages=[]; denials=[]
claim_map={}; line_map={}; auth_map={}; cov_map={}; subs_by_claim=defaultdict(list); denials_by_claim=defaultdict(list)

loc_codes=list(loc_weights); loc_w=[loc_weights[x] for x in loc_codes]

for i in range(1,N_CLAIMS+1):
    cid=f'CLM{200000+i:06d}'; account=f'A{200000+rng.randrange(800000):06d}'
    dos=random_service_date()
    loc=weighted_choice(loc_codes,loc_w); L=locations[loc]
    pc=prov_by_loc[loc]; provider=weighted_choice(list(pc),list(pc.values())); P=providers[provider]
    prc=proc_by_loc[loc]; proc=weighted_choice(list(prc),list(prc.values()))
    cc=cpt_by_proc[proc]; cpt=weighted_choice(list(cc),list(cc.values()))
    med,mn,mx=DUR.get(cpt,(75,30,180)); mins=sample_bounded_lognormal(med,mn,mx); base=base_units[cpt]
    pctr=payer_by_loc_proc.get((loc,proc)) or payer_by_loc[loc]; payer=weighted_choice(list(pctr),list(pctr.values())); PAY=payers[payer]
    auth_pct, filing, elig_mult, bund_mult, cob_mult, doc_mult=ADMIN[PAY['arch']]
    submit=dos+timedelta(days=rng.randint(2,14))
    # tiny timely-filing defect pool generated later may override submission date while remaining <= report
    adj_delay=rng.randint(10,38)
    true_adj=submit+timedelta(days=adj_delay)
    visible_adj=true_adj if true_adj<=REPORT_DATE else None

    gross=round((base+mins/15.0)*140,0)
    allowed=expected_allowed(payer,P['type'],base,mins,L['locality'],dos,gross)
    dx,dxcat=rng.choice(DX[proc])
    doc_required = proc in ('Spine','Pain') or yes(.08*doc_mult)
    med_review = proc in ('Pain','Spine') and yes(.35)
    referring_required = proc in ('Pain','Spine') and yes(.30)
    prior_similar = rng.choices([0,1,2,3,4],weights=[60,23,10,5,2])[0]
    auth_required=yes(auth_pct)
    auth_id=f'AUTH{i:06d}' if auth_required else ''
    cov_id=f'COV{i:06d}'

    row={
      'Claim ID':cid,'Account':account,'Service Date':dstr(dos),'Submit Date':dstr(submit),'Initial Adjudication Date':dstr(visible_adj),
      'Provider Code':provider,'Provider Name':P['name'],'Provider Type':P['type'],'Modifier':'AA' if P['type']=='Anesthesiologist' else 'QZ',
      'Location Code':loc,'Location Name':L['name'],'Setting':L['setting'],'County':L['county'],'Medicare Locality':L['locality'],
      'Procedure Group':proc,'Primary CPT':cpt,'Anesthesia Minutes':mins,'CMS Base Units':base,'Internal Anesthesia Units':round(base+mins/15.0,1),
      'Payer Code':payer,'Payer Name':PAY['name'],'AR Type':PAY['ar'],'Payer Archetype':PAY['arch'],
      'Reimbursement Basis':('CA OMFS DWC Table A' if PAY['arch']=='Workers Compensation' else PAY['basis']),
      'Modeled Filing Limit Days':filing,'Gross Billed Amount':money(gross),'Expected Allowed Amount':allowed,
      'Initial Claim Status':'Pending' if not visible_adj else 'Paid','Initial Paid Amount':0 if not visible_adj else allowed,'Initial Denied Amount':0,
      'Unique Revenue at Risk':0,'Final Paid Amount':0 if not visible_adj else allowed,'Final Balance':allowed if not visible_adj else 0,
      'Final Claim Status':'Pending' if not visible_adj else 'Paid','Denial Event Count':0,'Has Denial':'No','Claim Preventable':'No','Report Date':dstr(REPORT_DATE),
      'Primary Diagnosis Code':dx,'Diagnosis Category':dxcat,'Documentation Required':'Yes' if doc_required else 'No','Documentation Status':'Complete' if doc_required else 'Not Required',
      'Referring Provider Required':'Yes' if referring_required else 'No','Referring Provider ID':('NPI'+str(1000000000+rng.randrange(8999999999))) if referring_required else '',
      'Referring Provider ID Valid':'Yes' if referring_required else 'N/A','Medical Necessity Review Required':'Yes' if med_review else 'No','Prior Similar Service Count':prior_similar,
      'Authorization Required':'Yes' if auth_required else 'No','Authorization ID':auth_id}
    claims.append(row); claim_map[cid]=row

    # Primary line
    lid=f'{cid}-01'
    correct_mod=row['Modifier']; time_units=round(mins/15.0,1)
    if PAY['arch'] in ('Medi-Cal FFS','Medi-Cal Managed','Other Medicaid'): correct_time=medicaid_time_units(mins)
    elif PAY['arch']=='Workers Compensation': correct_time=round(mins/15.0,1)
    else: correct_time=round(mins/15.0,2)
    lr={'Claim Line ID':lid,'Claim ID':cid,'Line Number':1,'Service Date':dstr(dos),'Provider Code':provider,'Provider Name':P['name'],
        'Location Code':loc,'Location Name':L['name'],'Payer Code':payer,'Payer Name':PAY['name'],'Payer Archetype':PAY['arch'],'Procedure Group':proc,
        'Line Type':'Primary Anesthesia','Submitted CPT':cpt,'Correct CPT':cpt,'Submitted Modifier':correct_mod,'Correct Modifier':correct_mod,
        'Submitted Setting':L['setting'],'Correct Setting':L['setting'],'Anesthesia Minutes':mins,'Submitted Base Units':base,'Correct Base Units':base,
        'Submitted Time Units':correct_time,'Correct Time Units':correct_time,'Submitted Total Units':round(base+float(correct_time),2),'Correct Total Units':round(base+float(correct_time),2),
        'Coding Defect Type':'None','Bundling Eligible':'No','Bundling Relationship ID':'','Gross Billed Amount':money(gross),'Expected Allowed Amount':allowed,
        'Initial Paid Amount':0 if not visible_adj else allowed,'Initial Denied Amount':0,'Unique Line Revenue at Risk':0,'Final Paid Amount':0 if not visible_adj else allowed,'Final Line Status':'Pending' if not visible_adj else 'Paid'}
    lines.append(lr); line_map[lid]=lr

    # Secondary line generation
    sec_lines=[]
    if proc in ('Ortho','Orthopedic','Hand','Foot','Spine') and yes(.12):
        if proc=='Spine': scpt='64483'
        elif proc=='Hand': scpt=rng.choice(['64415','64450'])
        elif proc in ('Ortho','Orthopedic'): scpt=rng.choice(['64415','64447','64450'])
        else: scpt=rng.choice(['64447','64450'])
        sec_lines.append(scpt)
        if scpt in ('64415','64447','64450') and yes(.70): sec_lines.append('76942')
    for j,scpt in enumerate(sec_lines,start=2):
        slid=f'{cid}-{j:02d}'; sgross=SECONDARY_ALLOWED[scpt]; sallow=secondary_allowed(scpt,payer)
        sl={'Claim Line ID':slid,'Claim ID':cid,'Line Number':j,'Service Date':dstr(dos),'Provider Code':provider,'Provider Name':P['name'],
            'Location Code':loc,'Location Name':L['name'],'Payer Code':payer,'Payer Name':PAY['name'],'Payer Archetype':PAY['arch'],'Procedure Group':proc,
            'Line Type':'Ultrasound Guidance' if scpt=='76942' else 'Regional Block / Injection','Submitted CPT':scpt,'Correct CPT':scpt,'Submitted Modifier':SECONDARY_MOD[scpt],'Correct Modifier':SECONDARY_MOD[scpt],
            'Submitted Setting':L['setting'],'Correct Setting':L['setting'],'Anesthesia Minutes':'','Submitted Base Units':'','Correct Base Units':'','Submitted Time Units':'','Correct Time Units':'','Submitted Total Units':1,'Correct Total Units':1,
            'Coding Defect Type':'None','Bundling Eligible':'Yes','Bundling Relationship ID':f'BND-{cid}','Gross Billed Amount':money(sgross),'Expected Allowed Amount':sallow,
            'Initial Paid Amount':0 if not visible_adj else sallow,'Initial Denied Amount':0,'Unique Line Revenue at Risk':0,'Final Paid Amount':0 if not visible_adj else sallow,'Final Line Status':'Pending' if not visible_adj else 'Paid'}
        lines.append(sl); line_map[slid]=sl
        row['Gross Billed Amount']=money(row['Gross Billed Amount']+sgross); row['Expected Allowed Amount']=money(row['Expected Allowed Amount']+sallow)
        if visible_adj: row['Initial Paid Amount']=row['Expected Allowed Amount']; row['Final Paid Amount']=row['Expected Allowed Amount']
        else: row['Final Balance']=row['Expected Allowed Amount']

    # Coverage record: initially valid; denial defects may mutate later.
    cov={'Coverage COB ID':cov_id,'Claim ID':cid,'Service Date':dstr(dos),'Billed Payer Code':payer,'Billed Payer Name':PAY['name'],
         'Primary Payer Code':payer,'Primary Payer Name':PAY['name'],'Secondary Payer Code':'','Secondary Payer Name':'','Expected Responsible Payer Code':payer,'Expected Responsible Payer Name':PAY['name'],
         'Other Active Coverage':'No','COB Sequence':'Primary','Coverage Effective Date':dstr(dos-timedelta(days=rng.randint(90,900))),
         'Coverage Termination Date':'','Eligibility Check Date':dstr(max(dos-timedelta(days=rng.randint(1,7)),DOS_START)),'Eligibility Check Result':'Active','Member Information Match':'Yes','Eligibility Defect Type':'None','Payer Eligibility File Error':'No','Report Date':dstr(REPORT_DATE)}
    coverages.append(cov); cov_map[cid]=cov

    # Authorization record only if required. Initially valid.
    if auth_required:
        auth={'Authorization ID':auth_id,'Claim ID':cid,'Payer Code':payer,'Payer Name':PAY['name'],'Authorization Required':'Yes','Authorization Obtained':'Yes','Authorization Number':'PA'+str(100000+rng.randrange(900000)),
              'Authorization Start Date':dstr(dos-timedelta(days=15)),'Authorization End Date':dstr(dos+timedelta(days=30)),'Authorized Provider Code':provider,'Authorized Location Code':loc,'Authorized CPT':cpt,'Submitted CPT':cpt,
              'Authorization Match Status':'Match','Mismatch Type':'None','Authorization Status':'Valid','Retro Authorization Requested':'No','Retro Authorization Outcome':'N/A','Report Date':dstr(REPORT_DATE)}
        authorizations.append(auth); auth_map[cid]=auth

    # Original submission only if it exists by snapshot.
    if submit<=REPORT_DATE:
        sid=f'SUB-{cid}-01'
        sr={'Submission ID':sid,'Claim ID':cid,'Submission Number':1,'Submission Date':dstr(submit),'Submission Type':'Original','Submission Reason':'Initial claim submission','Trigger Denial Event ID':'','Resulting Denial Event ID':'','Submission Outcome':'Pending' if not visible_adj else 'Accepted / Adjudicated','Payer Code':payer,'Payer Name':PAY['name'],'Claim Frequency Type':'1 - Original','Was Duplicate Submission':'No','Duplicate Of Submission ID':'','Corrected Fields':'','Days Since Prior Submission':'','Report Date':dstr(REPORT_DATE)}
        submissions.append(sr); subs_by_claim[cid].append(sr)

# index lines by claim after secondary line creation
lines_by_claim=defaultdict(list)
for l in lines: lines_by_claim[l['Claim ID']].append(l)

# ---------- denial defect/evidence generation ----------
def pick_other_payer(exclude):
    cand=[x for x in payers if x!=exclude]
    return rng.choice(cand)

def ensure_auth(c):
    cid=c['Claim ID']
    if cid not in auth_map:
        aid=f'AUTHX-{cid}'
        c['Authorization Required']='Yes'; c['Authorization ID']=aid
        a={'Authorization ID':aid,'Claim ID':cid,'Payer Code':c['Payer Code'],'Payer Name':c['Payer Name'],'Authorization Required':'Yes','Authorization Obtained':'Yes','Authorization Number':'PA'+str(100000+rng.randrange(900000)),
           'Authorization Start Date':dstr(date.fromisoformat(c['Service Date'])-timedelta(days=15)),'Authorization End Date':dstr(date.fromisoformat(c['Service Date'])+timedelta(days=30)),'Authorized Provider Code':c['Provider Code'],'Authorized Location Code':c['Location Code'],'Authorized CPT':c['Primary CPT'],'Submitted CPT':c['Primary CPT'],
           'Authorization Match Status':'Match','Mismatch Type':'None','Authorization Status':'Valid','Retro Authorization Requested':'No','Retro Authorization Outcome':'N/A','Report Date':dstr(REPORT_DATE)}
        authorizations.append(a); auth_map[cid]=a
    return auth_map[cid]

def make_defect(c, scenario):
    cid=c['Claim ID']; primary=lines_by_claim[cid][0]; cov=cov_map[cid]; dos=date.fromisoformat(c['Service Date'])
    evidence_type=SCEN[scenario][7]; evidence_id=''; defect_field=''; submitted=''; expected=''; target=primary
    if scenario=='DEN01': cov['Coverage Effective Date']=dstr(dos+timedelta(days=10)); cov['Eligibility Check Result']='Inactive'; cov['Eligibility Defect Type']='Coverage Not Yet Effective'; evidence_id=cov['Coverage COB ID']; defect_field='Coverage Effective Date'; submitted=cov['Coverage Effective Date']; expected=f'<= {c["Service Date"]}'
    elif scenario=='DEN02': cov['Coverage Termination Date']=dstr(dos-timedelta(days=10)); cov['Eligibility Check Result']='Inactive'; cov['Eligibility Defect Type']='Coverage Terminated'; evidence_id=cov['Coverage COB ID']; defect_field='Coverage Termination Date'; submitted=cov['Coverage Termination Date']; expected=f'>= {c["Service Date"]}'
    elif scenario=='DEN03': cov['Member Information Match']='No'; cov['Eligibility Check Result']='Mismatch'; cov['Eligibility Defect Type']=rng.choice(['Member ID Mismatch','Demographic Mismatch']); evidence_id=cov['Coverage COB ID']; defect_field='Member Information Match'; submitted='No'; expected='Yes'
    elif scenario=='DEN04': cov['Payer Eligibility File Error']='Yes'; cov['Eligibility Check Result']='Payer Error'; cov['Eligibility Defect Type']='Payer Eligibility File Error'; evidence_id=cov['Coverage COB ID']; defect_field='Payer Eligibility File Error'; submitted='Yes'; expected='No payer error'
    elif scenario in ('DEN05','DEN06','DEN07','DEN08'):
        a=ensure_auth(c); evidence_id=a['Authorization ID']
        if scenario=='DEN05': a['Authorization Obtained']='No'; a['Authorization Number']=''; a['Authorization Match Status']='Missing'; a['Mismatch Type']='Missing Authorization'; a['Authorization Status']='Missing'; defect_field='Authorization Obtained'; submitted='No'; expected='Yes'
        elif scenario=='DEN06': a['Authorized CPT']=rng.choice([x for x in base_units if x!=c['Primary CPT']]); a['Authorization Match Status']='No Match'; a['Mismatch Type']='CPT'; a['Authorization Status']='Mismatched'; defect_field='Authorized CPT'; submitted=c['Primary CPT']; expected=a['Authorized CPT']
        elif scenario=='DEN07': a['Authorization Start Date']=dstr(dos+timedelta(days=5)); a['AuthorizationEndDate' if False else 'Authorization End Date']=dstr(dos+timedelta(days=30)); a['Authorization Match Status']='No Match'; a['Mismatch Type']='DOS'; a['Authorization Status']='Expired'; defect_field='Authorization Date Range'; submitted=c['Service Date']; expected=f'{a["Authorization Start Date"]} to {a["Authorization End Date"]}'
        else:
            if yes(.5): a['Authorized Provider Code']=rng.choice([x for x in providers if x!=c['Provider Code']]); a['Mismatch Type']='Provider'; defect_field='Authorized Provider Code'; submitted=c['Provider Code']; expected=a['Authorized Provider Code']
            else: a['Authorized Location Code']=rng.choice([x for x in locations if x!=c['Location Code']]); a['Mismatch Type']='Location'; defect_field='Authorized Location Code'; submitted=c['Location Code']; expected=a['Authorized Location Code']
            a['Authorization Match Status']='No Match'; a['Authorization Status']='Mismatched'
    elif scenario=='DEN09':
        primary['Submitted Modifier']='' if yes(.5) else ('QZ' if primary['Correct Modifier']=='AA' else 'AA'); primary['Coding Defect Type']='Missing Modifier' if not primary['Submitted Modifier'] else 'Wrong Modifier'; evidence_id=primary['Claim Line ID']; defect_field='Submitted Modifier'; submitted=primary['Submitted Modifier']; expected=primary['Correct Modifier']
    elif scenario=='DEN10':
        wrong={'Hospital - Inpatient':'Hospital - Outpatient','Hospital - Outpatient':'Surgery Center','Hospital - ER':'Hospital - Outpatient','Surgery Center':'Hospital - Outpatient','Surgery Center - Orthopedic':'Hospital - Outpatient'}[primary['Correct Setting']]
        primary['Submitted Setting']=wrong; primary['Coding Defect Type']='POS Mismatch'; evidence_id=primary['Claim Line ID']; defect_field='Submitted Setting'; submitted=wrong; expected=primary['Correct Setting']
    elif scenario=='DEN11': c['Primary Diagnosis Code']='Z00.00'; c['Diagnosis Category']='General exam / incompatible synthetic context'; evidence_id=cid; defect_field='Primary Diagnosis Code'; submitted='Z00.00'; expected='Procedure-compatible diagnosis'
    elif scenario=='DEN12': c['Primary Diagnosis Code']=''; c['Diagnosis Category']='Missing'; evidence_id=cid; defect_field='Primary Diagnosis Code'; submitted='blank'; expected='Valid ICD-10-CM code'
    elif scenario=='DEN13':
        primary['Submitted Base Units']=max(0,int(primary['Correct Base Units']) + rng.choice([-2,-1,1,2])); primary['Submitted Total Units']=round(float(primary['Submitted Base Units'])+float(primary['Submitted Time Units']),2); primary['Coding Defect Type']='Wrong Base Units'; evidence_id=primary['Claim Line ID']; defect_field='Submitted Base Units'; submitted=str(primary['Submitted Base Units']); expected=str(primary['Correct Base Units'])
    elif scenario=='DEN14': c['Referring Provider Required']='Yes'; c['Referring Provider ID']=''; c['Referring Provider ID Valid']='No'; evidence_id=cid; defect_field='Referring Provider ID'; submitted='blank'; expected='Valid referring provider ID'
    elif scenario=='DEN15': c['Documentation Required']='Yes'; c['Documentation Status']=rng.choice(['Missing','Not Submitted','Incomplete']); evidence_id=cid; defect_field='Documentation Status'; submitted=c['Documentation Status']; expected='Complete / Submitted'
    elif scenario=='DEN16': c['Medical Necessity Review Required']='Yes'; c['Primary Diagnosis Code']='Z00.00'; c['Diagnosis Category']='Fails modeled medical-necessity rule'; evidence_id=cid; defect_field='Medical Necessity Review'; submitted='Fails modeled rule'; expected='Pass modeled rule'
    elif scenario=='DEN17': c['Medical Necessity Review Required']='Yes'; c['Prior Similar Service Count']=rng.randint(4,7); evidence_id=cid; defect_field='Prior Similar Service Count'; submitted=str(c['Prior Similar Service Count']); expected='<= modeled threshold'
    elif scenario in ('DEN18','DEN19'):
        other=pick_other_payer(c['Payer Code']); evidence_id=cov['Coverage COB ID']
        if scenario=='DEN18': cov['Other Active Coverage']='Yes'; cov['Primary Payer Code']=other; cov['Primary Payer Name']=payers[other]['name']; cov['Expected Responsible Payer Code']=other; cov['Expected Responsible Payer Name']=payers[other]['name']; cov['Eligibility Defect Type']='Other Insurance Primary'; defect_field='Primary Payer Code'; submitted=c['Payer Code']; expected=other
        else: cov['Expected Responsible Payer Code']=other; cov['Expected Responsible Payer Name']=payers[other]['name']; cov['Eligibility Defect Type']='Wrong Payer'; defect_field='Expected Responsible Payer Code'; submitted=c['Payer Code']; expected=other
    elif scenario in ('DEN20','DEN21'):
        evidence_type='Claim_Submissions'; defect_field='Was Duplicate Submission'; expected='No'
        evidence_id='PENDING_SUBMISSION_EVIDENCE'
    elif scenario=='DEN22':
        # Actual filing violation. Eligibility is checked before this function is called,
        # so DOS never changes after reimbursement has been calculated.
        filing=int(c['Modeled Filing Limit Days'])
        max_late=(REPORT_DATE-dos).days-filing-10
        late_days=max(1,min(20,max_late))
        viol=dos+timedelta(days=filing+rng.randint(1,late_days))
        c['Submit Date']=dstr(viol)
        if subs_by_claim[cid]:
            subs_by_claim[cid][0]['Submission Date']=dstr(viol)
        defect_field='Submit Date vs Filing Limit'; submitted=c['Submit Date']; expected=f'<= DOS + {filing} days'; evidence_id=cid
    elif scenario in ('DEN23','DEN24'):
        sec=[x for x in lines_by_claim[cid] if x['Line Type']!='Primary Anesthesia']
        if not sec:
            # create a valid eligible secondary block line specifically to support bundling evidence
            scpt='64450'; j=len(lines_by_claim[cid])+1; slid=f'{cid}-{j:02d}'; sgross=SECONDARY_ALLOWED[scpt]; sallow=secondary_allowed(scpt,c['Payer Code'])
            target={'Claim Line ID':slid,'Claim ID':cid,'Line Number':j,'Service Date':c['Service Date'],'Provider Code':c['Provider Code'],'Provider Name':c['Provider Name'],'Location Code':c['Location Code'],'Location Name':c['Location Name'],'Payer Code':c['Payer Code'],'Payer Name':c['Payer Name'],'Payer Archetype':c['Payer Archetype'],'Procedure Group':c['Procedure Group'],'Line Type':'Regional Block / Injection','Submitted CPT':scpt,'Correct CPT':scpt,'Submitted Modifier':'XU','Correct Modifier':'XU','Submitted Setting':c['Setting'],'Correct Setting':c['Setting'],'Anesthesia Minutes':'','Submitted Base Units':'','Correct Base Units':'','Submitted Time Units':'','Correct Time Units':'','Submitted Total Units':1,'Correct Total Units':1,'Coding Defect Type':'None','Bundling Eligible':'Yes','Bundling Relationship ID':f'BND-{cid}','Gross Billed Amount':money(sgross),'Expected Allowed Amount':sallow,'Initial Paid Amount':sallow,'Initial Denied Amount':0,'Unique Line Revenue at Risk':0,'Final Paid Amount':sallow,'Final Line Status':'Paid'}
            lines.append(target); lines_by_claim[cid].append(target); line_map[slid]=target; c['Gross Billed Amount']=money(c['Gross Billed Amount']+sgross); c['Expected Allowed Amount']=money(c['Expected Allowed Amount']+sallow); c['Initial Paid Amount']=money(c['Initial Paid Amount']+sallow); c['Final Paid Amount']=money(c['Final Paid Amount']+sallow)
        else: target=rng.choice(sec)
        evidence_id=target['Claim Line ID']; defect_field='Bundling Eligibility / Payment Logic'; submitted='Bundled by payer'; expected='Correct bundle' if scenario=='DEN23' else 'Separately payable'
    elif scenario in ('DEN25','DEN26'): evidence_id=cid; defect_field='Benefit Coverage'; submitted=c['Primary CPT']; expected='Excluded under modeled benefit rule'
    return target,evidence_type,evidence_id,defect_field,submitted,expected

# Eligible adjudicated claims; denial incidence generated probabilistically, not forced to an exact count.
for c in claims:
    if c['Initial Claim Status']=='Pending': continue
    if not yes(.107): continue
    cid=c['Claim ID']
    # choose defect category, then instantiate evidence; denial scenario is consequence of defect template.
    cat=weighted_choice(list(CATEGORY_WEIGHTS),list(CATEGORY_WEIGHTS.values()))
    opts,w=SCEN_BY_CAT[cat]
    scen=weighted_choice(opts,w)
    # Timely-filing denials are eligible only when the filing-limit violation and adjudication
    # can both exist on/before the snapshot date. Otherwise use a different supported defect.
    if scen=='DEN22':
        dos0=date.fromisoformat(c['Service Date']); filing0=int(c['Modeled Filing Limit Days'])
        if dos0+timedelta(days=filing0+11)>REPORT_DATE:
            scen='DEN12'

    # Auth category only applies cleanly after ensure_auth; bundling will create eligible secondary if needed.
    target,evtype,evid,def_field,subval,expval=make_defect(c,scen)

    # Denial date is visible initial adjudication date; timely filing may have changed Submit Date, so recompute.
    submit=date.fromisoformat(c['Submit Date'])
    denial_date=max(submit+timedelta(days=rng.randint(10,25)), date.fromisoformat(c['Initial Adjudication Date']))
    if denial_date>REPORT_DATE:
        # snapshot says this claim would still be pending, so censor the denial entirely.
        c['Initial Claim Status']='Pending'; c['Initial Adjudication Date']=''; c['Initial Paid Amount']=0; c['InitialDeniedAmount' if False else 'Initial Denied Amount']=0; c['Final Paid Amount']=0; c['Final Balance']=c['Expected Allowed Amount'];
        for l in lines_by_claim[cid]: l['Initial Paid Amount']=0; l['Initial Denied Amount']=0; l['Final Paid Amount']=0; l['Final Line Status']='Pending'
        continue
    c['Initial Adjudication Date']=dstr(denial_date)

    # denied amount targets the affected line allowed amount; non-line events target primary line.
    denied=money(float(target['Expected Allowed Amount']))
    no_rev=scen in ('DEN20','DEN23')
    recoverable=0 if no_rev else denied
    unique=0 if no_rev else denied

    # Update claim/line initial state from paid to denied amount.
    target['InitialDeniedAmount' if False else 'Initial Denied Amount']=denied
    target['Initial Paid Amount']=money(max(0,float(target['Expected Allowed Amount'])-denied))
    target['Unique Line Revenue at Risk']=unique
    target['Final Line Status']='Denied / Open'
    c['Initial Claim Status']='Denied'; c['Initial Denied Amount']=money(c['Initial Denied Amount']+denied); c['Initial Paid Amount']=money(max(0,c['Expected Allowed Amount']-c['Initial Denied Amount']))
    c['Unique Revenue at Risk']=money(c['Unique Revenue at Risk']+unique); c['Has Denial']='Yes'
    c['Claim Preventable']='Yes' if SCEN[scen][6]=='Yes' else ('Context-dependent' if SCEN[scen][6]=='Context-dependent' else 'No')

    event_idx=len(denials)+1; evid_id=f'DENEV{event_idx:06d}'
    # Link original submission to initial denial.
    orig=subs_by_claim[cid][0]
    orig['Resulting Denial Event ID']=evid_id; orig['Submission Outcome']='Denied'
    if scen in ('DEN20','DEN21'):
        # Create a second submission prior to denial evidence. For true duplicate, mark duplicate; for payer error, legitimate corrected submission.
        sdate=max(date.fromisoformat(orig['Submission Date'])+timedelta(days=rng.randint(2,7)), denial_date-timedelta(days=rng.randint(1,3)))
        if sdate>=denial_date: sdate=denial_date-timedelta(days=1)
        sid=f'SUB-{cid}-02'
        sr={'Submission ID':sid,'Claim ID':cid,'Submission Number':2,'Submission Date':dstr(sdate),'Submission Type':'Resubmission' if scen=='DEN20' else 'Corrected','Submission Reason':'Duplicate retransmission' if scen=='DEN20' else 'Legitimate corrected submission','Trigger Denial Event ID':'','Resulting Denial Event ID':evid_id,'Submission Outcome':'Denied as duplicate','Payer Code':c['Payer Code'],'Payer Name':c['Payer Name'],'Claim Frequency Type':'1 - Original' if scen=='DEN20' else '7 - Replacement','Was Duplicate Submission':'Yes' if scen=='DEN20' else 'No','Duplicate Of Submission ID':orig['Submission ID'] if scen=='DEN20' else '','Corrected Fields':'' if scen=='DEN20' else 'Claim correction','Days Since Prior Submission':(sdate-date.fromisoformat(orig['Submission Date'])).days,'Report Date':dstr(REPORT_DATE)}
        submissions.append(sr); subs_by_claim[cid].append(sr); evid=sr['Submission ID']; subval=sr['Was Duplicate Submission']; expval='No' if scen=='DEN20' else 'Legitimate submission'

    p_rec,typ_days=REC[scen]
    follow=denial_date+timedelta(days=rng.randint(5,12))
    resolution_method=''
    appeal='No'; appeal_date=None; appeal_out='N/A'; res_date=None; recovered=0; status='Open / Unresolved'; res_sub=''
    # Snapshot-aware resolution attempt.
    if follow<=REPORT_DATE and yes(.78):
        if scen in ('DEN20','DEN23'):
            res_date=min(REPORT_DATE, denial_date+timedelta(days=max(1,int(typ_days+rng.randint(-3,3)))))
            if res_date>=denial_date:
                status='Closed - No Revenue Opportunity'; resolution_method='Contractual / Administrative Closure'
        else:
            candidate=denial_date+timedelta(days=max(3,int(typ_days+rng.randint(-8,8))))
            if candidate<=REPORT_DATE:
                res_date=candidate
                got=yes(p_rec)
                recovered=denied if got else 0
                status='Resolved - Recovered' if got else 'Resolved - Not Recovered'
                if scen in ('DEN16','DEN17','DEN25','DEN26','DEN22') and yes(.55):
                    appeal='Yes'; appeal_date=min(res_date, follow+timedelta(days=rng.randint(1,6))); appeal_out='Overturned' if got else 'Upheld'; resolution_method='Appeal'
                else:
                    resolution_method='Corrected Claim' if scen not in ('DEN04','DEN21','DEN24') else 'Payer Reprocessing'
                    if resolution_method=='Corrected Claim':
                        sdate=max(follow, denial_date+timedelta(days=1));
                        if sdate<=res_date:
                            sn=len(subs_by_claim[cid])+1; sid=f'SUB-{cid}-{sn:02d}'
                            sr={'Submission ID':sid,'Claim ID':cid,'Submission Number':sn,'Submission Date':dstr(sdate),'Submission Type':'Corrected','Submission Reason':f'Correction for {scen}','Trigger Denial Event ID':evid_id,'Resulting Denial Event ID':'','Submission Outcome':'Paid / Resolved' if got else 'Resolved without payment','Payer Code':c['Payer Code'],'Payer Name':c['Payer Name'],'Claim Frequency Type':'7 - Replacement','Was Duplicate Submission':'No','Duplicate Of Submission ID':'','Corrected Fields':def_field,'Days Since Prior Submission':(sdate-date.fromisoformat(subs_by_claim[cid][-1]['Submission Date'])).days,'Report Date':dstr(REPORT_DATE)}
                            submissions.append(sr); subs_by_claim[cid].append(sr); res_sub=sid
    if follow>REPORT_DATE: follow=None

    de={'Denial Event ID':evid_id,'Claim ID':cid,'Claim Line ID':target['Claim Line ID'],'Sequence':1,'Prior Denial Event ID':'','Trigger Submission ID':orig['Submission ID'],'Denial Date':dstr(denial_date),'Group Code':SCEN[scen][0],'CARC':SCEN[scen][1],'RARC':SCEN[scen][2],'Business Denial Category':SCEN[scen][3],'Scenario ID':scen,'Root Cause':SCEN[scen][4],'Root Cause Owner':SCEN[scen][5],'Preventable':SCEN[scen][6],'Evidence Type':evtype,'Evidence Record ID':evid,'Defect Field':def_field,'Submitted Value':subval,'Expected Value':expval,'Denied Amount':denied,'Revenue Opportunity':'None' if no_rev else ('High' if recoverable>=300 else 'Moderate'),'Recoverable Revenue at Risk':recoverable,'Unique Revenue at Risk Flag':'No' if no_rev else 'Yes','Resolution Method':resolution_method,'Follow-Up Date':dstr(follow),'Appeal Submitted':appeal,'Appeal Date':dstr(appeal_date),'Appeal Outcome':appeal_out,'Resolution Submission ID':res_sub,'Resolution Date':dstr(res_date),'Recovered Amount':money(recovered),'Final Denial Status':status,'Days to Resolution':(res_date-denial_date).days if res_date else ''}
    denials.append(de); denials_by_claim[cid].append(de)

    # Repeat denial: only after an actual corrective submission and only if chronology fits snapshot.
    if scen not in ('DEN20','DEN23') and yes(.124):
        # create correction/resubmission after event 1 if none exists yet
        trig_date=(res_date or follow or (denial_date+timedelta(days=7)))
        if trig_date and trig_date<REPORT_DATE-timedelta(days=7):
            sdate=trig_date+timedelta(days=1)
            sn=len(subs_by_claim[cid])+1; sid=f'SUB-{cid}-{sn:02d}'
            sr={'Submission ID':sid,'Claim ID':cid,'Submission Number':sn,'Submission Date':dstr(sdate),'Submission Type':'Corrected','Submission Reason':'Correction / resubmission after denial','Trigger Denial Event ID':evid_id,'Resulting Denial Event ID':'','Submission Outcome':'Re-adjudicated','Payer Code':c['Payer Code'],'Payer Name':c['Payer Name'],'Claim Frequency Type':'7 - Replacement','Was Duplicate Submission':'No','Duplicate Of Submission ID':'','Corrected Fields':def_field,'Days Since Prior Submission':(sdate-date.fromisoformat(subs_by_claim[cid][-1]['Submission Date'])).days,'Report Date':dstr(REPORT_DATE)}
            submissions.append(sr); subs_by_claim[cid].append(sr)
            d2date=sdate+timedelta(days=rng.randint(5,14))
            if d2date<=REPORT_DATE:
                # second defect can differ; avoid no-revenue scenarios to keep financial sequence simple
                cat2=weighted_choice(['Coding','Missing','Authorization','Eligibility','Payer'],[25,25,15,15,20]); opts2,w2=SCEN_BY_CAT[cat2]; scen2=weighted_choice(opts2,w2)
                target2,evtype2,evid2,df2,sv2,xv2=make_defect(c,scen2)
                den2=money(min(float(target2['Expected Allowed Amount']), max(0,c['Unique Revenue at Risk']-recovered)))
                # same dollars can be denied again; unique flag no.
                if den2<=0: den2=money(float(target2['Expected Allowed Amount']))
                ev2id=f'DENEV{len(denials)+1:06d}'; sr['Resulting Denial Event ID']=ev2id
                f2=d2date+timedelta(days=rng.randint(5,10)); f2=f2 if f2<=REPORT_DATE else None
                r2=None; rec2=0; st2='Open / Unresolved'; rm2=''; rs2=''
                p2,t2=REC[scen2]; cand=d2date+timedelta(days=max(3,int(t2+rng.randint(-6,6))))
                remaining=max(0,c['Unique Revenue at Risk']-recovered)
                if cand<=REPORT_DATE and yes(.70):
                    r2=cand; rec2=money(min(den2,remaining)) if yes(p2) else 0; st2='Resolved - Recovered' if rec2>0 else 'Resolved - Not Recovered'; rm2='Corrected Claim' if scen2 not in ('DEN04','DEN21','DEN24') else 'Payer Reprocessing'
                d2={'Denial Event ID':ev2id,'Claim ID':cid,'Claim Line ID':target2['Claim Line ID'],'Sequence':2,'Prior Denial Event ID':evid_id,'Trigger Submission ID':sid,'Denial Date':dstr(d2date),'Group Code':SCEN[scen2][0],'CARC':SCEN[scen2][1],'RARC':SCEN[scen2][2],'Business Denial Category':SCEN[scen2][3],'Scenario ID':scen2,'Root Cause':SCEN[scen2][4],'Root Cause Owner':SCEN[scen2][5],'Preventable':SCEN[scen2][6],'Evidence Type':evtype2,'Evidence Record ID':evid2,'Defect Field':df2,'Submitted Value':sv2,'Expected Value':xv2,'Denied Amount':den2,'Revenue Opportunity':'High' if den2>=300 else 'Moderate','Recoverable Revenue at Risk':den2,'Unique Revenue at Risk Flag':'No','Resolution Method':rm2,'Follow-Up Date':dstr(f2),'Appeal Submitted':'No','Appeal Date':'','Appeal Outcome':'N/A','Resolution Submission ID':rs2,'Resolution Date':dstr(r2),'Recovered Amount':rec2,'Final Denial Status':st2,'Days to Resolution':(r2-d2date).days if r2 else ''}
                denials.append(d2); denials_by_claim[cid].append(d2)
                if yes(.065) and r2 and r2<REPORT_DATE-timedelta(days=5):
                    s3date=r2+timedelta(days=1); sn3=len(subs_by_claim[cid])+1; sid3=f'SUB-{cid}-{sn3:02d}'
                    sr3={'Submission ID':sid3,'Claim ID':cid,'Submission Number':sn3,'Submission Date':dstr(s3date),'Submission Type':'Corrected','Submission Reason':'Second correction / resubmission','Trigger Denial Event ID':ev2id,'Resulting Denial Event ID':'','Submission Outcome':'Re-adjudicated','Payer Code':c['Payer Code'],'Payer Name':c['Payer Name'],'Claim Frequency Type':'7 - Replacement','Was Duplicate Submission':'No','Duplicate Of Submission ID':'','Corrected Fields':df2,'Days Since Prior Submission':(s3date-date.fromisoformat(subs_by_claim[cid][-1]['Submission Date'])).days,'Report Date':dstr(REPORT_DATE)}
                    submissions.append(sr3); subs_by_claim[cid].append(sr3)
                    d3date=s3date+timedelta(days=rng.randint(3,6))
                    if d3date<=REPORT_DATE:
                        ev3id=f'DENEV{len(denials)+1:06d}'; sr3['Resulting Denial Event ID']=ev3id
                        remaining3=max(0,c['Unique Revenue at Risk']-recovered-rec2); den3=money(min(den2,remaining3 if remaining3>0 else den2))
                        d3={'Denial Event ID':ev3id,'Claim ID':cid,'Claim Line ID':target2['Claim Line ID'],'Sequence':3,'Prior Denial Event ID':ev2id,'Trigger Submission ID':sid3,'Denial Date':dstr(d3date),'Group Code':SCEN[scen2][0],'CARC':SCEN[scen2][1],'RARC':SCEN[scen2][2],'Business Denial Category':SCEN[scen2][3],'Scenario ID':scen2,'Root Cause':SCEN[scen2][4],'Root Cause Owner':SCEN[scen2][5],'Preventable':SCEN[scen2][6],'Evidence Type':evtype2,'Evidence Record ID':evid2,'Defect Field':df2,'Submitted Value':sv2,'Expected Value':xv2,'Denied Amount':den3,'Revenue Opportunity':'Moderate','Recoverable Revenue at Risk':den3,'Unique Revenue at Risk Flag':'No','Resolution Method':'','Follow-Up Date':'','Appeal Submitted':'No','Appeal Date':'','Appeal Outcome':'N/A','Resolution Submission ID':'','Resolution Date':'','Recovered Amount':0,'Final Denial Status':'Open / Unresolved','Days to Resolution':''}
                        denials.append(d3); denials_by_claim[cid].append(d3)

# ---------- final financial reconciliation ----------
for c in claims:
    cid=c['Claim ID']; evs=denials_by_claim[cid]
    if c['Initial Claim Status']=='Pending':
        c['Final Claim Status']='Pending'; c['Final Paid Amount']=0; c['Final Balance']=c['Expected Allowed Amount']; c['Denial Event Count']=0; c['Has Denial']='No'; c['Initial Denied Amount']=0; c['Unique Revenue at Risk']=0
        continue
    if not evs:
        c['Final Claim Status']='Paid'; c['Final Paid Amount']=c['Expected Allowed Amount']; c['Final Balance']=0; continue
    c['Denial Event Count']=len(evs); c['Has Denial']='Yes'
    total_rec=money(sum(float(e['Recovered Amount']) for e in evs))
    # cap total recovery to unique risk
    if total_rec>c['Unique Revenue at Risk']:
        excess=total_rec-c['Unique Revenue at Risk']
        for e in reversed(evs):
            r=float(e['Recovered Amount']); cut=min(r,excess); e['Recovered Amount']=money(r-cut); excess-=cut
            if e['Recovered Amount']==0 and e['Final Denial Status']=='Resolved - Recovered': e['Final Denial Status']='Resolved - Not Recovered'
            if excess<=0: break
        total_rec=money(sum(float(e['Recovered Amount']) for e in evs))
    no_rev_all=all(e['Scenario ID'] in ('DEN20','DEN23') for e in evs)
    c['Final Paid Amount']=money(min(c['Expected Allowed Amount'],c['Initial Paid Amount']+total_rec))
    c['Final Balance']=0 if no_rev_all else money(max(0,c['Expected Allowed Amount']-c['Final Paid Amount']))
    if any(e['Final Denial Status']=='Open / Unresolved' for e in evs): c['Final Claim Status']='Denied / Open'
    elif c['Final Paid Amount']>=c['Expected Allowed Amount']-.01: c['Final Claim Status']='Paid / Recovered'
    elif no_rev_all: c['Final Claim Status']='Closed - No Revenue Opportunity'
    else: c['Final Claim Status']='Resolved - Partial/No Recovery'
    # line final paid/reconciliation based on its own events
    for l in lines_by_claim[cid]:
        lev=[e for e in evs if e['Claim Line ID']==l['Claim Line ID']]
        if not lev: l['Final Paid Amount']=l['Initial Paid Amount']; l['Final Line Status']='Paid'
        else:
            rec=money(sum(float(e['Recovered Amount']) for e in lev)); l['Final Paid Amount']=money(min(float(l['Expected Allowed Amount']),float(l['Initial Paid Amount'])+rec))
            l['Final Line Status']='Denied / Open' if any(e['Final Denial Status']=='Open / Unresolved' for e in lev) else ('Paid / Recovered' if l['Final Paid Amount']>=float(l['Expected Allowed Amount'])-.01 else 'Resolved - Unpaid')

# Fix Claim_Submissions evidence IDs for DEN20/DEN21 if placeholder survived (shouldn't).
for e in denials:
    if e['Evidence Record ID']=='PENDING_SUBMISSION_EVIDENCE':
        ss=subs_by_claim[e['Claim ID']]; e['Evidence Record ID']=ss[-1]['Submission ID']

# ---------- output schemas ----------
CLAIM_FIELDS=['Claim ID','Account','Service Date','Submit Date','Initial Adjudication Date','Provider Code','Provider Name','Provider Type','Modifier','Location Code','Location Name','Setting','County','Medicare Locality','Procedure Group','Primary CPT','Anesthesia Minutes','CMS Base Units','Internal Anesthesia Units','Payer Code','Payer Name','AR Type','Payer Archetype','Reimbursement Basis','Modeled Filing Limit Days','Gross Billed Amount','Expected Allowed Amount','Initial Claim Status','Initial Paid Amount','Initial Denied Amount','Unique Revenue at Risk','Final Paid Amount','Final Balance','Final Claim Status','Denial Event Count','Has Denial','Claim Preventable','Report Date','Primary Diagnosis Code','Diagnosis Category','Documentation Required','Documentation Status','Referring Provider Required','Referring Provider ID','Referring Provider ID Valid','Medical Necessity Review Required','Prior Similar Service Count','Authorization Required','Authorization ID']
LINE_FIELDS=['Claim Line ID','Claim ID','Line Number','Service Date','Provider Code','Provider Name','Location Code','Location Name','Payer Code','Payer Name','Payer Archetype','Procedure Group','Line Type','Submitted CPT','Correct CPT','Submitted Modifier','Correct Modifier','Submitted Setting','Correct Setting','Anesthesia Minutes','Submitted Base Units','Correct Base Units','Submitted Time Units','Correct Time Units','Submitted Total Units','Correct Total Units','Coding Defect Type','Bundling Eligible','Bundling Relationship ID','Gross Billed Amount','Expected Allowed Amount','Initial Paid Amount','Initial Denied Amount','Unique Line Revenue at Risk','Final Paid Amount','Final Line Status']
DENIAL_FIELDS=['Denial Event ID','Claim ID','Claim Line ID','Sequence','Prior Denial Event ID','Trigger Submission ID','Denial Date','Group Code','CARC','RARC','Business Denial Category','Scenario ID','Root Cause','Root Cause Owner','Preventable','Evidence Type','Evidence Record ID','Defect Field','Submitted Value','Expected Value','Denied Amount','Revenue Opportunity','Recoverable Revenue at Risk','Unique Revenue at Risk Flag','Resolution Method','Follow-Up Date','Appeal Submitted','Appeal Date','Appeal Outcome','Resolution Submission ID','Resolution Date','Recovered Amount','Final Denial Status','Days to Resolution']
SUB_FIELDS=['Submission ID','Claim ID','Submission Number','Submission Date','Submission Type','Submission Reason','Trigger Denial Event ID','Resulting Denial Event ID','Submission Outcome','Payer Code','Payer Name','Claim Frequency Type','Was Duplicate Submission','Duplicate Of Submission ID','Corrected Fields','Days Since Prior Submission','Report Date']
AUTH_FIELDS=['Authorization ID','Claim ID','Payer Code','Payer Name','Authorization Required','Authorization Obtained','Authorization Number','Authorization Start Date','Authorization End Date','Authorized Provider Code','Authorized Location Code','Authorized CPT','Submitted CPT','Authorization Match Status','Mismatch Type','Authorization Status','Retro Authorization Requested','Retro Authorization Outcome','Report Date']
COV_FIELDS=['Coverage COB ID','Claim ID','Service Date','Billed Payer Code','Billed Payer Name','Primary Payer Code','Primary Payer Name','Secondary Payer Code','Secondary Payer Name','Expected Responsible Payer Code','Expected Responsible Payer Name','Other Active Coverage','COB Sequence','Coverage Effective Date','Coverage Termination Date','Eligibility Check Date','Eligibility Check Result','Member Information Match','Eligibility Defect Type','Payer Eligibility File Error','Report Date']

write_csv(OUT/'Claims.csv',claims,CLAIM_FIELDS)
write_csv(OUT/'Claim_Lines.csv',lines,LINE_FIELDS)
write_csv(OUT/'Denial_Events.csv',denials,DENIAL_FIELDS)
write_csv(OUT/'Claim_Submissions.csv',submissions,SUB_FIELDS)
write_csv(OUT/'Authorizations.csv',authorizations,AUTH_FIELDS)
write_csv(OUT/'Coverage_COB.csv',coverages,COV_FIELDS)

# ---------- QA gate ----------
errors=[]; warnings=[]
claim_ids={c['Claim ID'] for c in claims}; line_ids={l['Claim Line ID'] for l in lines}; sub_ids={s['Submission ID'] for s in submissions}; auth_ids={a['Authorization ID'] for a in authorizations}; cov_ids={x['Coverage COB ID'] for x in coverages}

def fail(msg): errors.append(msg)
def warn(msg): warnings.append(msg)
if len(claim_ids)!=len(claims): fail('Duplicate Claim ID')
if len(line_ids)!=len(lines): fail('Duplicate Claim Line ID')
if len(sub_ids)!=len(submissions): fail('Duplicate Submission ID')
if len(auth_ids)!=len(authorizations): fail('Duplicate Authorization ID')
if len(cov_ids)!=len(coverages): fail('Duplicate Coverage COB ID')
for l in lines:
    if l['Claim ID'] not in claim_ids: fail('Orphan line '+l['Claim Line ID'])
for e in denials:
    if e['Claim ID'] not in claim_ids or e['Claim Line ID'] not in line_ids: fail('Orphan denial '+e['Denial Event ID'])
    if e['Trigger Submission ID'] not in sub_ids: fail('Bad trigger submission '+e['Denial Event ID'])
    if e['Resolution Submission ID'] and e['Resolution Submission ID'] not in sub_ids: fail('Bad resolution submission '+e['Denial Event ID'])
    dd=date.fromisoformat(e['Denial Date'])
    for fld in ('Follow-Up Date','Appeal Date','Resolution Date'):
        if e[fld] and date.fromisoformat(e[fld])>REPORT_DATE: fail('Future '+fld+' '+e['Denial Event ID'])
    if e['Resolution Date'] and date.fromisoformat(e['Resolution Date'])<dd: fail('Resolution before denial '+e['Denial Event ID'])
    if e['Appeal Date'] and date.fromisoformat(e['Appeal Date'])<dd: fail('Appeal before denial '+e['Denial Event ID'])
    if float(e['Recovered Amount'])>float(e['Denied Amount'])+.01: fail('Recovered > denied '+e['Denial Event ID'])
    if e['Final Denial Status']=='Open / Unresolved' and float(e['Recovered Amount'])!=0: fail('Open event has recovery '+e['Denial Event ID'])
    if e['Scenario ID'] in ('DEN20','DEN23') and float(e['Recovered Amount'])!=0: fail('No-opportunity scenario recovered '+e['Denial Event ID'])
for c in claims:
    if float(c['Expected Allowed Amount'])>float(c['Gross Billed Amount'])+.01: fail('Allowed > billed '+c['Claim ID'])
    if float(c['Initial Paid Amount'])+float(c['Initial Denied Amount'])>float(c['Expected Allowed Amount'])+.02: fail('Initial paid+denied > allowed '+c['Claim ID'])
    if float(c['Final Paid Amount'])>float(c['Expected Allowed Amount'])+.01: fail('Final paid > allowed '+c['Claim ID'])
    evs=denials_by_claim[c['Claim ID']]
    if sum(float(e['Recovered Amount']) for e in evs)>float(c['Unique Revenue at Risk'])+.02: fail('Recovery > unique risk '+c['Claim ID'])
    if c['Initial Claim Status']=='Pending':
        if c['Initial Adjudication Date'] or float(c['Initial Paid Amount']) or float(c['Initial Denied Amount']) or int(c['Denial Event Count']) or c['Has Denial']!='No': fail('Pending snapshot violation '+c['Claim ID'])
for s in submissions:
    if date.fromisoformat(s['Submission Date'])>REPORT_DATE: fail('Future submission '+s['Submission ID'])
for c in claims:
    ss=sorted(subs_by_claim[c['Claim ID']],key=lambda x:int(x['Submission Number']))
    ds=[date.fromisoformat(x['Submission Date']) for x in ss]
    if ds!=sorted(ds): fail('Submission chronology '+c['Claim ID'])
# sequence chronology/linkage
for cid,evs in denials_by_claim.items():
    evs=sorted(evs,key=lambda x:int(x['Sequence']))
    for j,e in enumerate(evs):
        if int(e['Sequence'])!=j+1: fail('Sequence numbering '+cid)
        if j>0:
            if e['Prior Denial Event ID']!=evs[j-1]['Denial Event ID']: fail('Prior denial link '+e['Denial Event ID'])
            ts=next((s for s in submissions if s['Submission ID']==e['Trigger Submission ID']),None)
            if not ts or date.fromisoformat(ts['Submission Date'])>=date.fromisoformat(e['Denial Date']): fail('Trigger submission chronology '+e['Denial Event ID'])
# modifier and reimbursement-specific checks
for l in lines:
    if l['Line Type']=='Primary Anesthesia':
        pt=claim_map[l['Claim ID']]['Provider Type']; expected='AA' if pt=='Anesthesiologist' else 'QZ'
        if l['Correct Modifier']!=expected: fail('Bad correct primary modifier '+l['Claim Line ID'])
    elif l['Correct CPT']=='76942' and l['Correct Modifier']!='26': fail('Bad 76942 modifier '+l['Claim Line ID'])
    elif l['Correct CPT'] in ('64415','64447','64450','64483') and l['Correct Modifier']!='XU': fail('Bad injection modifier '+l['Claim Line ID'])
# evidence checks
for e in denials:
    if e['Evidence Type']=='Coverage_COB' and e['Evidence Record ID'] not in cov_ids: fail('Missing coverage evidence '+e['Denial Event ID'])
    if e['Evidence Type']=='Authorizations' and e['Evidence Record ID'] not in auth_ids: fail('Missing auth evidence '+e['Denial Event ID'])
    if e['Evidence Type']=='Claim_Submissions' and e['Evidence Record ID'] not in sub_ids: fail('Missing submission evidence '+e['Denial Event ID'])
    if e['Evidence Type']=='Claim_Lines' and e['Evidence Record ID'] not in line_ids: fail('Missing line evidence '+e['Denial Event ID'])
# unique risk repeat rule: only first event may flag yes for same claim in this generator
for cid,evs in denials_by_claim.items():
    yesflags=sum(1 for e in evs if e['Unique Revenue at Risk Flag']=='Yes')
    if yesflags>1: fail('Repeat denials inflate unique risk '+cid)

adjudicated=sum(1 for c in claims if c['Initial Claim Status']!='Pending')
denied_claims=sum(1 for c in claims if c['Has Denial']=='Yes')
denial_rate=denied_claims/adjudicated if adjudicated else 0
if not (.09<=denial_rate<=.12): warn(f'Initial denial rate outside diagnostic guardrail: {denial_rate:.3%}')
seq_counts=Counter(int(e['Sequence']) for e in denials)
scenario_counts=Counter(e['Scenario ID'] for e in denials)
month_counts=Counter(date.fromisoformat(c['Service Date']).month for c in claims)

report=[]
report.append('PROJECT 2 CONTROLLED REGENERATION QA REPORT')
report.append(f'Seed: {SEED}')
report.append(f'Report date: {REPORT_DATE}')
report.append('')
report.append(f'Claims: {len(claims)}')
report.append(f'Claim lines: {len(lines)}')
report.append(f'Denial events: {len(denials)}')
report.append(f'Claim submissions: {len(submissions)}')
report.append(f'Authorizations: {len(authorizations)}')
report.append(f'Coverage/COB records: {len(coverages)}')
report.append(f'Pending claims: {sum(1 for c in claims if c["Initial Claim Status"]=="Pending")}')
report.append(f'Initial denied claims: {denied_claims}')
report.append(f'Adjudicated claims: {adjudicated}')
report.append(f'Initial denial rate: {denial_rate:.2%}')
report.append(f'Denial sequence counts: {dict(sorted(seq_counts.items()))}')
report.append(f'December service volume: {month_counts[12]} | monthly mean: {statistics.mean(month_counts.values()):.1f}')
report.append('')
report.append('Hard QA failures: '+str(len(errors)))
for x in errors[:100]: report.append('FAIL: '+x)
report.append('Warnings: '+str(len(warnings)))
for x in warnings: report.append('WARN: '+x)
report.append('')
report.append('Scenario counts:')
for k in sorted(scenario_counts): report.append(f'  {k}: {scenario_counts[k]}')
report.append('')
report.append('RELEASE STATUS: '+('PASS' if not errors else 'FAIL'))
(OUT/'Project_2_QA_Report.txt').write_text('\n'.join(report),encoding='utf-8')
print('\n'.join(report[:25]))
if errors:
    raise SystemExit(2)
