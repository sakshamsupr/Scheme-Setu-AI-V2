import { BookOpenCheck, CheckCircle2, ExternalLink, ShieldCheck, Sparkles } from 'lucide-react';
import { useProfile } from '../context/ProfileContext';
import { useLanguage } from '../context/LanguageContext';
import { caseForScheme } from '../data/caseStudies';
import { useState } from 'react';
import { api } from '../services/api';

export default function WhyThisScheme({scheme,full=false}){
 const {profile}=useProfile(); const {t}=useLanguage(); const [gap,setGap]=useState(null); const [loading,setLoading]=useState(false);
 const caseStudy=caseForScheme(scheme.scheme_name); const reasons=(scheme.match_reasons||[]).slice(0,4); const gaps=(scheme.gaps||[]).slice(0,3);
 const detect=async()=>{setLoading(true);try{const r=await api.eligibilityGap({profile,limit:50}); const found=(r.items||[]).find(x=>x.scheme_id===scheme.scheme_id); setGap(found||null);}catch(e){setGap({error:e.message})}finally{setLoading(false)}};
 return <section className={`why-scheme ${full?'full':''}`}><div className="why-head"><div><span className="section-kicker">{t('why')}</span><h3><Sparkles size={16}/> {t('whyFull')}</h3></div><button className="btn btn-light small-btn" onClick={detect}>{t('gap')}</button></div>
 <div className="why-reasons">{reasons.length?reasons.map(r=><span key={r}><CheckCircle2 size={14}/>{r}</span>):gaps.length?gaps.map(g=><span className="gap-pill" key={g}>{g}</span>):<span>{t('whyProfilePending')}</span>}</div>
 {caseStudy&&<div className="case-study"><div className="case-icon"><BookOpenCheck size={18}/></div><div><strong>{t('caseStudy')}: {caseStudy.title}</strong><p>{caseStudy.summary}</p><a href={caseStudy.source} target="_blank" rel="noreferrer">{caseStudy.sourceLabel} <ExternalLink size={12}/></a></div></div>}
 {!caseStudy&&<div className="evidence-note"><ShieldCheck size={16}/><div><strong>{t('officialEvidence')}</strong><span>{t('relatedEvidence')}</span><a className="text-link" href={scheme.apply_link} target="_blank" rel="noreferrer">{t('verifySource')} <ExternalLink size={12}/></a></div></div>}
 {gap&&<div className="gap-result"><strong>{gap.error?gap.error:(gap.eligible? t('noHardGap'):t('gapsFound'))}</strong>{gap.gaps?.length?<ul>{gap.gaps.map(g=><li key={g}>{g}</li>)}</ul>:!gap.error&&<p>{t('noGap')}</p>}</div>}
 {loading&&<div className="tiny-loading">{t('checking')}</div>}
 </section>
}
