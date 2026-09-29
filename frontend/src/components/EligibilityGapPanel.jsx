import { AlertCircle, CheckCircle2, Lightbulb } from 'lucide-react';
import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { useProfile } from '../context/ProfileContext';
import { useLanguage } from '../context/LanguageContext';

export default function EligibilityGapPanel({schemeId}){
 const {profile}=useProfile(); const {t}=useLanguage(); const [row,setRow]=useState(null); const [busy,setBusy]=useState(false);
 useEffect(()=>{let active=true; setBusy(true); api.eligibilityGap({profile,limit:50}).then(r=>{if(active)setRow((r.items||[]).find(x=>x.scheme_id===schemeId)||null)}).catch(()=>{}).finally(()=>active&&setBusy(false)); return()=>{active=false}},[JSON.stringify(profile),schemeId]);
 if(busy) return <div className="panel gap-panel"><span className="section-kicker">{t('gap')}</span><p>Checking eligibility signals…</p></div>;
 if(!row) return <div className="panel gap-panel"><span className="section-kicker">{t('gap')}</span><p>{t('setProfile')}</p></div>;
 return <div className="panel gap-panel"><div className="panel-title"><div><span className="section-kicker">{t('gap')}</span><h2>{row.eligible? 'You pass the current hard checks.':'Before you apply, fix these gaps.'}</h2></div>{row.eligible?<CheckCircle2 size={24}/>:<AlertCircle size={24}/>}</div><p>{t('gapIntro')}</p><div className="gap-list">{(row.gaps||[]).map(g=><div key={g}><AlertCircle size={15}/><span>{g}</span></div>)}</div>{!(row.gaps||[]).length&&<div className="gap-ok"><CheckCircle2 size={16}/>{t('noGap')}</div>}<div className="gap-suggestions"><Lightbulb size={16}/><span>Tip: a gap is a planning signal, not a final sanction decision. Verify the latest official eligibility before applying.</span></div></div>
}
