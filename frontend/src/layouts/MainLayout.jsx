import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { Home as HomeIcon, LayoutDashboard, Search, Scale, Calculator as CalculatorIcon, MapPinned, FileText, UserRound, Menu, X, Sparkles, Route, Languages } from 'lucide-react';
import { useState } from 'react';
import FloatingAI from '../components/FloatingAI';
import NotificationCenter from '../components/NotificationCenter';
import BrandLogo from '../components/BrandLogo';
import { useLanguage } from '../context/LanguageContext';

const items=[
 ['/', 'home', HomeIcon], ['/dashboard','dashboard',LayoutDashboard], ['/schemes','schemes',Search], ['/compare','compare',Scale], ['/calculator','calculator',CalculatorIcon], ['/partners','partners',MapPinned], ['/documents','documents',FileText], ['/roadmap','roadmap',Route], ['/profile','profile',UserRound]
];
export default function MainLayout(){
 const [open,setOpen]=useState(false); const location=useLocation(); const navigate=useNavigate(); const {t,language,changeLanguage,options}=useLanguage();
 return <div className="app-shell">
  <button className="mobile-menu" onClick={()=>setOpen(true)} aria-label="Open menu"><Menu size={22}/></button>
  {open&&<button className="mobile-backdrop" onClick={()=>setOpen(false)} aria-label="Close menu"/>}
  <aside className={`sidebar ${open?'open':''}`}>
   <div className="brand-row"><BrandLogo compact/><div><div className="brand-name">Scheme Setu <em>AI</em></div><div className="brand-sub">Bharat-first finance bridge</div></div><button className="mobile-close" onClick={()=>setOpen(false)}><X size={18}/></button></div>
   <div className="trust-pill"><Sparkles size={15}/> {t('ai')}</div>
   <nav className="nav-stack">{items.map(([path,label,Icon])=><NavLink onClick={()=>setOpen(false)} className={({isActive})=>`nav-item ${isActive&&(path==='/'?location.pathname==='/':true)?'active':''}`} to={path} key={path}><Icon size={18}/><span>{t(label)}</span></NavLink>)}</nav>
   <div className="sidebar-footer"><button className="side-cta" onClick={()=>navigate('/schemes')}><span>{t('explore')}</span><span>→</span></button><p>Seed/demo dataset now; verified government data can replace it without changing the product shell.</p></div>
  </aside>
  <div className="topbar"><div className="topbar-spacer"/><div className="topbar-actions"><div className="language-switch"><Languages size={15}/><select value={language} onChange={e=>changeLanguage(e.target.value)} aria-label={t('language')}>{options.map(o=><option key={o.code} value={o.code}>{o.label}</option>)}</select></div><NotificationCenter/></div></div>
  <main className="main-pane"><Outlet/></main><FloatingAI/>
  <div className="mobile-bottom-nav">{items.slice(0,5).map(([path,label,Icon])=><NavLink key={path} to={path} className={({isActive})=>`mobile-nav-item ${isActive?'active':''}`}><Icon size={18}/><span>{t(label).split(' ')[0]}</span></NavLink>)}</div>
 </div>
}
