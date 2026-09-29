import { useMemo, useState } from 'react';
import { Bell, CalendarClock, CheckCheck, ExternalLink, RefreshCw, X } from 'lucide-react';
import { useNotifications } from '../context/NotificationContext';
import { useLanguage } from '../context/LanguageContext';
import { useNavigate } from 'react-router-dom';

export default function NotificationCenter(){
 const {items,unread,addReminder,markRead,markAll,refresh}=useNotifications(); const {t}=useLanguage(); const nav=useNavigate();
 const [open,setOpen]=useState(false); const [showAdd,setShowAdd]=useState(false); const [title,setTitle]=useState(''); const [date,setDate]=useState('');
 const groups=useMemo(()=>({scheme:items.filter(x=>x.type==='scheme'),application:items.filter(x=>x.type==='application'),deadline:items.filter(x=>x.type==='deadline'),reminder:items.filter(x=>x.type==='reminder')}),[items]);
 const add=()=>{if(!title||!date)return; addReminder({title,message:`Reminder: ${title}`,dueAt:date}); setTitle('');setDate('');setShowAdd(false)};
 const go=(item)=>{markRead(item.id); if(item.target) nav(item.target); else if(item.source) window.open(item.source,'_blank','noopener,noreferrer')};
 return <div className="notification-wrap">
  <button className={`top-icon ${unread?'has-unread':''}`} onClick={()=>setOpen(v=>!v)} aria-label={t('notifications')}><Bell size={19}/>{unread>0&&<span className="notif-count">{unread>9?'9+':unread}</span>}</button>
  {open&&<div className="notification-popover">
   <div className="notification-head"><div><strong>{t('notifications')}</strong><span>{unread} unread</span></div><button className="icon-btn light-icon" onClick={()=>setOpen(false)}><X size={16}/></button></div>
   <div className="notification-actions"><button onClick={markAll}><CheckCheck size={14}/>Mark all</button><button onClick={()=>refresh()}><RefreshCw size={14}/>{t('refresh')}</button><button onClick={()=>setShowAdd(v=>!v)}><CalendarClock size={14}/>{t('setReminder')}</button></div>
   {showAdd&&<div className="reminder-form"><input placeholder={t('reminderTitle')} value={title} onChange={e=>setTitle(e.target.value)}/><input type="datetime-local" value={date} onChange={e=>setDate(e.target.value)}/><button className="btn btn-primary" onClick={add}>{t('addReminder')}</button></div>}
   <div className="notification-list">
    {items.slice(0,10).map(n=><button key={n.id} className={`notification-item ${n.read?'read':''}`} onClick={()=>go(n)}><span className={`notif-dot ${n.type}`}></span><div><strong>{n.title}</strong><p>{n.message}</p>{n.dueAt&&<small>Due {new Date(n.dueAt).toLocaleString()}</small>}</div>{(n.target||n.source)&&<ExternalLink size={14}/>}</button>)}
    {!items.length&&<div className="empty-state">{t('noNotifications')}</div>}
   </div>
   <div className="notification-foot">Government updates are source-linked; live sync requires the corresponding official feed/API.</div>
  </div>}
 </div>
}
